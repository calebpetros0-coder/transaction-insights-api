# app/utils.py
# ─────────────────────────────────────────────────────────────────────────────
# Small, focused helper functions that don't belong in the main processor.
# Keeping them here makes processor.py easier to read and test in isolation.
#
# Libraries used (all built-in — no third-party packages needed):
#   csv       – reads CSV files row by row into plain Python dicts
#   datetime  – parses and validates date strings
#   pathlib   – cross-platform file path handling
# ─────────────────────────────────────────────────────────────────────────────

import csv
from datetime import datetime
from pathlib import Path


# Path to the CSV file, relative to the project root.
# Path(__file__) resolves to this file; .parent steps up one directory at a time.
CSV_PATH = Path(__file__).parent.parent / "data" / "transactions.csv"

# The exact column names we expect in the CSV header row.
REQUIRED_COLUMNS = {"date", "description", "amount", "category"}

# Date format we accept in the CSV.  "2024-01-15" matches "%Y-%m-%d".
DATE_FORMAT = "%Y-%m-%d"


def load_csv(path: Path = CSV_PATH) -> list[dict]:
    """
    Read the transactions CSV from disk using the built-in csv module.

    csv.DictReader turns each data row into a plain Python dict whose keys
    are taken from the header line of the file.  For example, the row:

        2024-01-05,Netflix,15.99,Subscriptions

    becomes:
        {"date": "2024-01-05", "description": "Netflix",
         "amount": "15.99", "category": "Subscriptions"}

    All values are strings at this stage — validate_rows() handles parsing.

    Returns a list of raw dicts (one per CSV row) before any validation.
    Raises FileNotFoundError early so the caller gets a clear error message
    instead of a confusing crash deep in the csv module.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Transaction file not found at '{path}'. "
            "Make sure data/transactions.csv exists."
        )

    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # reader.fieldnames is populated as soon as the file is opened.
        # If the file is completely empty it will be None.
        if not reader.fieldnames:
            raise ValueError("CSV file appears to be empty.")

        # Verify that every expected column is present in the header.
        file_columns  = set(reader.fieldnames)
        missing_cols  = REQUIRED_COLUMNS - file_columns
        if missing_cols:
            raise ValueError(
                f"CSV is missing required column(s): {missing_cols}. "
                f"Expected columns: {REQUIRED_COLUMNS}"
            )

        for row in reader:
            rows.append(row)

    return rows


def validate_rows(raw_rows: list[dict]) -> list[dict]:
    """
    Validate and clean a list of raw CSV row dicts.

    Each row goes through four checks in order:

      1. Blank-field check  – skip rows where any of the four key fields is
                              empty or whitespace-only.
      2. Date validation    – parse the date string with strptime; skip rows
                              whose date doesn't match DATE_FORMAT.
      3. Amount validation  – convert amount to float; skip rows where that
                              fails (e.g. the value is "abc" or "$15").
      4. String cleanup     – strip leading/trailing whitespace from
                              description and category.

    Returns a new list of dicts that passed every check.  The 'date' value
    in each returned dict is a datetime object (not a string) so processor.py
    can do date arithmetic (e.g. extract year-month) without re-parsing.
    """
    clean          = []
    dropped_blank  = 0
    dropped_date   = 0
    dropped_amount = 0

    for row in raw_rows:

        # ── 1. Blank-field check ──────────────────────────────────────────────
        # row.get() returns None if a key is absent; "or ''" converts None to
        # an empty string so .strip() never raises an AttributeError.
        date_str    = (row.get("date")        or "").strip()
        description = (row.get("description") or "").strip()
        amount_str  = (row.get("amount")      or "").strip()
        category    = (row.get("category")    or "").strip()

        if not all([date_str, description, amount_str, category]):
            dropped_blank += 1
            continue            # skip this row entirely

        # ── 2. Date validation ────────────────────────────────────────────────
        # strptime raises ValueError when the string doesn't match the format,
        # so we catch that and skip the row rather than crashing the whole app.
        try:
            parsed_date = datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            dropped_date += 1
            continue

        # ── 3. Amount validation ──────────────────────────────────────────────
        # float() raises ValueError for non-numeric strings like "abc" or "--".
        try:
            parsed_amount = float(amount_str)
        except ValueError:
            dropped_amount += 1
            continue

        # ── 4. Assemble the clean row ─────────────────────────────────────────
        # Store parsed types so processor.py never has to convert again.
        clean.append({
            "date":        parsed_date,   # datetime  ← was a string
            "description": description,   # str, whitespace stripped
            "amount":      parsed_amount, # float     ← was a string
            "category":    category,      # str, whitespace stripped
        })

    # Log a summary so developers can spot data problems quickly.
    if dropped_blank:
        print(f"[validate] Dropped {dropped_blank} row(s) with missing values.")
    if dropped_date:
        print(f"[validate] Dropped {dropped_date} row(s) with invalid dates.")
    if dropped_amount:
        print(f"[validate] Dropped {dropped_amount} row(s) with invalid amounts.")

    print(f"[validate] Loaded {len(clean)} valid transaction(s).")
    return clean


def format_currency(value: float) -> str:
    """Return a value formatted as a USD currency string.

    Example:  format_currency(1234.5) → '$1,234.50'
    """
    return f"${value:,.2f}"


def pct_change_label(old: float, new: float) -> str:
    """Return a human-readable percentage-change string.

    Examples:
        pct_change_label(100, 120) → '+20.0%'
        pct_change_label(100,  80) → '-20.0%'
        pct_change_label(0,    50) → 'N/A (no prior data)'
    """
    if old == 0:
        return "N/A (no prior data)"
    change = ((new - old) / old) * 100
    sign   = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"
