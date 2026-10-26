# Operational Rules (Remote Tester)
1. Test every single remote endpoint in sequence; never skip or batch unverified calls.
2. Test both valid inputs and adversarial boundary cases (nulls, overflows, rapid bursts).
3. Validate HTTP 200/202 responses and check latency benchmarks (< 200ms).
4. Record structured output in api_test_results.log with empirical Exit Code 0 evidence.
