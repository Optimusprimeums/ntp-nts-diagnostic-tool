# NTP/NTS Diagnostic Tool

A Windows diagnostic utility for testing **NTPv4** and **Network Time Security (NTS)** servers.

Version **2.0.2** remains the known-good NTS interoperability baseline. **v2.1.0 is the current development version** and adds an integrated NTP peer test responder and fault-injection/peer-monitoring tools. It performs real NTS Key Establishment over TLS 1.3, negotiates `ntske/1`, derives client-to-server and server-to-client keys with the TLS exporter, exchanges NTS cookies, creates authenticated NTP requests using AEAD AES-SIV-CMAC-256, verifies authenticated replies, and reports NTP offset and network delay.

![Annotated NTP/NTS Diagnostic Tool v2.0.2 overview](screenshots/ntp-nts-diagnostic-tool-overview.svg)

*Annotated overview of the v2.0.2 interface and major diagnostic features.*

## Quick start

1. Download the standalone Windows executable from the latest GitHub Release.
2. Enter the NTP/NTS server hostname or IP address.
3. Leave **Enable NTS** checked for RFC 8915 testing, or clear it for plain NTP.
4. Keep TLS certificate verification enabled for normal NTS operation.
5. Choose the request count and delay, then start the test.
6. Optionally enable **Log to File** and choose a destination with **Select Log File...** for long stability runs.
7. Click **Start Requests**. Use **Stop** to interrupt an active run.
8. Watch **Real-Time Statistics** for Sent, Received, Failures, NTS Failures, and KoD Packets.
9. For NTS, look for **NTS-KE SUCCESS** followed by **NTS AUTHENTICATED** on each successful exchange.

See the [complete user guide](docs/wiki/Home.md) for field descriptions, examples, output interpretation, certificate troubleshooting, and timing limitations.

## NTP peer monitoring and fault injection

v2.1.0 adds an integrated **NTP Peer Test Responder**. It listens for incoming NTP client/peer requests, logs the source address, request size and selected response behavior, and sends controlled replies so peer implementations can be monitored and validated.

The responder preserves the original peer-test behaviors: `valid`, `kod` (RATE), `bad-originate`, `short` (16-byte malformed reply), and `duplicate` T3. Advanced modes add `kod-deny`, `kod-rstr`, `wrong-mode`, `bad-version`, `zero-t2`, `zero-t3`, `li-alarm`, `stratum-16`, `drop`, `delayed`, ±100 ms timestamp offset, 100 ms processing delay, and full-response `replay`.

This makes the tool useful in both directions: it can actively test an NTP/NTS server, or act as a controlled NTP server endpoint while monitoring how another NTP peer/client behaves under valid, malformed, stale, delayed, unsynchronized and policy-response conditions.

> **Development note:** v2.1.0 is not yet the tagged stable release. Keep v2.0.2 for the validated public-NTS baseline until v2.1.0 regression testing is complete.

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
