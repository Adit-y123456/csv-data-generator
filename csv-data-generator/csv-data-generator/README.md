# Financial CSV Data Generator

A reconstruction of the synthetic financial data generator for the Money Talks hackathon's Audit-Ready Agent project.

It creates transaction-level records and monthly account summaries, including a visible AWS cloud-spending anomaly. All data is synthetic and for demos/testing only.

## Run

Install Python 3 and open this folder in VS Code. In Terminal, run:

```bash
python generate_csv.py
```

On Windows, `py generate_csv.py` also works if Python is installed with the launcher.

CSV files appear in the `output` folder.

## Files

- `monthly_account_summaries.csv`: account_id, account_name, month, amount
- `transaction_details.csv`: transaction_id, date, account_id, account_name, vendor_name, category, amount, user_department, anomaly_flag, description
- `summary_monthly.csv`: compatibility copy of the monthly account summaries
- `transactions_raw.csv`: transaction_id, date, account_id, vendor_name, amount, user_department, anomaly_flag
- `variance_comparison.csv`: account_id, account_name, prior_amount, current_amount, comparing the final two months

There are 500 transactions by default, spanning March through August 2026. Two large AWS transactions are flagged in May to produce a clear account-level variance. Other account expenses follow a rising-then-falling trend. Month/account totals are calculated directly from transactions, so the two files reconcile exactly.

## Options

```bash
python generate_csv.py --rows 1000 --seed 10
python generate_csv.py --spike-month 2026-08
python generate_csv.py --output my_csv_files
```

Changing the `--seed` changes the transaction amounts and vendors. With the same seed and settings, the generated data is reproducible.

## Notes

This is newly reconstructed code based on old project specifications; it is not the deleted original source. The transactions are fictional. Do not describe them as real receipts or accounting records.
