# Releasing

1. Confirm the intended `ntp_nts_tester_vX_Y_Z.py` is the highest versioned source.
2. Run `build_windows.bat`.
3. Test the resulting `dist\NTP-NTS-Diagnostic-Tool.exe` in NTP-only and NTS modes.
4. Verify certificate validation remains enabled by default.
5. Test against at least one independent NTS implementation.
6. Code-sign the executable when a signing certificate is available.
7. Create and push a tag such as `v2.0.2`.

A `v*` tag triggers the Windows GitHub Actions workflow and publishes the executable as a GitHub Release asset.
