# app/models.py
# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models define the shape of data coming in and going out of the API.
# FastAPI uses these automatically for validation and JSON serialisation.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Dict, List, Optional


# ── A single transaction row after it has been cleaned and validated ──────────
class Transaction(BaseModel):
    date: str           # ISO date string  e.g. "2024-01-15"
    description: str    # Human-readable merchant / payee name
    amount: float       # Positive number representing money spent
    category: str       # High-level bucket e.g. "Groceries"


# ── Response model for GET /summary ──────────────────────────────────────────
class SummaryResponse(BaseModel):
    total_transactions: int         # How many valid rows were loaded
    total_spending: float           # Sum of all amounts
    average_transaction: float      # Mean amount per transaction
    largest_transaction: dict       # The single biggest spend (full row)
    monthly_spending: Dict[str, float]  # {"2024-01": 450.23, ...}


# ── Response model for GET /categories ───────────────────────────────────────
class CategoryResponse(BaseModel):
    spending_by_category: Dict[str, float]      # {"Groceries": 259.72, ...}
    transaction_count_by_category: Dict[str, int]  # {"Groceries": 6, ...}
    top_category: str                            # Category with highest spend


# ── A single insight item returned by GET /insights ──────────────────────────
class Insight(BaseModel):
    title: str          # Short label shown to the user
    description: str    # Plain-English explanation of the finding
    value: Optional[str] = None  # Optional formatted value (e.g. "$45.23")


# ── Response model for GET /insights ─────────────────────────────────────────
class InsightsResponse(BaseModel):
    insights: List[Insight]
