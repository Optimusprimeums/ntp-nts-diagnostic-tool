# TLS & Certificate Troubleshooting

With certificate verification enabled, **Server (IP/FQDN)** must be valid for the server certificate.

A message saying that a certificate is not valid for an IP address means certificate identity validation was reached but the certificate does not cover that raw IP. Prefer the DNS hostname covered by the certificate. If raw-IP access is required, the certificate needs that address as an IP Subject Alternative Name.

**Skip TLS certificate verification** can isolate certificate problems in controlled development, but removes server identity verification and should not be normal operation.

Also check SAN entries, validity dates, issuing CA/trust chain, Windows trust, TCP 4460 reachability, and whether the server is actually running NTS-KE.
