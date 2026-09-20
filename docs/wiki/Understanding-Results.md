# Understanding Results

**LI** is the Leap Indicator, **VN** the NTP version, **Mode=4** a server response, and **Stratum** the server stratum.

**offset** is the four-timestamp NTP offset estimate; **network delay** is the corresponding round-trip delay estimate.

For NTS, **NTS-KE SUCCESS** confirms key establishment and `ntske/1` negotiation. **UID matched** associates the response with its request. **S2C tag verified** confirms response authentication. **new cookies=1, pool=8** reports replacement-cookie and pool state.

For stability tests, compare Sent/Received and watch Failures, NTS Failures, and KoD Packets. Zero counters establish that the application counted no failures during the completed exchanges; they do not establish sub-microsecond clock accuracy.

## Peer responder results (v2.1.0 development)

Responder log lines identify the requesting peer address, datagram size and active response mode. The responder then records whether it sent a normal/fault-injected response, deliberately dropped the request, delayed it, or replayed an earlier response. Use the peer's own logs/status together with this responder log to determine whether the peer accepted, rejected, timed out, backed off, or otherwise handled the injected condition.
