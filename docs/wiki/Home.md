# NTP/NTS Diagnostic Tool Wiki

Welcome to the user documentation for **NTP/NTS Diagnostic Tool v2.0.2**, a Windows diagnostic client for NTPv4 and RFC 8915 Network Time Security.

![Annotated NTP/NTS Diagnostic Tool overview](../../screenshots/ntp-nts-diagnostic-tool-overview.svg)

## Start here

- [Getting Started](Getting-Started.md) — download, run, and perform a first test.
- [Interface Guide](Interface-Guide.md) — every control, counter, and log area.
- [Testing an NTP Server](Testing-an-NTP-Server.md) — plain NTPv4 testing.
- [Testing an NTS Server](Testing-an-NTS-Server.md) — TLS 1.3 NTS-KE and authenticated NTP.
- [Understanding Results](Understanding-Results.md) — NTP fields, offset/delay, cookies, and authentication.
- [Stability Testing](Stability-Testing.md) — long-duration testing and file logging.
- [TLS & Certificate Troubleshooting](TLS-and-Certificate-Troubleshooting.md) — hostname, SAN, trust, and TLS issues.
- [Troubleshooting](Troubleshooting.md) — common NTP/NTS failures.
- [Security & Technical Notes](Security-and-Technical-Notes.md) — standards, security, and timing limitations.

Version 2.0.2 is retained as the project's known-good interoperability baseline. It has completed authenticated NTS exchanges against Cloudflare's public NTS service and an independent ESP32-P4 NTS implementation.
