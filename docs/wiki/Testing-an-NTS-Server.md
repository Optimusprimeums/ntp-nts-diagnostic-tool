# Testing an NTS Server

NTS mode tests RFC 8915 key establishment and authenticated NTP exchanges.

## Configure the test

1. Enter the server's certificate-valid hostname.
2. Check **Enable NTS (TCP 4460)**.
3. Leave **Skip TLS certificate verification** unchecked for normal operation.
4. Choose the request count and delay.
5. Optionally enable **Log to File**.
6. Click **Start Requests**.

## NTS-KE

A successful key-establishment phase should include output similar to:

```text
NTS-KE SUCCESS: TLSv1.3, TLS_AES_256_GCM_SHA384, ALPN=ntske/1, AEAD=15
NTS-KE: received 8 cookie(s); NTP endpoint=time.cloudflare.com:123
NTS-KE: C2S/S2C keys derived with TLS exporter
```

The client negotiates the `ntske/1` ALPN and uses AEAD 15 (AEAD_AES_SIV_CMAC_256).

## Authenticated NTP

Each successful exchange should end with output similar to:

```text
NTS AUTHENTICATED: UID matched, S2C tag verified, new cookies=1, pool=8
```

This is the key end-to-end result: the response corresponds to the request and authenticates using the negotiated server-to-client key.

The cookie pool allows subsequent authenticated UDP exchanges without keeping the TLS connection open.
