import datetime
import ipaddress
import os
import queue
import select
import socket
import struct
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import filedialog, scrolledtext, ttk

import certifi
from cryptography.hazmat.primitives.ciphers.aead import AESSIV
from OpenSSL import SSL

APP_NAME = "NTP/NTS Diagnostic Tool"
APP_VERSION = "2.1.0"
NTP_EPOCH = 2208988800
NTS_KE_PORT = 4460
DEFAULT_NTP_PORT = 123
AEAD_AES_SIV_CMAC_256 = 15
AEAD_KEY_LEN = 32
NTS_ALPN = b"ntske/1"

EF_UID = 0x0104
EF_COOKIE = 0x0204
EF_COOKIE_PLACEHOLDER = 0x0304
EF_AUTH = 0x0404

KE_END = 0
KE_NEXT_PROTOCOL = 1
KE_ERROR = 2
KE_WARNING = 3
KE_AEAD = 4
KE_COOKIE = 5
KE_SERVER = 6
KE_PORT = 7


class ProtocolError(Exception):
    pass


@dataclass
class NTSSession:
    ke_host: str
    ntp_host: str
    ntp_port: int
    aead_id: int
    c2s_key: bytes
    s2c_key: bytes
    cookies: list[bytes] = field(default_factory=list)
    tls_version: str = ""
    cipher: str = ""


def pad4(data: bytes) -> bytes:
    return data + (b"\x00" * ((-len(data)) % 4))


def make_ke_record(record_type: int, body: bytes = b"", critical: bool = False) -> bytes:
    if not (0 <= record_type <= 0x7FFF):
        raise ValueError("invalid NTS-KE record type")
    wire_type = record_type | (0x8000 if critical else 0)
    return struct.pack("!HH", wire_type, len(body)) + body


def parse_ke_records(data: bytes):
    records = []
    pos = 0
    saw_end = False
    while pos + 4 <= len(data):
        wire_type, body_len = struct.unpack("!HH", data[pos:pos + 4])
        pos += 4
        if pos + body_len > len(data):
            raise ProtocolError("truncated NTS-KE record")
        critical = bool(wire_type & 0x8000)
        record_type = wire_type & 0x7FFF
        body = data[pos:pos + body_len]
        pos += body_len
        records.append((record_type, critical, body))
        if record_type == KE_END:
            if body_len != 0 or not critical:
                raise ProtocolError("invalid End-of-Message record")
            if pos != len(data):
                raise ProtocolError("data follows NTS-KE End-of-Message")
            saw_end = True
            break
    if not saw_end:
        raise ProtocolError("NTS-KE response has no End-of-Message record")
    return records


def ke_message_complete(data: bytes) -> bool:
    pos = 0
    while pos + 4 <= len(data):
        wire_type, body_len = struct.unpack("!HH", data[pos:pos + 4])
        pos += 4
        if pos + body_len > len(data):
            return False
        record_type = wire_type & 0x7FFF
        pos += body_len
        if record_type == KE_END:
            return True
    return False


def ntp_timestamp(unix_time: float) -> bytes:
    ntp = unix_time + NTP_EPOCH
    sec = int(ntp) & 0xFFFFFFFF
    frac = int((ntp - int(ntp)) * (1 << 32)) & 0xFFFFFFFF
    return struct.pack("!II", sec, frac)


def ntp_timestamp_to_unix(raw: bytes) -> float:
    sec, frac = struct.unpack("!II", raw)
    return (sec - NTP_EPOCH) + frac / float(1 << 32)


def make_extension(field_type: int, body: bytes) -> bytes:
    total_len = 4 + len(body)
    if total_len % 4:
        raise ProtocolError(f"extension 0x{field_type:04x} body is not 32-bit aligned")
    if total_len > 0xFFFF:
        raise ProtocolError("NTP extension field too large")
    return struct.pack("!HH", field_type, total_len) + body


def parse_extensions(data: bytes, start: int = 48):
    fields = []
    pos = start
    while pos < len(data):
        if len(data) - pos < 4:
            raise ProtocolError("trailing bytes after NTP extension fields")
        field_type, field_len = struct.unpack("!HH", data[pos:pos + 4])
        if field_len < 4 or field_len % 4 or pos + field_len > len(data):
            raise ProtocolError(f"invalid NTP extension field length {field_len}")
        fields.append((field_type, data[pos + 4:pos + field_len], pos, pos + field_len))
        pos += field_len
    return fields


def is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host.rstrip("."))
        return True
    except ValueError:
        return False


def create_openssl_context(skip_verify: bool) -> SSL.Context:
    ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
    ctx.set_min_proto_version(SSL.TLS1_3_VERSION)
    ctx.set_alpn_protos([NTS_ALPN])
    if skip_verify:
        ctx.set_verify(SSL.VERIFY_NONE, lambda *_: True)
    else:
        ctx.load_verify_locations(certifi.where())
        ctx.set_verify(SSL.VERIFY_PEER, lambda conn, cert, errno, depth, ok: ok)
    return ctx



def _ssl_wait(sock, want_write: bool, deadline: float):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("TLS operation timed out")
    rlist = [] if want_write else [sock]
    wlist = [sock] if want_write else []
    readable, writable, _ = select.select(rlist, wlist, [], remaining)
    if not readable and not writable:
        raise TimeoutError("TLS operation timed out")


def _ssl_handshake(conn, sock, timeout: float):
    deadline = time.monotonic() + timeout
    while True:
        try:
            conn.do_handshake()
            return
        except SSL.WantReadError:
            _ssl_wait(sock, False, deadline)
        except SSL.WantWriteError:
            _ssl_wait(sock, True, deadline)


def _ssl_sendall(conn, sock, data: bytes, timeout: float):
    deadline = time.monotonic() + timeout
    view = memoryview(data)
    sent = 0
    while sent < len(view):
        try:
            n = conn.send(view[sent:])
            if n <= 0:
                raise ProtocolError("TLS connection closed while sending NTS-KE request")
            sent += n
        except SSL.WantReadError:
            _ssl_wait(sock, False, deadline)
        except SSL.WantWriteError:
            _ssl_wait(sock, True, deadline)


def _ssl_recv(conn, sock, size: int, deadline: float) -> bytes:
    while True:
        try:
            return conn.recv(size)
        except SSL.WantReadError:
            _ssl_wait(sock, False, deadline)
        except SSL.WantWriteError:
            _ssl_wait(sock, True, deadline)

def perform_nts_ke(host: str, skip_verify: bool, timeout: float = 5.0) -> NTSSession:
    request = b"".join([
        make_ke_record(KE_NEXT_PROTOCOL, struct.pack("!H", 0), critical=True),
        make_ke_record(KE_AEAD, struct.pack("!H", AEAD_AES_SIV_CMAC_256)),
        make_ke_record(KE_END, b"", critical=True),
    ])

    raw_sock = socket.create_connection((host, NTS_KE_PORT), timeout=timeout)
    raw_sock.settimeout(timeout)
    conn = None
    try:
        ctx = create_openssl_context(skip_verify)
        conn = SSL.Connection(ctx, raw_sock)
        conn.set_connect_state()
        if not is_ip_literal(host):
            conn.set_tlsext_host_name(host.rstrip(".").encode("idna"))
        _ssl_handshake(conn, raw_sock, timeout)

        alpn = conn.get_alpn_proto_negotiated()
        if alpn != NTS_ALPN:
            got = alpn.decode("ascii", "replace") if alpn else "none"
            raise ProtocolError(f"server did not negotiate required ALPN ntske/1 (got {got})")

        if not skip_verify:
            cert = conn.get_peer_certificate()
            if cert is None:
                raise ProtocolError("server supplied no TLS certificate")
            # OpenSSL chain validation is enabled above. Verify service identity explicitly.
            from cryptography import x509
            from cryptography.x509 import DNSName, IPAddress
            from cryptography.x509.verification import PolicyBuilder, Store
            # pyOpenSSL has already validated the chain. Use stdlib hostname matcher-compatible
            # certificate decoding through cryptography for a direct SAN/CN check below.
            cert_crypto = cert.to_cryptography()
            try:
                san = cert_crypto.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
                if is_ip_literal(host):
                    expected = ipaddress.ip_address(host.rstrip("."))
                    if expected not in san.get_values_for_type(x509.IPAddress):
                        raise ProtocolError(f"certificate is not valid for IP address {host}")
                else:
                    names = san.get_values_for_type(x509.DNSName)
                    import ssl as _ssl
                    cert_dict = {"subjectAltName": [("DNS", n) for n in names]}
                    _ssl.match_hostname(cert_dict, host.rstrip("."))
            except x509.ExtensionNotFound:
                # Modern public NTS certificates should carry SAN. Refuse ambiguous identity.
                raise ProtocolError("TLS certificate has no Subject Alternative Name")

        _ssl_sendall(conn, raw_sock, request, timeout)
        response = bytearray()
        recv_deadline = time.monotonic() + timeout
        while len(response) < 65536:
            chunk = _ssl_recv(conn, raw_sock, 4096, recv_deadline)
            if not chunk:
                break
            response.extend(chunk)
            if ke_message_complete(response):
                break
        if not ke_message_complete(response):
            raise ProtocolError("incomplete NTS-KE response")

        records = parse_ke_records(bytes(response))
        next_protocols = []
        selected_aead = None
        cookies = []
        ntp_host = host
        ntp_port = DEFAULT_NTP_PORT

        for rtype, critical, body in records:
            if rtype == KE_NEXT_PROTOCOL:
                if len(body) % 2:
                    raise ProtocolError("malformed Next Protocol record")
                next_protocols.extend(struct.unpack(f"!{len(body)//2}H", body) if body else ())
            elif rtype == KE_ERROR:
                code = struct.unpack("!H", body)[0] if len(body) == 2 else -1
                raise ProtocolError(f"NTS-KE server returned error {code}")
            elif rtype == KE_WARNING:
                code = struct.unpack("!H", body)[0] if len(body) == 2 else -1
                raise ProtocolError(f"NTS-KE server returned warning {code}")
            elif rtype == KE_AEAD:
                if len(body) != 2:
                    raise ProtocolError("server selected zero or multiple AEAD algorithms")
                selected_aead = struct.unpack("!H", body)[0]
            elif rtype == KE_COOKIE:
                if not body:
                    raise ProtocolError("server returned an empty NTS cookie")
                cookies.append(body)
            elif rtype == KE_SERVER:
                try:
                    ntp_host = body.decode("ascii").rstrip(".")
                except UnicodeDecodeError as exc:
                    raise ProtocolError("non-ASCII NTP server negotiation record") from exc
            elif rtype == KE_PORT:
                if len(body) != 2:
                    raise ProtocolError("malformed NTP port negotiation record")
                ntp_port = struct.unpack("!H", body)[0]
            elif rtype == KE_END:
                pass
            elif critical:
                raise ProtocolError(f"unknown critical NTS-KE record type {rtype}")

        if 0 not in next_protocols:
            raise ProtocolError("server did not negotiate NTPv4 as the next protocol")
        if selected_aead != AEAD_AES_SIV_CMAC_256:
            raise ProtocolError(f"unsupported AEAD selected by server: {selected_aead}")
        if not cookies:
            raise ProtocolError("NTS-KE server returned no cookies")

        label = b"EXPORTER-network-time-security"
        c2s_context = struct.pack("!HHB", 0, selected_aead, 0)
        s2c_context = struct.pack("!HHB", 0, selected_aead, 1)
        c2s_key = conn.export_keying_material(label, AEAD_KEY_LEN, c2s_context)
        s2c_key = conn.export_keying_material(label, AEAD_KEY_LEN, s2c_context)

        cipher_name = conn.get_cipher_name() or ""
        tls_version = conn.get_protocol_version_name() or ""
        return NTSSession(host, ntp_host, ntp_port, selected_aead, c2s_key, s2c_key,
                          cookies, tls_version, cipher_name)
    finally:
        if conn is not None:
            try:
                conn.shutdown()
            except Exception:
                pass
        try:
            raw_sock.close()
        except Exception:
            pass


def build_plain_ntp_request(t1: float):
    header = bytearray(48)
    header[0] = 0x23  # LI=0, VN=4, Mode=3 (client)
    tx = ntp_timestamp(t1)
    header[40:48] = tx
    return bytes(header), tx


def build_nts_request(session: NTSSession, t1: float):
    if not session.cookies:
        raise ProtocolError("no unused NTS cookies remain; repeat NTS-KE")
    cookie = session.cookies.pop(0)
    if len(cookie) % 4:
        raise ProtocolError("server supplied an NTS cookie that is not 32-bit aligned")

    header, tx = build_plain_ntp_request(t1)
    uid = os.urandom(32)
    uid_ef = make_extension(EF_UID, uid)
    cookie_ef = make_extension(EF_COOKIE, cookie)

    # Ask for enough replacement cookies to refill toward RFC 8915's recommended pool of 8.
    wanted = max(0, min(7, 8 - len(session.cookies) - 1))
    placeholders = b"".join(make_extension(EF_COOKIE_PLACEHOLDER, b"\x00" * len(cookie))
                            for _ in range(wanted))
    associated = header + uid_ef + cookie_ef + placeholders

    nonce = os.urandom(16)
    # RFC 5297 nonce-based SIV: nonce is the final AD component before plaintext.
    ciphertext = AESSIV(session.c2s_key).encrypt(b"", [associated, nonce])
    auth_body = struct.pack("!HH", len(nonce), len(ciphertext)) + pad4(nonce) + pad4(ciphertext)
    auth_ef = make_extension(EF_AUTH, auth_body)
    return associated + auth_ef, tx, uid


def decode_authenticator(body: bytes):
    if len(body) < 4:
        raise ProtocolError("truncated NTS authenticator")
    nonce_len, cipher_len = struct.unpack("!HH", body[:4])
    nonce_pad = (nonce_len + 3) & ~3
    cipher_pad = (cipher_len + 3) & ~3
    if 4 + nonce_pad + cipher_pad > len(body):
        raise ProtocolError("invalid NTS authenticator lengths")
    nonce = body[4:4 + nonce_len]
    cipher_start = 4 + nonce_pad
    ciphertext = body[cipher_start:cipher_start + cipher_len]
    return nonce, ciphertext


def validate_ntp_response(data: bytes, tx_raw: bytes, t1: float, t4: float):
    if len(data) < 48:
        raise ProtocolError(f"short NTP response ({len(data)} bytes)")
    li_vn_mode = data[0]
    li = (li_vn_mode >> 6) & 0x3
    vn = (li_vn_mode >> 3) & 0x7
    mode = li_vn_mode & 0x7
    stratum = data[1]
    if mode != 4:
        raise ProtocolError(f"unexpected NTP mode {mode}; expected server mode 4")
    if vn not in (3, 4):
        raise ProtocolError(f"unexpected NTP version {vn}")
    if data[24:32] != tx_raw:
        raise ProtocolError("originate timestamp does not match this request")

    result = {"li": li, "vn": vn, "mode": mode, "stratum": stratum}
    if stratum == 0:
        result["kod"] = data[12:16].decode("ascii", errors="replace")
        return result

    t2 = ntp_timestamp_to_unix(data[32:40])
    t3 = ntp_timestamp_to_unix(data[40:48])
    if data[32:40] == b"\x00" * 8 or data[40:48] == b"\x00" * 8:
        raise ProtocolError("server returned a zero receive/transmit timestamp")
    result.update({
        "t2": t2,
        "t3": t3,
        "offset_ms": (((t2 - t1) + (t3 - t4)) / 2.0) * 1000.0,
        "delay_ms": ((t4 - t1) - (t3 - t2)) * 1000.0,
    })
    return result


def validate_nts_response(data: bytes, session: NTSSession, tx_raw: bytes, uid: bytes,
                          t1: float, t4: float):
    result = validate_ntp_response(data, tx_raw, t1, t4)
    if result["stratum"] == 0:
        # NTSN is intentionally unauthenticated in some failure cases; report it distinctly.
        return result

    fields = parse_extensions(data)
    uid_seen = None
    auth = None
    auth_start = None
    for ftype, body, start, end in fields:
        if ftype == EF_UID and uid_seen is None:
            uid_seen = body
        elif ftype == EF_AUTH:
            if auth is not None:
                raise ProtocolError("multiple NTS authenticator fields in response")
            auth = body
            auth_start = start

    if uid_seen != uid:
        raise ProtocolError("NTS Unique Identifier mismatch")
    if auth is None:
        raise ProtocolError("NTS-protected request received an unauthenticated response")

    nonce, ciphertext = decode_authenticator(auth)
    associated = data[:auth_start]
    try:
        plaintext = AESSIV(session.s2c_key).decrypt(ciphertext, [associated, nonce])
    except Exception as exc:
        raise ProtocolError("NTS response authentication failed") from exc

    new_cookies = []
    if plaintext:
        for ftype, body, _start, _end in parse_extensions(b"\x00" * 48 + plaintext):
            if ftype == EF_COOKIE:
                new_cookies.append(body)
    session.cookies.extend(new_cookies)
    result["nts_authenticated"] = True
    result["new_cookies"] = len(new_cookies)
    return result


class NTPApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("980x720")
        self.root.minsize(850, 620)
        self.root.configure(padx=10, pady=10)
        try:
            ttk.Style().theme_use("vista")
        except tk.TclError:
            pass

        self.stop_event = threading.Event()
        self.log_file_path = None
        self.ui_queue = queue.Queue()
        self.root.after(50, self.process_ui_queue)

        self.target_var = tk.StringVar(value="time.cloudflare.com")
        self.count_var = tk.IntVar(value=5)
        self.delay_var = tk.IntVar(value=1000)
        self.nts_var = tk.BooleanVar(value=True)
        self.insecure_tls_var = tk.BooleanVar(value=False)
        self.log_to_file_var = tk.BooleanVar(value=False)
        self.sent_var = tk.IntVar(value=0)
        self.recv_var = tk.IntVar(value=0)
        self.fail_var = tk.IntVar(value=0)
        self.nts_fail_var = tk.IntVar(value=0)
        self.kod_var = tk.IntVar(value=0)

        # NTP peer-test responder state. Kept separate from the client worker so
        # client diagnostics and the local test responder can be controlled independently.
        self.peer_stop_event = threading.Event()
        self.peer_thread = None
        self.peer_socket = None
        self.peer_mode_var = tk.StringVar(value="valid")
        self.peer_bind_var = tk.StringVar(value="0.0.0.0")
        self.peer_port_var = tk.IntVar(value=123)
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        ctrl = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        ctrl.pack(fill="x", pady=(0, 10))
        ttk.Label(ctrl, text="Server (IP/FQDN):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(ctrl, textvariable=self.target_var, width=34).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(ctrl, text="Number of Requests:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Spinbox(ctrl, from_=1, to=10000, textvariable=self.count_var, width=10).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(ctrl, text="Delay (ms):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Spinbox(ctrl, from_=0, to=60000, textvariable=self.delay_var, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(ctrl, text="Enable NTS (TCP 4460)", variable=self.nts_var).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(ctrl, text="Skip TLS certificate verification", variable=self.insecure_tls_var).grid(row=1, column=3, sticky="w", padx=5, pady=5)

        lf = ttk.Frame(ctrl)
        lf.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(lf, text="Log to File", variable=self.log_to_file_var, command=self.toggle_file_picker).pack(side="left", padx=(0, 10))
        self.btn_file = ttk.Button(lf, text="Select Log File...", state="disabled", command=self.select_file)
        self.btn_file.pack(side="left")
        self.lbl_file = ttk.Label(lf, text="No file selected")
        self.lbl_file.pack(side="left", padx=10)

        bf = ttk.Frame(ctrl)
        bf.grid(row=3, column=0, columnspan=4, pady=10)
        self.btn_start = ttk.Button(bf, text="Start Requests", command=self.start_requests)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(bf, text="Stop", command=self.stop_requests, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        peer = ttk.LabelFrame(self.root, text="NTP Peer Test Responder", padding=10)
        peer.pack(fill="x", pady=(0, 10))
        ttk.Label(peer, text="Bind:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(peer, textvariable=self.peer_bind_var, width=16).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(peer, text="UDP Port:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Spinbox(peer, from_=1, to=65535, textvariable=self.peer_port_var, width=7).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(peer, text="Response Mode:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.peer_mode = ttk.Combobox(
            peer, textvariable=self.peer_mode_var, state="readonly", width=15,
            values=("valid", "kod", "bad-originate", "short", "duplicate")
        )
        self.peer_mode.grid(row=0, column=5, padx=5, pady=5)
        self.btn_peer_start = ttk.Button(peer, text="Start Responder", command=self.start_peer_responder)
        self.btn_peer_start.grid(row=0, column=6, padx=5, pady=5)
        self.btn_peer_stop = ttk.Button(peer, text="Stop Responder", command=self.stop_peer_responder, state="disabled")
        self.btn_peer_stop.grid(row=0, column=7, padx=5, pady=5)
        ttk.Label(
            peer,
            text="Modes: valid | RATE KoD | bad originate timestamp | 16-byte short reply | duplicate transmit timestamp",
        ).grid(row=1, column=0, columnspan=8, sticky="w", padx=5, pady=(2, 0))

        sf = ttk.LabelFrame(self.root, text="Real-Time Statistics", padding=10)
        sf.pack(fill="x", pady=(0, 10))
        for i, (label, var) in enumerate([
            ("Sent:", self.sent_var), ("Received:", self.recv_var), ("Failures:", self.fail_var),
            ("NTS Failures:", self.nts_fail_var), ("KoD Packets:", self.kod_var)
        ]):
            ttk.Label(sf, text=label).grid(row=0, column=i * 2, padx=5, sticky="e")
            ttk.Label(sf, textvariable=var, font=("Segoe UI", 10, "bold")).grid(row=0, column=i * 2 + 1, padx=(0, 15), sticky="w")

        out = ttk.LabelFrame(self.root, text="Running Log", padding=10)
        out.pack(fill="both", expand=True)
        self.log_text = scrolledtext.ScrolledText(out, wrap=tk.WORD, font=("Consolas", 9), state="disabled", bg="#1e1e1e", fg="#cccccc")
        self.log_text.pack(fill="both", expand=True)

    def start_peer_responder(self):
        if self.peer_thread and self.peer_thread.is_alive():
            return
        bind_host = self.peer_bind_var.get().strip() or "0.0.0.0"
        try:
            port = int(self.peer_port_var.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except (tk.TclError, ValueError):
            self.log_message("PEER TEST ERROR: UDP port must be between 1 and 65535.")
            return
        mode = self.peer_mode_var.get().strip().lower()
        if mode not in {"valid", "kod", "bad-originate", "short", "duplicate"}:
            self.log_message("PEER TEST ERROR: Unknown response mode.")
            return

        self.peer_stop_event.clear()
        self.btn_peer_start.config(state="disabled")
        self.btn_peer_stop.config(state="normal")
        self.peer_mode.config(state="disabled")
        self.peer_thread = threading.Thread(
            target=self.run_peer_responder, args=(bind_host, port, mode), daemon=True
        )
        self.peer_thread.start()

    def stop_peer_responder(self):
        self.peer_stop_event.set()
        sock = self.peer_socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        self.log_message("NTP peer test responder stop requested.")

    @staticmethod
    def _now_ntp_parts():
        t = time.time() + NTP_EPOCH
        sec = int(t) & 0xFFFFFFFF
        frac = int((t - int(t)) * 4294967296) & 0xFFFFFFFF
        return sec, frac

    @staticmethod
    def _put_ntp_parts(packet, offset, sec, frac):
        struct.pack_into("!II", packet, offset, sec, frac)

    def run_peer_responder(self, bind_host, port, mode):
        duplicate_t3 = None
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.5)
            sock.bind((bind_host, port))
            self.peer_socket = sock
            self.log_message(
                f"NTP peer test responder listening on {bind_host}:{port}/UDP | mode={mode}"
            )
            if port == 123:
                self.log_message(
                    "PEER TEST: UDP/123 may require elevated privileges and must not already be in use."
                )

            while not self.peer_stop_event.is_set():
                try:
                    request, addr = sock.recvfrom(2048)
                except socket.timeout:
                    continue
                except OSError:
                    if self.peer_stop_event.is_set():
                        break
                    raise

                if len(request) < 48:
                    self.log_message(
                        f"PEER TEST {addr[0]}:{addr[1]}: ignored short request ({len(request)} bytes)"
                    )
                    continue

                originate = request[40:48]
                self.log_message(
                    f"PEER TEST {addr[0]}:{addr[1]}: request {len(request)} bytes | mode={mode}"
                )

                if mode == "short":
                    reply = b"\\x24\\x01\\x00\\x00" + b"\\x00" * 12
                    sock.sendto(reply, addr)
                    self.log_message("PEER TEST -> sent 16-byte malformed response")
                    continue

                response = bytearray(48)
                response[0] = 0x24  # LI=0, VN=4, Mode=4 (server)
                response[1] = 1
                response[2] = 6
                response[3] = 0xEC
                struct.pack_into("!I", response, 4, 0)
                struct.pack_into("!I", response, 8, 1)

                if mode == "kod":
                    response[1] = 0
                    response[12:16] = b"RATE"
                else:
                    response[12:16] = b"TEST"

                ref_sec, ref_frac = self._now_ntp_parts()
                self._put_ntp_parts(response, 16, (ref_sec - 1) & 0xFFFFFFFF, ref_frac)

                if mode == "bad-originate":
                    response[24:32] = b"\\x12\\x34\\x56\\x78\\x9a\\xbc\\xde\\xf0"
                else:
                    response[24:32] = originate

                recv_sec, recv_frac = self._now_ntp_parts()
                self._put_ntp_parts(response, 32, recv_sec, recv_frac)

                if mode == "duplicate":
                    if duplicate_t3 is None:
                        duplicate_t3 = self._now_ntp_parts()
                    tx_sec, tx_frac = duplicate_t3
                else:
                    tx_sec, tx_frac = self._now_ntp_parts()
                self._put_ntp_parts(response, 40, tx_sec, tx_frac)

                sock.sendto(response, addr)
                refid = response[12:16].decode("ascii", errors="replace")
                self.log_message(
                    f"PEER TEST -> sent response | stratum={response[1]} | refid={refid}"
                )
        except PermissionError as exc:
            self.log_message(
                f"PEER TEST ERROR: cannot bind {bind_host}:{port}/UDP: {exc}. "
                "On Windows, try running as Administrator or choose an unprivileged test port."
            )
        except OSError as exc:
            if not self.peer_stop_event.is_set():
                self.log_message(f"PEER TEST ERROR: {exc}")
        except Exception as exc:
            self.log_message(f"PEER TEST ERROR [{type(exc).__name__}]: {exc}")
        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
            self.peer_socket = None
            self.ui_queue.put(("peer_done", None))
            self.log_message("NTP peer test responder stopped.")

    def on_close(self):
        self.stop_event.set()
        self.peer_stop_event.set()
        if self.peer_socket is not None:
            try:
                self.peer_socket.close()
            except OSError:
                pass
        self.root.destroy()

    def process_ui_queue(self):
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "stat":
                    var, value = payload
                    var.set(value)
                elif kind == "done":
                    self._reset_buttons()
                elif kind == "peer_done":
                    self.btn_peer_start.config(state="normal")
                    self.btn_peer_stop.config(state="disabled")
                    self.peer_mode.config(state="readonly")
        except queue.Empty:
            pass
        self.root.after(50, self.process_ui_queue)

    def toggle_file_picker(self):
        self.btn_file.config(state="normal" if self.log_to_file_var.get() else "disabled")

    def select_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("Log Files", "*.log")])
        if path:
            self.log_file_path = path
            self.lbl_file.config(text=path)

    def log_message(self, msg):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        full = f"[{timestamp}] {msg}\n"
        self.ui_queue.put(("log", full))
        if self.log_to_file_var.get() and self.log_file_path:
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(full)
            except Exception as exc:
                self.ui_queue.put(("log", f"[ERROR] Failed to write log file: {exc}\n"))

    def _append_log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def set_stat(self, var, value):
        self.ui_queue.put(("stat", (var, value)))

    def start_requests(self):
        if self.log_to_file_var.get() and not self.log_file_path:
            self.log_message("ERROR: Log to file is checked but no file is selected.")
            return
        target = self.target_var.get().strip()
        if not target:
            self.log_message("ERROR: Server is empty.")
            return
        try:
            count = int(self.count_var.get())
            delay = int(self.delay_var.get())
        except (tk.TclError, ValueError):
            self.log_message("ERROR: Count and delay must be valid integers.")
            return

        for var in (self.sent_var, self.recv_var, self.fail_var, self.nts_fail_var, self.kod_var):
            var.set(0)
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.stop_event.clear()
        config = (target, count, delay, bool(self.nts_var.get()), bool(self.insecure_tls_var.get()))
        threading.Thread(target=self.run_worker, args=config, daemon=True).start()

    def stop_requests(self):
        self.stop_event.set()
        self.btn_stop.config(state="disabled")
        self.log_message("Stop requested; waiting for the active network operation to finish...")

    def run_worker(self, target, count, delay_ms, use_nts, skip_verify):
        sent = received = failures = nts_failures = kods = 0
        session = None
        try:
            self.log_message(f"Starting {APP_NAME} {APP_VERSION} against {target} | Count={count} | Delay={delay_ms} ms | NTS={use_nts}")
            if use_nts:
                self.log_message(f"NTS-KE: connecting to {target}:{NTS_KE_PORT}; TLS certificate verification={'OFF' if skip_verify else 'ON'}")
                try:
                    session = perform_nts_ke(target, skip_verify)
                    self.log_message(f"NTS-KE SUCCESS: {session.tls_version}, {session.cipher}, ALPN=ntske/1, AEAD=15")
                    self.log_message(f"NTS-KE: received {len(session.cookies)} cookie(s); NTP endpoint={session.ntp_host}:{session.ntp_port}")
                    self.log_message("NTS-KE: C2S/S2C keys derived with TLS exporter (key bytes are intentionally not logged).")
                except Exception as exc:
                    nts_failures += 1
                    self.set_stat(self.nts_fail_var, nts_failures)
                    detail = str(exc).strip() or repr(exc)
                    self.log_message(f"NTS-KE FAILED [{type(exc).__name__}]: {detail}")
                    return

            for i in range(1, count + 1):
                if self.stop_event.is_set():
                    self.log_message("Execution aborted by user.")
                    break
                self.log_message(f"--- Request {i}/{count} ---")

                if use_nts and session is not None and not session.cookies:
                    self.log_message("NTS cookie pool exhausted; performing a fresh NTS-KE exchange.")
                    try:
                        session = perform_nts_ke(target, skip_verify)
                    except Exception as exc:
                        nts_failures += 1
                        self.set_stat(self.nts_fail_var, nts_failures)
                        self.log_message(f"NTS-KE refresh FAILED: {exc}")
                        break

                t1 = time.time()
                if use_nts:
                    packet, tx_raw, uid = build_nts_request(session, t1)
                    host, port = session.ntp_host, session.ntp_port
                    self.log_message(f"NTS request: {len(packet)} bytes, UID=32 bytes, authenticated with AEAD_AES_SIV_CMAC_256")
                else:
                    packet, tx_raw = build_plain_ntp_request(t1)
                    uid = None
                    host, port = target, DEFAULT_NTP_PORT

                sent += 1
                self.set_stat(self.sent_var, sent)
                self.log_message(f"Sending UDP request to {host}:{port}")

                try:
                    infos = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)
                    if not infos:
                        raise OSError("name resolution returned no addresses")
                    family, socktype, proto, _canon, sockaddr = infos[0]
                    with socket.socket(family, socktype, proto) as udp:
                        udp.settimeout(3.0)
                        udp.sendto(packet, sockaddr)
                        data, addr = udp.recvfrom(65535)
                    t4 = time.time()
                    received += 1
                    self.set_stat(self.recv_var, received)
                    self.log_message(f"Received {len(data)} bytes from {addr[0]}:{addr[1]}")

                    if use_nts:
                        result = validate_nts_response(data, session, tx_raw, uid, t1, t4)
                    else:
                        result = validate_ntp_response(data, tx_raw, t1, t4)

                    self.log_message(f"NTP: LI={result['li']} VN={result['vn']} Mode={result['mode']} Stratum={result['stratum']}")
                    if result["stratum"] == 0:
                        kods += 1
                        self.set_stat(self.kod_var, kods)
                        self.log_message(f"WARNING: Kiss-o'-Death packet: {result.get('kod', '????')}")
                        if use_nts and result.get("kod") == "NTSN":
                            nts_failures += 1
                            self.set_stat(self.nts_fail_var, nts_failures)
                    else:
                        self.log_message(f"Timing: offset={result['offset_ms']:+.3f} ms | network delay={result['delay_ms']:.3f} ms")
                        if use_nts:
                            self.log_message(f"NTS AUTHENTICATED: UID matched, S2C tag verified, new cookies={result['new_cookies']}, pool={len(session.cookies)}")
                except socket.timeout:
                    failures += 1
                    self.set_stat(self.fail_var, failures)
                    self.log_message("ERROR: UDP request timed out.")
                except Exception as exc:
                    failures += 1
                    self.set_stat(self.fail_var, failures)
                    if use_nts and isinstance(exc, ProtocolError):
                        nts_failures += 1
                        self.set_stat(self.nts_fail_var, nts_failures)
                    self.log_message(f"ERROR: {exc}")

                if i < count and not self.stop_event.is_set() and delay_ms > 0:
                    if self.stop_event.wait(delay_ms / 1000.0):
                        self.log_message("Execution aborted by user.")
                        break
        finally:
            self.log_message("Execution complete.")
            self.ui_queue.put(("done", None))

    def _reset_buttons(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    NTPApp(root)
    root.mainloop()
