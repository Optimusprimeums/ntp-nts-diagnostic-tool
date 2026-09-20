# Understanding Results

## NTP fields

**LI** — Leap Indicator.

**VN** — NTP version.

**Mode** — NTP operating mode. A server response normally reports `Mode=4`.

**Stratum** — the server's NTP stratum. Stratum zero is used for Kiss-o'-Death/control responses rather than normal synchronized time service.

## Timing

**offset** is the standard four-timestamp NTP offset estimate based on T1/T2/T3/T4.

**network delay** is the corresponding round-trip delay estimate.

Do not interpret these values as NIC hardware timestamp measurements. Windows client T1/T4 are application/userspace observations.

## NTS results

**NTS-KE SUCCESS** means the TLS 1.3 key-establishment connection succeeded, the required `ntske/1` ALPN was negotiated, and an acceptable AEAD was selected.

**AEAD=15** means AEAD_AES_SIV_CMAC_256.

**received N cookie(s)** reports the opaque NTS cookies supplied by the server.

**UID matched** means the authenticated response corresponds to the request's NTS Unique Identifier.

**S2C tag verified** means the response authenticator verified with the negotiated server-to-client key.

**new cookies=1, pool=8** means the response returned a replacement cookie and the client retained a working cookie pool.

## Real-time counters

For stability testing, compare **Sent** and **Received** and watch **Failures**, **NTS Failures**, and **KoD Packets**. Zero failure counters across a completed run establish that the application did not count a failure during those configured exchanges; they do not by themselves establish sub-microsecond clock accuracy.
