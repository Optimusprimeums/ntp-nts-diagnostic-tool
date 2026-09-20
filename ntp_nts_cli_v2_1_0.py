#!/usr/bin/env python3
"""Headless Linux CLI for NTP/NTS Diagnostic Tool v2.1.0.

This entry point deliberately has no tkinter dependency.  It imports the
protocol implementation from the versioned application source while keeping
GUI construction out of the headless execution path.
"""
import argparse
import socket
import struct
import sys
import time
import importlib.util
from pathlib import Path

APP_VERSION = "2.1.0"

def load_engine():
    here = Path(__file__).resolve().parent
    candidates = sorted(here.glob("ntp_nts_tester_v*.py"))
    if not candidates:
        # PyInstaller places bundled modules beside/inside the executable.
        import ntp_nts_tester_v2_1_0 as engine
        return engine
    path = candidates[-1]
    spec = importlib.util.spec_from_file_location("ntp_engine", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def query(engine, host, use_nts, skip_verify, count, delay_ms):
    session = None
    if use_nts:
        print(f"NTS-KE: {host}:4460 TLS verification={'OFF' if skip_verify else 'ON'}")
        session = engine.perform_nts_ke(host, skip_verify)
        print(f"NTS-KE SUCCESS: {session.tls_version}, {session.cipher}, ALPN=ntske/1")
    failures = 0
    for i in range(1, count + 1):
        try:
            if use_nts and not session.cookies:
                session = engine.perform_nts_ke(host, skip_verify)
            t1 = time.time()
            if use_nts:
                packet, tx_raw, uid = engine.build_nts_request(session, t1)
                target, port = session.ntp_host, session.ntp_port
            else:
                packet, tx_raw = engine.build_plain_ntp_request(t1)
                uid = None
                target, port = host, engine.DEFAULT_NTP_PORT
            infos = socket.getaddrinfo(target, port, type=socket.SOCK_DGRAM)
            family, socktype, proto, _, sockaddr = infos[0]
            with socket.socket(family, socktype, proto) as udp:
                udp.settimeout(3.0)
                udp.sendto(packet, sockaddr)
                data, addr = udp.recvfrom(65535)
            t4 = time.time()
            result = (engine.validate_nts_response(data, session, tx_raw, uid, t1, t4)
                      if use_nts else engine.validate_ntp_response(data, tx_raw, t1, t4))
            if result["stratum"] == 0:
                print(f"[{i}/{count}] {addr[0]} KoD={result.get('kod', '????')}")
            else:
                auth = " NTS=authenticated" if use_nts else ""
                print(f"[{i}/{count}] {addr[0]} stratum={result['stratum']} "
                      f"offset={result['offset_ms']:+.3f} ms delay={result['delay_ms']:.3f} ms{auth}")
        except Exception as exc:
            failures += 1
            print(f"[{i}/{count}] ERROR [{type(exc).__name__}]: {exc}", file=sys.stderr)
        if i < count and delay_ms:
            time.sleep(delay_ms / 1000.0)
    return 1 if failures else 0

def make_reply(engine, request, mode, duplicate_t3, replay_packet):
    if mode == "drop":
        return None, duplicate_t3, replay_packet
    if mode == "short":
        return b"\x24\x01\x00\x00" + b"\x00" * 12, duplicate_t3, replay_packet
    if mode == "replay" and replay_packet is not None:
        return replay_packet, duplicate_t3, replay_packet
    response = bytearray(48)
    response[0] = {"wrong-mode":0x23, "bad-version":0x04, "li-alarm":0xE4}.get(mode, 0x24)
    response[1], response[2], response[3] = 1, 6, 0xEC
    struct.pack_into("!I", response, 8, 1)
    if mode in {"kod","kod-deny","kod-rstr"}:
        response[1] = 0
        response[12:16] = {"kod":b"RATE","kod-deny":b"DENY","kod-rstr":b"RSTR"}[mode]
    else:
        response[12:16] = b"TEST"
    if mode == "stratum-16":
        response[1] = 16
    now = time.time()
    response[16:24] = engine.ntp_timestamp(now - 1)
    response[24:32] = (b"\x12\x34\x56\x78\x9a\xbc\xde\xf0"
                       if mode == "bad-originate" else request[40:48])
    t2 = now
    delta = 0.1 if mode == "offset-plus-100ms" else -0.1 if mode == "offset-minus-100ms" else 0
    if mode != "zero-t2":
        response[32:40] = engine.ntp_timestamp(t2 + delta)
    if mode == "processing-100ms":
        time.sleep(0.1)
    if mode == "duplicate":
        duplicate_t3 = duplicate_t3 or engine.ntp_timestamp(time.time())
        t3raw = duplicate_t3
    else:
        t3raw = engine.ntp_timestamp(time.time() + delta)
    if mode != "zero-t3":
        response[40:48] = t3raw
    result = bytes(response)
    if mode == "replay" and replay_packet is None:
        replay_packet = result
    if mode == "delayed":
        time.sleep(1.0)
    return result, duplicate_t3, replay_packet

def peer(engine, bind, port, mode):
    duplicate_t3 = replay_packet = None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind, port))
        print(f"Peer responder listening on {bind}:{port}/UDP mode={mode}", flush=True)
        try:
            while True:
                request, addr = sock.recvfrom(2048)
                if len(request) < 48:
                    print(f"{addr[0]}:{addr[1]} ignored short request ({len(request)} bytes)")
                    continue
                reply, duplicate_t3, replay_packet = make_reply(engine, request, mode, duplicate_t3, replay_packet)
                if reply is not None:
                    sock.sendto(reply, addr)
                    print(f"{addr[0]}:{addr[1]} -> {len(reply)} bytes")
                else:
                    print(f"{addr[0]}:{addr[1]} -> dropped")
        except KeyboardInterrupt:
            print("\nPeer responder stopped.")
    return 0

def self_test(engine):
    # Headless smoke test for the wire generator; the GUI suite remains the
    # exhaustive 19-mode loopback test until the shared responder is factored out.
    request = bytearray(48); request[0] = 0x23; request[40:48] = engine.ntp_timestamp(time.time())
    modes = ["valid","kod","kod-deny","kod-rstr","bad-originate","short","wrong-mode",
             "bad-version","zero-t2","zero-t3","li-alarm","stratum-16",
             "offset-plus-100ms","offset-minus-100ms"]
    failed = 0
    for mode in modes:
        try:
            reply, _, _ = make_reply(engine, bytes(request), mode, None, None)
            ok = reply is not None and (len(reply) == 16 if mode == "short" else len(reply) == 48)
        except Exception:
            ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] {mode}")
        failed += not ok
    print(f"{len(modes)-failed} passed / {failed} failed")
    return 1 if failed else 0

def main():
    p = argparse.ArgumentParser(prog="NTP-NTS-Diagnostic-Tool-CLI")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("query", help="run NTP/NTS diagnostic requests")
    q.add_argument("server"); q.add_argument("-n","--count",type=int,default=5)
    q.add_argument("--delay",type=int,default=1000,metavar="MS")
    q.add_argument("--nts",action="store_true"); q.add_argument("--skip-tls-verify",action="store_true")
    r = sub.add_parser("peer", help="run headless NTP peer responder")
    r.add_argument("--bind",default="0.0.0.0"); r.add_argument("--port",type=int,default=123)
    r.add_argument("--mode",default="valid", choices=["valid","kod","kod-deny","kod-rstr","bad-originate",
        "short","duplicate","wrong-mode","bad-version","zero-t2","zero-t3","li-alarm","stratum-16",
        "drop","delayed","offset-plus-100ms","offset-minus-100ms","processing-100ms","replay"])
    sub.add_parser("self-test", help="run headless responder smoke tests")
    args = p.parse_args()
    engine = load_engine()
    if args.command == "query":
        return query(engine,args.server,args.nts,args.skip_tls_verify,args.count,args.delay)
    if args.command == "peer":
        return peer(engine,args.bind,args.port,args.mode)
    return self_test(engine)

if __name__ == "__main__":
    raise SystemExit(main())
