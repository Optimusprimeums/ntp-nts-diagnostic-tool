# Testing an NTP Server

Use this mode to test conventional NTPv4 without NTS authentication.

1. Enter the server hostname or IP address.
2. Clear **Enable NTS (TCP 4460)**.
3. Choose **Number of Requests** and **Delay (ms)**.
4. Optionally enable **Log to File**.
5. Click **Start Requests**.

A valid server reply reports fields including `LI`, `VN`, `Mode`, and `Stratum`, followed by calculated offset and network delay.

A normal server response uses **Mode=4**. A stratum-zero response is handled as a Kiss-o'-Death response and its reference identifier is reported.

The displayed timing values are useful for diagnostics, but client T1/T4 are userspace/socket/system-clock observations rather than Ethernet NIC hardware timestamps. See [Security & Technical Notes](Security-and-Technical-Notes.md).
