# Registered replication method

Population / fixture: 1,000 deterministic JSON documents generated from the same versioned fixture set.

Procedure: run baseline parser and candidate parser on the same fixture set in randomized order, after five warm-up passes, for ten measured passes each.

Measurement: median wall-clock parse latency in milliseconds and total parse-error count.

Analysis: compare median latency across measured passes. The registered claim is supported only if candidate latency is at least 12% lower and the candidate error count is not higher than baseline.

Window: one controlled benchmark session using the frozen fixture version.
