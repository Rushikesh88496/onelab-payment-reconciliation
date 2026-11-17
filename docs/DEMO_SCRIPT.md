# 90-second demo recording script

1. Open the deployed ClearMatch URL and show the title and reporting period.
2. Point out the two source datasets. Explain that the sample records are synthetic.
3. Click **Run reconciliation**.
4. Show the platform total, bank total, gross difference, and matched count.
5. Filter exceptions and point out:
   - TXN1009 settled on November 1, after the October reporting cutoff.
   - TXN1006 and TXN1010–TXN1012 have small per-row amount variances.
   - TXN1001 has a repeated bank settlement row.
   - REFUND-ORPHAN-77 has no platform-side original.
6. Download the reconciliation report CSV.
7. End by explaining that the system separates timing differences from genuine exceptions.

Do not record real customer or bank data. Show the actual running application and actual deployed URL.
