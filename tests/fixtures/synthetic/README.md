# Fictional test cases

`tests/conftest.py` builds deterministic fictional markets and books. None is seeded into the live database or shown as real prices. Unit cases cover the specified 0.54 + 0.43 + 0.02 = 0.99 construction, unsupported lots/fees, date/threshold differences, stale/skewed snapshots, and the DD+RD Senate replication with an explicit OTHER state. The browser virtualization test marks every row FICTIONAL BENCHMARK.
