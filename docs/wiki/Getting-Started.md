# Getting Started

## Download

Download `NTP-NTS-Diagnostic-Tool.exe` from the project's **v2.0.2 GitHub Release**. The packaged Windows executable is standalone; Python is not required.

The v2.0.2 release executable has SHA-256:

```text
9c6f5a236f431ac7d1bbd8e6799e629df348452bf8e058a7e3fe75fa1047fa7b
```

## First NTS test

1. Start the application.
2. Enter a certificate-valid NTS hostname in **Server (IP/FQDN)**. For a public interoperability test, use `time.cloudflare.com`.
3. Set **Number of Requests** to `5`.
4. Set **Delay (ms)** to `1000`.
5. Check **Enable NTS (TCP 4460)**.
6. Leave **Skip TLS certificate verification** unchecked.
7. Click **Start Requests**.
8. Watch the Running Log for **NTS-KE SUCCESS** followed by **NTS AUTHENTICATED**.

For plain NTP, clear **Enable NTS** before starting.

## What success looks like

A successful NTS session first establishes TLS 1.3/NTS-KE, obtains cookies and derives C2S/S2C keys. Successful UDP responses then include output such as:

```text
NTS AUTHENTICATED: UID matched, S2C tag verified, new cookies=1, pool=8
```

That line confirms that the response UID matched and the server-to-client authentication tag verified.

Next: [Interface Guide](Interface-Guide.md).
