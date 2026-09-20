# Troubleshooting

## NTS-KE connection refused or timeout

The NTS-KE service may be unreachable, not listening on TCP 4460, or blocked by a firewall.

## ALPN negotiation failure

RFC 8915 NTS-KE requires the `ntske/1` ALPN. A failure here means the TLS peer did not negotiate the required protocol.

## Certificate validation failure

Check the server name, SAN entries, certificate dates, trust chain, and Windows trust environment. See [TLS & Certificate Troubleshooting](TLS-and-Certificate-Troubleshooting.md).

## No cookies returned

The NTS-KE exchange did not provide the cookie material needed for authenticated NTP requests.

## NTS response authentication failed

The returned NTP packet could not be authenticated with the negotiated server-to-client key.

## UID mismatch

The response NTS Unique Identifier does not match the request being validated.

## Originate timestamp mismatch

The returned NTP response does not contain the expected originate timestamp corresponding to the request.

## KoD packet

A Kiss-o'-Death response is an NTP stratum-zero control/rate-limit response. Check the reported reference identifier and server policy.

## Timing looks unexpectedly large

Offset and delay can be affected by Windows userspace timestamp placement, scheduling, path asymmetry, network load, and server timestamp placement. This tool is primarily for protocol diagnostics and interoperability testing.
