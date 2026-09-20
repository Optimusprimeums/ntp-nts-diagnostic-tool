# NTP/NTS Diagnostic Tool

A Windows diagnostic utility for testing **NTPv4** and **Network Time Security (NTS)** servers.

Version **2.0.2** is the current known-good interoperability baseline. It performs real NTS Key Establishment over TLS 1.3, negotiates `ntske/1`, derives client-to-server and server-to-client keys with the TLS exporter, exchanges NTS cookies, creates authenticated NTP requests using AEAD AES-SIV-CMAC-256, verifies authenticated replies, and reports NTP offset and network delay.

![NTP/NTS Diagnostic Tool interface](screenshots/interface-overview.svg)

## Quick start

1. Download the standalone Windows executable from the latest GitHub Release.
2. Enter the NTP/NTS server hostname or IP address.
3. Leave **Enable NTS** checked for RFC 8915 testing, or clear it for plain NTP.
4. Keep TLS certificate verification enabled for normal NTS operation.
5. Choose the request count and delay, then start the test.
6. For NTS, look for **NTS-KE SUCCESS** followed by **NTS AUTHENTICATED** on each successful exchange.

See the [complete user guide](docs/wiki/Home.md) for field descriptions, examples, output interpretation, certificate troubleshooting, and timing limitations.

## Validated interoperability

2.0.2 has completed repeated authenticated NTS exchanges against Cloudflare's public `time.cloudflare.com` service and an independent ESP32-P4 NTS server.

## Security

TLS certificate verification is enabled by default. **Skip TLS Verify** is intended only for controlled development and certificate-diagnostic testing. The application intentionally does not log derived NTS keys.

## Windows build

End users can use the standalone Windows executable without installing Python. Developers can build from source with the included `build_windows.bat` or the GitHub Actions Windows workflow.

## Standards

- RFC 5905 — Network Time Protocol Version 4
- RFC 8915 — Network Time Security for the Network Time Protocol
- RFC 5297 — Synthetic Initialization Vector authenticated encryption

## Timing note

Client T1/T4 are application/userspace observations rather than NIC hardware timestamps. This application is intended for protocol diagnostics and interoperability testing, not as a sub-microsecond hardware timestamp reference.

## License

MIT.
