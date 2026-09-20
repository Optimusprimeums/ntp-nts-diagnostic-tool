# NTP/NTS Diagnostic Tool Wiki

Welcome to the user documentation for **NTP/NTS Diagnostic Tool**. v2.0.2 remains the known-good NTS interoperability baseline; v2.1.0 is the development version adding integrated NTP peer monitoring, a peer test responder, and fault injection.

![Annotated NTP/NTS Diagnostic Tool overview](https://raw.githubusercontent.com/Optimusprimeums/ntp-nts-diagnostic-tool/main/screenshots/ntp-nts-diagnostic-tool-overview.svg)

## Documentation

- [Getting Started](Getting-Started)
- [Interface Guide](Interface-Guide)
- [Testing an NTP Server](Testing-an-NTP-Server)
- [NTP Peer Monitoring & Fault Injection](NTP-Peer-Monitoring-and-Fault-Injection)
- [Testing an NTS Server](Testing-an-NTS-Server)
- [Understanding Results](Understanding-Results)
- [Stability Testing](Stability-Testing)
- [TLS & Certificate Troubleshooting](TLS-and-Certificate-Troubleshooting)
- [Troubleshooting](Troubleshooting)
- [Security & Technical Notes](Security-and-Technical-Notes)

Version 2.0.2 is retained as the project's known-good interoperability baseline. It has completed authenticated NTS exchanges against Cloudflare's public NTS service and an independent ESP32-P4 NTS implementation.

## v2.1.0 additions

The development release also adds **Copy Log** and **Clear Log** controls to the Running Log. Linux gains a headless command-line distribution for NTP/NTS queries, peer fault injection, and responder smoke testing, so a desktop session is not required for the Linux CLI.

