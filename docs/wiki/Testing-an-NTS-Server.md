# Testing an NTS Server

Enter the server's certificate-valid hostname, enable **NTS**, leave TLS verification enabled, choose request count/delay, and click **Start Requests**.

A successful NTS-KE phase resembles:

```text
NTS-KE SUCCESS: TLSv1.3, TLS_AES_256_GCM_SHA384, ALPN=ntske/1, AEAD=15
NTS-KE: received 8 cookie(s); NTP endpoint=time.cloudflare.com:123
NTS-KE: C2S/S2C keys derived with TLS exporter
```

Each successful authenticated exchange should end with:

```text
NTS AUTHENTICATED: UID matched, S2C tag verified, new cookies=1, pool=8
```

This confirms the response UID matched and the S2C authentication tag verified. AEAD 15 is AEAD_AES_SIV_CMAC_256.

## Linux CLI

The headless v2.1.0 Linux equivalent is:

```bash
./NTP-NTS-Diagnostic-Tool query time.cloudflare.com --nts -n 5
```

TLS certificate verification remains the default. `--skip-tls-verify` is available only for deliberate diagnostic use.

