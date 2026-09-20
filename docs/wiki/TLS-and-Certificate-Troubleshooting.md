# TLS & Certificate Troubleshooting

NTS uses TLS 1.3 during NTS Key Establishment, so server identity and certificate validation matter.

## Hostname and IP SAN errors

With certificate verification enabled, the value entered in **Server (IP/FQDN)** must be valid for the server certificate.

For example:

```text
certificate is not valid for IP address 192.168.2.54
```

means the connection reached certificate identity validation but the certificate is not valid for that raw IP address.

If the certificate contains the server's DNS name, use that DNS hostname. If raw-IP access is required, the certificate must contain the address as an IP Subject Alternative Name.

## Skip TLS certificate verification

This option disables certificate verification. It can help isolate certificate problems in a controlled development environment, but it removes server identity verification and should not be the normal configuration.

## Other checks

For certificate validation failures, check:

- the hostname or IP entered in the application;
- Subject Alternative Names;
- certificate validity dates;
- issuing CA/trust chain;
- the local Windows trust environment.

For NTS-KE connectivity failures, also verify TCP port 4460 reachability and that the server is actually running an NTS-KE service.
