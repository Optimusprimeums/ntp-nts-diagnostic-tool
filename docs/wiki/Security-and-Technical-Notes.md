# Security & Technical Notes

The v2.0.2 client is based on RFC 5905 (NTPv4), RFC 8915 (NTS), and RFC 5297 (SIV authenticated encryption).

NTS mode uses TLS 1.3 NTS-KE, `ntske/1`, TLS-exporter-derived C2S/S2C keys, NTS cookies, and AEAD_AES_SIV_CMAC_256 (AEAD 15).

TLS certificate verification is enabled by default. The application intentionally does not log derived C2S/S2C keys. Review logs before publishing them because hostnames, internal IPs, paths, or infrastructure details may be environment-specific.

Client T1/T4 are application/userspace observations rather than Ethernet NIC hardware timestamps. The tool is intended for NTP/NTS protocol diagnostics, interoperability validation, and practical timing investigation—not as a sub-microsecond hardware timestamp reference.

Version 2.0.2 is retained as the known-good interoperability baseline.

v2.1.0 Windows permission assistance is explicit and opt-in: elevation and firewall authorization are separate prompts. The optional firewall rule allows inbound UDP/123 on Domain and Private profiles and excludes Public. Linux does not automatically elevate or modify firewall policy.

The Linux v2.1.0 CLI is intended to expose the diagnostic and peer-test functionality without requiring a graphical desktop.

