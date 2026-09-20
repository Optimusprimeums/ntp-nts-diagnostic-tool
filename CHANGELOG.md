# Changelog

## [2.0.2] - 2026-09-19

### Fixed
- Corrected TLS handshake helper regression introduced during timeout handling.
- Retained robust pyOpenSSL WantRead/WantWrite handling.

### Validated
- Successful end-to-end NTS interoperability with `time.cloudflare.com`.
- TLS 1.3 and `ntske/1` ALPN negotiation.
- AEAD AES-SIV-CMAC-256 authentication.
- NTS cookie replenishment and repeated authenticated replies.
- Successful independent ESP32-P4 NTS server interoperability.

## [2.0.1] - 2026-09-19

- Added pyOpenSSL nonblocking/timeout handling.
- Improved exception diagnostics.

## [2.0.0] - 2026-09-19

- Added real RFC 8915 NTS-KE.
- Added TLS exporter key derivation, cookies, Unique Identifier, authenticated NTP requests/replies, timing calculations, IPv4/IPv6 resolution, and stricter NTP validation.
