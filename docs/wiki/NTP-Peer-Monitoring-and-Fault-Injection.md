# NTP Peer Monitoring and Fault Injection

v2.1.0 adds an integrated **NTP Peer Test Responder** for exercising another NTP implementation while monitoring the requests it sends.

## Windows startup permissions

v2.1.0 performs a Windows privilege check shortly after startup. When the process is not elevated, it offers to restart through the standard Windows UAC **Run as administrator** flow. Declining does not close the application.

When the application is already elevated, it separately asks whether to configure Windows Defender Firewall for inbound peer testing. If approved, it creates/refreshes the rule `NTP-NTS Diagnostic Tool Peer Responder` for inbound **UDP/123** on **Domain and Private** profiles. The Public profile is intentionally excluded.

The elevation and firewall actions are separate and opt-in. Administrator status alone does not guarantee that inbound UDP/123 is permitted through the firewall.

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

## Automated responder self-test

Click **Run Self-Test Suite** to regression-test the integrated responder without requiring another machine. The suite binds each case to loopback on an ephemeral UDP port, generates a fresh NTP client request, captures the response, and checks the expected packet property.

The current suite performs 19 checks covering valid replies, RATE/DENY/RSTR KoD, bad originate, 16-byte malformed replies, wrong mode/version, zero T2/T3, LI=3, stratum 16, duplicate T3, byte-for-byte replay, intentional packet drop, one-second delay, ±100 ms timestamp shifts, and approximately 100 ms T2→T3 processing delay.

Results appear in the Running Log:

```text
=== PEER RESPONDER SELF-TEST: 19 checks ===
[PASS] valid | response=48 bytes
...
[PASS] replay
[PASS] drop | request intentionally unanswered
...
=== PEER RESPONDER SELF-TEST COMPLETE: 19 passed / 0 failed ===
```

A PASS means the local responder generated the intended wire behavior. It does **not** mean an external NTP implementation correctly handled that behavior. For peer interoperability testing, point the external peer at the responder and correlate this application's Running Log with the peer's own logs/status.

## Headless Linux peer responder

v2.1.0 also provides a Linux CLI responder, allowing fault injection without a graphical desktop:

```bash
./NTP-NTS-Diagnostic-Tool peer --bind 0.0.0.0 --port 123 --mode valid
./NTP-NTS-Diagnostic-Tool peer --bind 0.0.0.0 --port 123 --mode replay
```

The CLI exposes the responder modes used by the v2.1.0 peer-test implementation. Linux firewall and privileged-port configuration remain administrator-controlled.

