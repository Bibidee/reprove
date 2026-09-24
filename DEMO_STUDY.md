# Synthetic live-demo study

Use this only as a non-sensitive demonstration. Replace `<PRODUCTION_URL>` after Vercel deployment.

## Study registration

- Study key: `parser-cache-01`
- Title: `Bounded symbol caching and parse latency`
- Field: `Software performance research`
- Claim: `Enabling the bounded symbol-cache strategy reduces median parse latency by at least 12% on the registered 1,000-document fixture without increasing parse errors.`
- Population: `The frozen 1,000-document JSON fixture set.`
- Procedure: `Baseline and candidate run on the same fixture in randomized order after five warm-up passes, followed by ten measured passes each.`
- Measurement: `Median wall-clock parse latency in milliseconds and total parse-error count.`
- Analysis: `Compare median latency; calculate relative reduction; verify candidate error count does not exceed baseline.`
- Window: `One controlled benchmark session using the frozen fixture version.`
- Outcome rule: `REPLICATED only if protocol is satisfied, required evidence is sufficient, median candidate latency is at least 12% lower than baseline, and candidate parse errors do not exceed baseline. FAILED_TO_REPLICATE only when the protocol and evidence are sufficient but the 12% criterion is not met or errors increase.`
- Required evidence kinds: `PREREGISTRATION_REFERENCE`, `METHOD`, `DATASET`, `ANALYSIS`, `RESULT_TABLE`
- Minimum distinct origins: `2`
- Suggested allowed origins after deployment: `<PRODUCTION_ORIGIN>` and `https://raw.githubusercontent.com`
- Suggested required origin: `https://raw.githubusercontent.com`
- Suggested reward: `5 GEN`
- Suggested max rewarded attempts: `2`

## Attempt evidence

Use public HTTPS URLs corresponding to:

- `<PRODUCTION_URL>/demo-evidence/preregistration.md`
- `<PRODUCTION_URL>/demo-evidence/method.md`
- `<PRODUCTION_URL>/demo-evidence/dataset.csv`
- `<PRODUCTION_URL>/demo-evidence/analysis.md`
- `<PRODUCTION_URL>/demo-evidence/result-table.csv`

For reviewer-quality source diversity, mirror at least the preregistration or method file to the final public GitHub repository and use the raw GitHub URL for that evidence leaf. Do not claim independent origins if all files are hosted on the same domain.
