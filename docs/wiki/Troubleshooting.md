# Troubleshooting

**NTS-KE timeout/refused:** check TCP 4460 reachability, firewall rules, and the NTS-KE service.

**ALPN failure:** the TLS peer did not negotiate required `ntske/1`.

**Certificate validation failure:** check hostname/IP, SAN, validity dates, trust chain, and Windows trust.

**No cookies returned:** NTS-KE did not provide material needed for authenticated NTP.

**NTS authentication failure:** the response could not be authenticated with the negotiated S2C key.

**UID/originate mismatch:** the received response does not correspond to the request being validated.

**KoD packet:** inspect the NTP stratum-zero reference identifier and server policy/rate limiting.

**Unexpected timing:** Windows userspace timestamping, scheduling, path asymmetry, load, and server timestamp placement can affect offset/delay.


**Peer responder cannot bind UDP/123:** stop another local NTP service using the port, run with appropriate privileges where required, or select another UDP port for a controlled test.

**Peer sends no requests:** verify that the peer is configured for the responder's address/port and that host/network firewalls permit UDP traffic.

**Fault mode appears to have no effect:** confirm the Running Log shows incoming requests and the intended response mode. Then inspect the peer's own monitoring/logs; several fault modes are specifically designed to be rejected silently by a correct peer.
