# Day 19 Member 1 Evidence

**Date:** 2026-10-17 (Asia/Calcutta). **Branch:** `member1/security-architecture`.

**Assignment:** Define identity, route and resource-cost limits.

[LIMIT-LAB-1.0](identity-route-resource-limits.md) defines twenty numeric limit
rows: request/subject/route buckets, weighted costs, concurrency, key/byte caps,
bounded request parsing, events/batches/queues, retry deadlines and adapter
decisions. It excludes raw credentials, object IDs and query strings from keys.

Arithmetic checks confirm MRVP's normal 100-RPS mix costs 390 units/s within
the 400-unit service budget. Per-subject costs are 190 and 200, within 300.
Ten thousand 4-KiB events exceed 16 MiB, so the documented lower byte limit wins.
These consistency checks do not measure throughput or resource consumption.

Verification also uses [common checks](member1-oct17-verification.md):
40 application/contract tests PASS and compilation PASS. LM IDs, links and
whitespace are checked before handoff. Limiter, pagination, bounded collector
and load/recovery tests are absent; profile activation is BLOCKED and R-010
remains High/Open. Day 21 must settle route-specific dependency failure behavior.
