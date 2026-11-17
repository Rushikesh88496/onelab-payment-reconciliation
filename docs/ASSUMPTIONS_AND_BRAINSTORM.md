# Assessment thinking notes — ClearMatch

## Problem framing
The company has two event streams:
- Platform transactions: records customer activity immediately.
- Bank settlements: records money received later, often in batches.

A month-end total comparison alone is insufficient. A valid October transaction may settle in November, and duplicate or unmatched bank rows can distort the bank total. The solution therefore needs row-level matching plus a period cutoff view.

## Questions considered
1. What uniquely identifies a payment? Assumption: transaction ID, with transaction type included.
2. Should late settlements be treated as missing? No. Search beyond the reporting cutoff for a matching later settlement and classify it as timing.
3. How to prevent duplicates from inflating totals? Keep one bank row per transaction/type for primary matching; flag extra rows and exclude them from the unique bank total.
4. How to handle tiny monetary differences? Use Decimal, a configurable tolerance, and separate statuses for exact vs within-tolerance matches.
5. How to detect an orphan refund? A bank refund whose transaction ID/type has no platform counterpart.
6. What should the user receive? Summary metrics, row-level exception report, and downloadable CSV.

## Design decision
Use deterministic Python/Pandas logic rather than asking an LLM to decide whether money matches. Financial calculations should be reproducible and testable. An LLM could later explain exceptions, but should not be the source of truth.

## Genuine conversation record
This document is a structured design note, not a verbatim transcript. Attach/export the actual brainstorming conversation separately as requested by the assessment.
