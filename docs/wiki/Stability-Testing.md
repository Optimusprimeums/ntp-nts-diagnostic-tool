# Stability Testing

The application can run hundreds of requests to exercise an NTP/NTS server over an extended period.

## Recommended workflow

1. Enter the target server.
2. Enable NTS when testing an NTS implementation.
3. Keep TLS verification enabled for normal authenticated testing.
4. Increase **Number of Requests**.
5. Select a suitable **Delay (ms)**.
6. Enable **Log to File** and choose a destination.
7. Click **Start Requests**.
8. Monitor the Real-Time Statistics while the test runs.
9. Preserve the log after completion for analysis.

For example, **500 requests at 5000 ms** exercises the server for roughly 42 minutes plus network and processing time.

A clean completed run can show:

```text
Sent:          500
Received:      500
Failures:        0
NTS Failures:    0
KoD Packets:     0
```

For NTS, also inspect the log for repeated `NTS AUTHENTICATED` results and healthy cookie-pool replenishment.

## What this demonstrates

A zero-failure run is useful evidence of protocol interoperability and stability over the test interval. Timing offset/delay remains subject to userspace timestamping, OS scheduling, network asymmetry, and server timestamp placement.
