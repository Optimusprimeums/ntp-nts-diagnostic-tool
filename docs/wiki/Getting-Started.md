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
