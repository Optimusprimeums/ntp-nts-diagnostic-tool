# NTP Peer Monitoring and Fault Injection

v2.1.0 adds an integrated **NTP Peer Test Responder** for exercising another NTP implementation while monitoring the requests it sends.

## What it monitors

When the responder receives an NTP datagram it logs the source IP/port, request length, selected fault-injection mode, response stratum and reference ID. Requests shorter than the 48-byte NTP header are logged and ignored. The responder runs independently from the normal NTP/NTS client worker and can be stopped without closing the application.

The default bind address is `0.0.0.0` and the default port is UDP/123. On Windows, UDP/123 can already be occupied by Windows Time or another NTP service and may require elevated privileges. A different port can be selected for controlled lab tests.

## Original peer-test modes

| Mode | Behavior |
| --- | --- |
| `valid` | 48-byte NTPv4 Mode 4, stratum-1 response with matching originate timestamp |
| `kod` | Stratum 0 Kiss-o'-Death response with RefID `RATE` |
| `bad-originate` | Deliberately replaces the request-correlating originate timestamp |
| `short` | Sends a deliberately malformed 16-byte reply |
| `duplicate` | Reuses the same T3 transmit timestamp after the first response |

## Advanced modes

| Mode | Behavior / peer behavior under test |
| --- | --- |
| `kod-deny` | Stratum 0 / `DENY` |
| `kod-rstr` | Stratum 0 / `RSTR` |
| `wrong-mode` | Responds with client Mode 3 instead of server Mode 4 |
| `bad-version` | Uses an invalid NTP version field |
| `zero-t2` | Zero receive timestamp |
| `zero-t3` | Zero transmit timestamp |
| `li-alarm` | LI=3 alarm/unsynchronized indication |
| `stratum-16` | Unsynchronized stratum value |
| `drop` | Receives and logs the request but sends no response |
| `delayed` | Delays the response by 1 second |
| `offset-plus-100ms` | Shifts T2/T3 forward by 100 ms |
| `offset-minus-100ms` | Shifts T2/T3 backward by 100 ms |
| `processing-100ms` | Inserts 100 ms between receive and transmit timestamp generation |
| `replay` | Saves the first complete response and replays it unchanged for later requests |

## Peer-validation uses

The modes are intended to show whether the peer/client rejects malformed correlation fields and invalid headers, recognizes KoD/policy responses, handles LI/stratum unsynchronized indications, times out cleanly when packets are dropped, behaves sensibly with latency and processing delay, and rejects or otherwise safely handles replayed/stale responses.

The running log is the primary peer-monitoring record. For longer tests, enable **Log to File** so request/response behavior can be reviewed after the run.

## Scope

This responder currently targets plain NTP packet behavior. NTS fault injection (bad UID, invalid authenticator, malformed encrypted extension fields, stale cookies, NTSN, and NTS-KE negotiation faults) is a separate future test layer because those cases require controlled modification of authenticated NTS structures.
