# Testing an NTP Server

1. Enter the server hostname or IP.
2. Clear **Enable NTS (TCP 4460)**.
3. Choose request count and delay.
4. Optionally enable **Log to File**.
5. Click **Start Requests**.

A valid reply reports `LI`, `VN`, `Mode`, `Stratum`, offset, and network delay. A normal server reply uses `Mode=4`. Stratum zero is treated as a Kiss-o'-Death/control response.

The displayed timing is diagnostic: client T1/T4 are Windows userspace/socket/system-clock observations, not NIC hardware timestamps.

## Testing the other direction: monitoring an NTP peer

v2.1.0 can also listen as a controlled NTP server while another NTP client/peer sends requests to it. Use the **NTP Peer Test Responder** to observe request source/size and exercise peer handling of valid replies, KoD, timestamp correlation faults, malformed packets, duplicate/replayed responses, unsynchronized states, delay and packet loss. See [NTP Peer Monitoring & Fault Injection](NTP-Peer-Monitoring-and-Fault-Injection.md).
