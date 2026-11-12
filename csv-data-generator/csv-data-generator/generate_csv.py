import argparse
import csv
import calendar
import random
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ACCOUNTS = [
    ("6100", "Cloud Infrastructure", "Engineering", ["Amazon Web Services", "Microsoft Azure", "Google Cloud"]),
    ("6200", "Software Subscriptions", "Product", ["GitHub", "Atlassian", "Figma", "Notion"]),
    ("6300", "Marketing", "Marketing", ["Google Ads", "Meta Ads", "HubSpot"]),
    ("6400", "Travel and Entertainment", "Operations", ["Delta Air Lines", "Marriott", "Uber"]),
    ("6500", "Professional Services", "Finance", ["Deloitte", "Legal Counsel", "Contractor Services"]),
]

BASE_AMOUNTS = {
    "6100": (550, 1100),
    "6200": (150, 700),
    "6300": (250, 900),
    "6400": (100, 500),
    "6500": (300, 850),
}

TREND = [1.00, 1.12, 1.15, 1.05, 1.00, 0.96]


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def months_from(start, count):
    year, month = map(int, start.split("-"))
    if not 1 <= month <= 12:
        raise ValueError("Month must be between 01 and 12")
    if count < 1:
        raise ValueError("At least one month is required")
    return [f"{year + (month - 1 + i) // 12:04d}-{(month - 1 + i) % 12 + 1:02d}" for i in range(count)]


def save_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate(rows, seed, start, month_count, spike_month, output):
    rng = random.Random(seed)
    months = months_from(start, month_count)
    if rows < month_count * len(ACCOUNTS):
        raise ValueError(f"At least {month_count * len(ACCOUNTS)} rows are needed for all month/account combinations")
    if spike_month not in months:
        raise ValueError(f"Spike month {spike_month} is not in {months[0]} through {months[-1]}")
    groups = [(month, account) for month in months for account in ACCOUNTS]
    assignments = [groups[i % len(groups)] for i in range(rows)]
    rng.shuffle(assignments)
    spike_count = 0
    details = []

    for index, (month, account) in enumerate(assignments):
        account_id, account_name, department, vendors = account
        month_index = months.index(month)
        year, month_number = map(int, month.split("-"))
        day = rng.randint(1, calendar.monthrange(year, month_number)[1])
        lower, upper = BASE_AMOUNTS[account_id]
        factor = TREND[min(month_index, len(TREND) - 1)]
        amount = money(rng.uniform(lower, upper) * factor)
        vendor = rng.choice(vendors)
        anomaly = 0
        description = "Regular operating expense"

        if month == spike_month and account_id == "6100" and spike_count < 2:
            vendor = "Amazon Web Services"
            amount = money([18000, 12000][spike_count])
            description = ["Enterprise capacity upgrade", "Unplanned infrastructure expansion"][spike_count]
            anomaly = 1
            spike_count += 1

        details.append({
            "transaction_id": f"TXN-{10000 + index}",
            "date": str(date(year, month_number, day)),
            "account_id": account_id,
            "account_name": account_name,
            "vendor_name": vendor,
            "category": account_name,
            "amount": f"{amount:.2f}",
            "user_department": department,
            "anomaly_flag": anomaly,
            "description": description,
        })

    details.sort(key=lambda row: (row["date"], row["transaction_id"]))
    sums = defaultdict(lambda: Decimal("0.00"))
    for transaction in details:
        sums[(transaction["date"][:7], transaction["account_id"])] += Decimal(transaction["amount"])

    summaries = []
    for month in months:
        for account_id, account_name, _, _ in ACCOUNTS:
            amount = sums[(month, account_id)]
            summaries.append({
                "account_id": account_id,
                "account_name": account_name,
                "month": month,
                "amount": f"{amount:.2f}",
            })

    raw = [
        {field: transaction[field] for field in [
            "transaction_id", "date", "account_id", "vendor_name",
            "amount", "user_department", "anomaly_flag",
        ]}
        for transaction in details
    ]

    comparisons = []
    if len(months) >= 2:
        before, after = months[-2], months[-1]
        for account_id, account_name, _, _ in ACCOUNTS:
            comparisons.append({
                "account_id": account_id,
                "account_name": account_name,
                "prior_amount": f"{sums[(before, account_id)]:.2f}",
                "current_amount": f"{sums[(after, account_id)]:.2f}",
            })

    output.mkdir(parents=True, exist_ok=True)
    save_csv(output / "monthly_account_summaries.csv", ["account_id", "account_name", "month", "amount"], summaries)
    save_csv(output / "transaction_details.csv", [
        "transaction_id", "date", "account_id", "account_name", "vendor_name", "category",
        "amount", "user_department", "anomaly_flag", "description",
    ], details)
    save_csv(output / "summary_monthly.csv", ["account_id", "account_name", "month", "amount"], summaries)
    save_csv(output / "transactions_raw.csv", [
        "transaction_id", "date", "account_id", "vendor_name", "amount", "user_department", "anomaly_flag",
    ], raw)
    if comparisons:
        save_csv(output / "variance_comparison.csv", ["account_id", "account_name", "prior_amount", "current_amount"], comparisons)

    reconstructed = sum(Decimal(row["amount"]) for row in details)
    summarized = sum(Decimal(row["amount"]) for row in summaries)
    if reconstructed != summarized:
        raise ArithmeticError("Summary amounts do not match transactions")

    print(f"Created {len(details)} transactions and {len(summaries)} monthly account totals")
    print(f"Month range: {months[0]} through {months[-1]}")
    print(f"AWS anomaly month: {spike_month} with {spike_count} flagged transactions")
    print(f"Summary reconciled: ${summarized:,.2f}")
    print(f"CSV files saved to: {output.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic financial CSV data")
    parser.add_argument("--rows", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start", default="2026-03")
    parser.add_argument("--months", type=int, default=6)
    parser.add_argument("--spike-month", default="2026-05")
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    generate(args.rows, args.seed, args.start, args.months, args.spike_month, args.output)


if __name__ == "__main__":
    main()
