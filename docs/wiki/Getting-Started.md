# Getting Started

Download `NTP-NTS-Diagnostic-Tool.exe` from the project's v2.0.2 GitHub Release. The Windows executable is standalone; Python is not required.

## First NTS test

1. Start the application.
2. Enter a certificate-valid NTS hostname such as `time.cloudflare.com`.
3. Set **Number of Requests** to `5` and **Delay (ms)** to `1000`.
4. Check **Enable NTS (TCP 4460)**.
5. Leave **Skip TLS certificate verification** unchecked.
6. Click **Start Requests**.
7. Look for **NTS-KE SUCCESS** followed by **NTS AUTHENTICATED**.

For plain NTP, clear **Enable NTS** before starting.

A successful authenticated response includes:

```text
NTS AUTHENTICATED: UID matched, S2C tag verified, new cookies=1, pool=8
```

Next: [Interface Guide](Interface-Guide.md).

## v2.1.0 development builds

The Windows v2.1.0 GUI adds the peer responder, fault injection, responder self-test, startup permission assistance, and **Copy Log** / **Clear Log** controls.

The Linux v2.1.0 distribution is headless and can be used from a terminal or SSH session:

```bash
./NTP-NTS-Diagnostic-Tool query time.cloudflare.com --nts -n 5
./NTP-NTS-Diagnostic-Tool peer --bind 0.0.0.0 --port 123 --mode valid
./NTP-NTS-Diagnostic-Tool self-test
```

No X11/Wayland desktop is required for the Linux CLI. Binding UDP/123 may require elevated privileges or `CAP_NET_BIND_SERVICE` depending on the host's privileged-port policy.

