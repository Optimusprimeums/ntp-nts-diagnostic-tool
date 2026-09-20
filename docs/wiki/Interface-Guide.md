# Interface Guide

![Annotated interface overview](../../screenshots/ntp-nts-diagnostic-tool-overview.svg)

The v2.0.2 interface contains **Configuration**, **Real-Time Statistics**, and **Running Log**.

## Configuration

**Server (IP/FQDN)** selects the target. **Number of Requests** and **Delay (ms)** control the test duration. **Enable NTS (TCP 4460)** enables RFC 8915 NTS. **Skip TLS certificate verification** is for controlled certificate diagnostics and should remain unchecked normally.

**Log to File** preserves the full diagnostic output. **Select Log File...** chooses its destination. **Start Requests** begins a run and **Stop** interrupts it.

## Real-Time Statistics

**Sent** and **Received** count traffic. **Failures** counts general failures, **NTS Failures** counts NTS-specific failures, and **KoD Packets** counts Kiss-o'-Death responses.

A clean 500-request run can show:

```text
Sent: 500   Received: 500   Failures: 0   NTS Failures: 0   KoD Packets: 0
```

## Running Log

The log shows request numbering, authenticated packet construction, UDP transmission/reception, NTP fields, offset/delay, UID matching, S2C tag verification, replacement cookies, and cookie-pool state.
