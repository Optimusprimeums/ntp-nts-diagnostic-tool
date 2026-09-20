# Interface Guide

![Annotated interface overview](https://raw.githubusercontent.com/Optimusprimeums/ntp-nts-diagnostic-tool/main/screenshots/ntp-nts-diagnostic-tool-overview.svg)

The interface contains **Configuration**, **Real-Time Statistics**, and **Running Log**. The v2.1.0 development interface additionally includes **NTP Peer Test Responder** controls.

## Configuration

**Server (IP/FQDN)** selects the target. **Number of Requests** and **Delay (ms)** control the test duration. **Enable NTS (TCP 4460)** enables RFC 8915 NTS. **Skip TLS certificate verification** is for controlled certificate diagnostics and should remain unchecked normally.

**Log to File** preserves the full diagnostic output. **Select Log File...** chooses its destination. **Start Requests** begins a run and **Stop** interrupts it.

## NTP Peer Test Responder (v2.1.0 development)

The responder has a configurable **Bind** address, **UDP Port**, **Response Mode**, independent **Start Responder / Stop Responder** controls, and **Run Self-Test Suite**. The self-test performs 19 loopback regression checks and reports PASS/FAIL results in the Running Log. It monitors incoming peer/client requests in the Running Log and can return controlled valid or fault-injected NTP responses. See [NTP Peer Monitoring & Fault Injection](NTP-Peer-Monitoring-and-Fault-Injection).

## Real-Time Statistics

**Sent** and **Received** count traffic. **Failures** counts general failures, **NTS Failures** counts NTS-specific failures, and **KoD Packets** counts Kiss-o'-Death responses.

A clean 500-request run can show:

```text
Sent: 500   Received: 500   Failures: 0   NTS Failures: 0   KoD Packets: 0
```

## Running Log

The log shows request numbering, authenticated packet construction, UDP transmission/reception, NTP fields, offset/delay, UID matching, S2C tag verification, replacement cookies, and cookie-pool state.

## Running Log controls

The v2.0.2 and v2.1.0 GUI source includes **Copy Log** and **Clear Log** controls above the Running Log. **Copy Log** places the complete displayed log on the system clipboard. **Clear Log** removes the displayed text only; it does not stop an active request/responder operation or delete the configured log file.

## Linux v2.1.0

The Linux distribution uses a headless CLI rather than the Tkinter GUI. Its `query`, `peer`, and `self-test` commands are suitable for terminal and SSH use.



## v2.1.0 interface overview

![Annotated NTP/NTS Diagnostic Tool v2.1.0 overview](https://raw.githubusercontent.com/Optimusprimeums/ntp-nts-diagnostic-tool/main/screenshots/ntp-nts-diagnostic-tool-v2.1.0-overview.svg)
