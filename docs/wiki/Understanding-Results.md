# Understanding Results

**LI** is the Leap Indicator, **VN** the NTP version, **Mode=4** a server response, and **Stratum** the server stratum.

**offset** is the four-timestamp NTP offset estimate; **network delay** is the corresponding round-trip delay estimate.

For NTS, **NTS-KE SUCCESS** confirms key establishment and `ntske/1` negotiation. **UID matched** associates the response with its request. **S2C tag verified** confirms response authentication. **new cookies=1, pool=8** reports replacement-cookie and pool state.

For stability tests, compare Sent/Received and watch Failures, NTS Failures, and KoD Packets. Zero counters establish that the application counted no failures during the completed exchanges; they do not establish sub-microsecond clock accuracy.
