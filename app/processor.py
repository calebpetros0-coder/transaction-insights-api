# app/processor.py
# ─────────────────────────────────────────────────────────────────────────────
# All analysis logic lives here.  Each function receives a clean list of
# transaction dicts (already validated by utils.validate_rows) and returns a
# plain Python dict that route handlers can hand straight to Pydantic.
#
# Libraries used (all built-in — no third-party packages needed):
#   collections  – defaultdict makes grouping rows by key easy and readable
#   statistics   – mean() gives us a one-liner average (handles edge cases)
# ─────────────────────────────────────────────────────────────────────────────

from collections import defaultdict
from statistics import mean

from app.utils import format_currency, pct_change_label


# ── Shared helper ─────────────────────────────────────────────────────────────

def _row_month(row: dict) -> str:
    """
    Extract a 'YYYY-MM' string from a row's datetime date field.

    We use this string as a dict key whenever we need to group or sort
    transactions by month.  String comparison works correctly for ISO
    year-month strings ('2024-02' < '2024-03'), so no special sorting
    logic is needed.

    Example:
        row["date"] = datetime(2024, 3, 15)
        _row_month(row) → "2024-03"
    """
    return row["date"].strftime("%Y-%m")


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY  →  GET /api/v1/summary
# ─────────────────────────────────────────────────────────────────────────────

def get_summary(transactions: list[dict]) -> dict:
    """
    Compute high-level statistics across all transactions.

    Returns a dict with:
        total_transactions  – number of valid rows loaded
        total_spending      – sum of all amounts, rounded to 2 dp
        average_transaction – mean amount per transaction, rounded to 2 dp
        largest_transaction – the single most expensive row as a plain dict
        monthly_spending    – {"YYYY-MM": total} ordered chronologically
    """

    amounts = [row["amount"] for row in transactions]

    # ── Total & average ───────────────────────────────────────────────────────
    total_spending      = round(sum(amounts), 2)
    average_transaction = round(mean(amounts), 2)   # statistics.mean

    # ── Largest transaction ───────────────────────────────────────────────────
    # max() with a key function scans the list once and returns the whole row.
    largest_row = max(transactions, key=lambda row: row["amount"])

    # Convert datetime back to a plain string so it serialises cleanly to JSON.
    largest_transaction = {
        "date":        largest_row["date"].strftime("%Y-%m-%d"),
        "description": largest_row["description"],
        "amount":      largest_row["amount"],
        "category":    largest_row["category"],
    }

    # ── Monthly spending totals ───────────────────────────────────────────────
    # defaultdict(float) means monthly_sums["2024-01"] starts at 0.0
    # automatically — no need to check "if key in dict" before adding.
    monthly_sums: dict[str, float] = defaultdict(float)
    for row in transactions:
        monthly_sums[_row_month(row)] += row["amount"]

    # Round each month's total and sort the dict by key (YYYY-MM sorts
    # lexicographically, which is the same as chronological order).
    monthly_spending = {
        month: round(total, 2)
        for month, total in sorted(monthly_sums.items())
    }

    return {
        "total_transactions":  len(transactions),
        "total_spending":      total_spending,
        "average_transaction": average_transaction,
        "largest_transaction": largest_transaction,
        "monthly_spending":    monthly_spending,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIES  →  GET /api/v1/categories
# ─────────────────────────────────────────────────────────────────────────────

def get_categories(transactions: list[dict]) -> dict:
    """
    Break spending down by category.

    Returns a dict with:
        spending_by_category          – {category: total_amount}
        transaction_count_by_category – {category: number_of_transactions}
        top_category                  – name of the highest-spend category
    """

    # Two accumulators: one for total money spent, one for row count.
    spending_sums: dict[str, float] = defaultdict(float)
    tx_counts:     dict[str, int]   = defaultdict(int)

    for row in transactions:
        cat = row["category"]
        spending_sums[cat] += row["amount"]
        tx_counts[cat]     += 1

    # Round every category total to 2 decimal places.
    spending_by_category = {
        cat: round(total, 2)
        for cat, total in spending_sums.items()
    }

    # max() with key=... scans the dict values once and returns the key
    # (category name) whose value (total spend) is the highest.
    top_category = max(spending_by_category, key=spending_by_category.get)

    return {
        "spending_by_category":           spending_by_category,
        "transaction_count_by_category":  dict(tx_counts),
        "top_category":                   top_category,
    }


# ─────────────────────────────────────────────────────────────────────────────
# INSIGHTS  →  GET /api/v1/insights
# ─────────────────────────────────────────────────────────────────────────────

def get_insights(transactions: list[dict]) -> dict:
    """
    Generate a list of plain-English insights about the transaction data.

    Each insight is a dict with:
        title       – short label shown to the user
        description – 1-2 sentence plain-English explanation
        value       – optional formatted number or string (can be None)

    Insights produced:
        1. Top spending category
        2. Recurring subscriptions (merchants appearing in 2+ months)
        3. Month-over-month spend change (last two complete months)
        4. Average daily spend
        5. Most frequently visited merchant
    """
    insights = []

    # ── Insight 1: Top spending category ─────────────────────────────────────
    # Reuse the same grouping logic from get_categories().
    spending_sums: dict[str, float] = defaultdict(float)
    for row in transactions:
        spending_sums[row["category"]] += row["amount"]

    top_cat       = max(spending_sums, key=spending_sums.get)
    top_cat_total = spending_sums[top_cat]

    insights.append({
        "title": "Top Spending Category",
        "description": (
            f"You spent the most on '{top_cat}'. "
            "Consider reviewing this category if you're looking to cut costs."
        ),
        "value": format_currency(top_cat_total),
    })

    # ── Insight 2: Recurring subscriptions ───────────────────────────────────
    # For each merchant we collect the set of months they appear in.
    # A set automatically de-duplicates, so buying Netflix twice in January
    # still counts as one month.  Merchants in 2+ distinct months are flagged.
    #
    #   merchant_months = {
    #       "Netflix":  {"2024-01", "2024-02", "2024-03"},
    #       "Chipotle": {"2024-01", "2024-03"},
    #       ...
    #   }
    merchant_months: dict[str, set] = defaultdict(set)
    for row in transactions:
        merchant_months[row["description"]].add(_row_month(row))

    recurring = [
        merchant
        for merchant, months in merchant_months.items()
        if len(months) >= 2
    ]

    if recurring:
        recurring_str = ", ".join(sorted(recurring))
        insights.append({
            "title": "Recurring Subscriptions Detected",
            "description": (
                f"These transactions appear every month: {recurring_str}. "
                "Make sure you still use all of them."
            ),
            "value": f"{len(recurring)} subscription(s)",
        })
    else:
        insights.append({
            "title": "No Recurring Subscriptions Found",
            "description": "No merchants appeared in more than one month.",
            "value": None,
        })

    # ── Insight 3: Month-over-month spending change ───────────────────────────
    # Build an ordered list of (month_str, total) pairs so we can grab the
    # last two entries regardless of how many months are in the data.
    monthly_sums: dict[str, float] = defaultdict(float)
    for row in transactions:
        monthly_sums[_row_month(row)] += row["amount"]

    # sorted() on the dict produces keys in ascending YYYY-MM order.
    ordered_months = sorted(monthly_sums.keys())

    if len(ordered_months) >= 2:
        prev_month = ordered_months[-2]
        last_month = ordered_months[-1]
        prev_total = monthly_sums[prev_month]
        last_total = monthly_sums[last_month]
        change_label = pct_change_label(prev_total, last_total)

        insights.append({
            "title": "Month-over-Month Change",
            "description": (
                f"Spending in {last_month} was {change_label} compared to {prev_month}. "
                f"You spent {format_currency(last_total)} vs "
                f"{format_currency(prev_total)} the month before."
            ),
            "value": change_label,
        })
    else:
        insights.append({
            "title": "Month-over-Month Change",
            "description": "Not enough monthly data to compare trends yet.",
            "value": None,
        })

    # ── Insight 4: Average daily spend ───────────────────────────────────────
    # Collect unique calendar dates (as date objects, not datetimes) so that
    # two transactions on the same day still count as one active day.
    unique_days = len({row["date"].date() for row in transactions})
    total       = sum(row["amount"] for row in transactions)
    avg_daily   = round(total / unique_days, 2) if unique_days else 0.0

    insights.append({
        "title": "Average Daily Spend",
        "description": (
            f"Across {unique_days} active day(s) you averaged "
            f"{format_currency(avg_daily)} per day."
        ),
        "value": format_currency(avg_daily),
    })

    # ── Insight 5: Most frequent merchant ────────────────────────────────────
    # Count how many times each merchant (description) appears in the data.
    merchant_counts: dict[str, int] = defaultdict(int)
    for row in transactions:
        merchant_counts[row["description"]] += 1

    top_merchant        = max(merchant_counts, key=merchant_counts.get)
    top_merchant_visits = merchant_counts[top_merchant]

    insights.append({
        "title": "Most Frequent Merchant",
        "description": (
            f"'{top_merchant}' appears {top_merchant_visits} time(s) — "
            "your most-visited merchant."
        ),
        "value": f"{top_merchant_visits} transaction(s)",
    })

    return {"insights": insights}
