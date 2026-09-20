# Testing an NTP Server

1. Enter the server hostname or IP.
2. Clear **Enable NTS (TCP 4460)**.
3. Choose request count and delay.
4. Optionally enable **Log to File**.
5. Click **Start Requests**.

A valid reply reports `LI`, `VN`, `Mode`, `Stratum`, offset, and network delay. A normal server reply uses `Mode=4`. Stratum zero is treated as a Kiss-o'-Death/control response.

The displayed timing is diagnostic: client T1/T4 are Windows userspace/socket/system-clock observations, not NIC hardware timestamps.
