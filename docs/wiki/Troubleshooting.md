# Troubleshooting

**NTS-KE timeout/refused:** check TCP 4460 reachability, firewall rules, and the NTS-KE service.

**ALPN failure:** the TLS peer did not negotiate required `ntske/1`.

**Certificate validation failure:** check hostname/IP, SAN, validity dates, trust chain, and Windows trust.

**No cookies returned:** NTS-KE did not provide material needed for authenticated NTP.

**NTS authentication failure:** the response could not be authenticated with the negotiated S2C key.

**UID/originate mismatch:** the received response does not correspond to the request being validated.

**KoD packet:** inspect the NTP stratum-zero reference identifier and server policy/rate limiting.

**Unexpected timing:** Windows userspace timestamping, scheduling, path asymmetry, load, and server timestamp placement can affect offset/delay.
