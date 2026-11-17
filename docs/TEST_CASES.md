# Test cases

| ID | Scenario | Input condition | Expected result |
|---|---|---|---|
| TC01 | Exact match | Same transaction ID/type and exact amount | Matched |
| TC02 | Late settlement | October transaction settled November 1 | Late settlement (next period) |
| TC03 | Rounding | Amount differs by one cent within tolerance | Matched within rounding tolerance |
| TC04 | Aggregate rounding | Three rows each differ by one cent | Three rounding exceptions; total variance accumulates |
| TC05 | Duplicate bank row | Same transaction ID/type appears twice in bank file | Extra row flagged duplicate and excluded from unique bank total |
| TC06 | Orphan refund | Bank refund ID absent from platform | Orphan refund |
| TC07 | Missing settlement | Platform transaction has no bank counterpart | Missing settlement |
| TC08 | Invalid platform duplicate | Platform transaction ID repeated | Input validation error |
| TC09 | Invalid amount | Negative or nonnumeric amount | Input validation error |
| TC10 | Configurable tolerance | Difference exceeds configured tolerance | Amount mismatch |

Run with `pytest -q`.
