# app/routes.py
# ─────────────────────────────────────────────────────────────────────────────
# FastAPI router containing all three API endpoints.
# Each route:
#   1. Loads + validates the CSV via utils helpers
#   2. Delegates computation to processor functions
#   3. Returns a typed Pydantic response model (auto-serialised to JSON)
#
# Keeping routes thin like this makes them easy to read and swap out later
# (e.g. replacing CSV with a database only requires changing this file).
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException

from app import processor
from app.models import SummaryResponse, CategoryResponse, InsightsResponse
from app.utils import load_csv, validate_rows   # ← validate_rows replaces validate_dataframe

# APIRouter lets us group related endpoints and mount them on main.py.
router = APIRouter()


def _load_clean_data() -> list[dict]:
    """
    Private helper used by every route.
    Loads the CSV and validates it, returning a clean list of transaction dicts.
    Raises HTTP 500 with a descriptive message if anything goes wrong.
    """
    try:
        raw_rows    = load_csv()
        transactions = validate_rows(raw_rows)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # An empty list means every row failed validation — surface that clearly.
    if not transactions:
        raise HTTPException(
            status_code=500,
            detail="No valid transactions found after validation. Check your CSV file."
        )

    return transactions


# ─────────────────────────────────────────────────────────────────────────────
# GET /summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Overall spending summary",
    description=(
        "Returns high-level statistics: total spending, average transaction, "
        "the largest single purchase, and a month-by-month spending breakdown."
    ),
)
def get_summary():
    transactions = _load_clean_data()
    return processor.get_summary(transactions)


# ─────────────────────────────────────────────────────────────────────────────
# GET /categories
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/categories",
    response_model=CategoryResponse,
    summary="Spending broken down by category",
    description=(
        "Returns total spend and transaction count per category, "
        "plus the single top-spending category."
    ),
)
def get_categories():
    transactions = _load_clean_data()
    return processor.get_categories(transactions)


# ─────────────────────────────────────────────────────────────────────────────
# GET /insights
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/insights",
    response_model=InsightsResponse,
    summary="Actionable spending insights",
    description=(
        "Returns a list of plain-English insights: top spending category, "
        "recurring subscriptions, month-over-month change, average daily spend, "
        "and most frequent merchant."
    ),
)
def get_insights():
    transactions = _load_clean_data()
    return processor.get_insights(transactions)
