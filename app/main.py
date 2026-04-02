# app/main.py
# ─────────────────────────────────────────────────────────────────────────────
# Application entry point.  Creates the FastAPI app, configures metadata
# (used by the auto-generated /docs page), and mounts the router.
#
# To run the server:
#   uvicorn app.main:app --reload
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from app.routes import router

# ── Create the FastAPI application instance ───────────────────────────────────
# The metadata below populates the interactive Swagger UI at /docs.
app = FastAPI(
    title="Transaction Insights API",
    description=(
        "A beginner-friendly REST API that reads personal transaction data from "
        "a CSV file, validates it with built-in Python libraries, and exposes spending summaries, "
        "category breakdowns, and plain-English financial insights."
    ),
    version="1.0.0",
)

# ── Register all routes defined in routes.py ─────────────────────────────────
# Prefix every endpoint with /api/v1 so the URLs are:
#   /api/v1/summary
#   /api/v1/categories
#   /api/v1/insights
app.include_router(router, prefix="/api/v1")


# ── Root endpoint – sanity check / welcome message ────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """
    Simple health-check endpoint.
    Visit http://127.0.0.1:8000/docs for the interactive API explorer.
    """
    return {
        "message": "Welcome to the Transaction Insights API!",
        "docs": "/docs",
        "endpoints": [
            "/api/v1/summary",
            "/api/v1/categories",
            "/api/v1/insights",
        ],
    }
