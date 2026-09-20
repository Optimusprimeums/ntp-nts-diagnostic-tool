# Interface Guide

The v2.0.2 interface has three main areas: **Configuration**, **Real-Time Statistics**, and **Running Log**.

![Annotated interface overview](../../screenshots/ntp-nts-diagnostic-tool-overview.svg)

## Configuration

**Server (IP/FQDN)** — NTP or NTS server to test. When NTS certificate verification is enabled, use a hostname or IP address covered by the server certificate.

**Number of Requests** — number of UDP NTP exchanges to perform. Small values are convenient for diagnostics; hundreds of requests can be used for stability testing.

**Delay (ms)** — pause between requests in milliseconds.

**Enable NTS (TCP 4460)** — enables RFC 8915 NTS. The client performs NTS-KE over TLS before sending authenticated NTP traffic.

**Skip TLS certificate verification** — disables TLS certificate validation. Leave this unchecked for normal use. It exists for controlled development and certificate diagnostics.

**Log to File** — writes the running diagnostic output to a persistent log.

**Select Log File...** — chooses the log destination.

**Start Requests** — starts the configured test.

**Stop** — interrupts an active test.

## Real-Time Statistics

**Sent** counts requests sent.

**Received** counts replies received.

**Failures** counts request, transport, or protocol failures recorded by the application.

**NTS Failures** counts failures specific to NTS processing/authentication.

**KoD Packets** counts NTP Kiss-o'-Death responses.

A clean 500-request stability run can therefore appear as:

```text
Sent:          500
Received:      500
Failures:        0
NTS Failures:    0
KoD Packets:     0
```

## Running Log

The Running Log shows protocol activity in real time, including request numbering, authenticated packet construction, UDP transmission/reception, NTP header fields, offset and delay, UID matching, S2C tag verification, replacement cookies, and cookie-pool state.

For long tests, enable **Log to File** so the complete output is preserved.
