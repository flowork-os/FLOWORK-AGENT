# Operational Rules (Remote Tester)
1. MANDATORY LIVE ENVIRONMENT: Always test against the real running Flowork engine (http://localhost:19890) and live app instance. Unit mocks or isolated sandbox tests are strictly prohibited.
2. BEYOND EXIT CODE 0: Exit Code 0 is merely a shell baseline. You must verify actual live response payloads, socket event emission, and latency benchmarks (< 200ms).
3. Test every single remote endpoint in sequence; never skip or batch unverified calls.
4. Test both valid inputs and adversarial boundary cases (nulls, overflows, rapid bursts).
5. Record live execution traces in api_test_results.log with exact timestamps and live network response data.
