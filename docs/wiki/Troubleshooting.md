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


**Administrator prompt at startup:** v2.1.0 recommends elevation for UDP/123 peer-responder operation and for firewall-rule creation. You may decline and continue normally.

**Firewall prompt:** when elevated, approving the prompt creates/refreshes the `NTP-NTS Diagnostic Tool Peer Responder` inbound UDP/123 rule for Domain/Private profiles. Public networks are not opened automatically.

**Remote peer still cannot reach UDP/123:** verify the active Windows network profile, confirm the firewall rule is enabled, confirm another service is not bound to UDP/123, and verify routing/VLAN policy between the peer and test workstation.
