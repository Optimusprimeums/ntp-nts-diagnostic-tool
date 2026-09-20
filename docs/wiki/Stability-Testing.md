# Stability Testing

For an extended test, increase **Number of Requests**, choose **Delay (ms)**, enable **Log to File**, select a destination, and start the run.

For example, **500 requests at 5000 ms** exercises the server for roughly 42 minutes plus network/processing time.

Monitor the counters throughout the run. A completed result of Sent 500, Received 500, Failures 0, NTS Failures 0, and KoD Packets 0 shows all configured exchanges completed without a counted failure.

For NTS, also inspect the saved log for repeated NTS AUTHENTICATED results and healthy cookie-pool replenishment. Timing remains subject to userspace timestamp placement, OS scheduling, network asymmetry, and server timestamp placement.
