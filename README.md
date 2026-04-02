# Transaction Insights API

A backend REST API built with Python and FastAPI that processes structured transaction data and generates financial insights.

The system reads transaction records from a CSV file, validates each entry, computes key statistics, and exposes the results through clean API endpoints.

This project focuses on building a service-style backend with clear separation between data processing, validation, and API layers.

---

## Key Features

- REST API design with structured endpoints  
- CSV data ingestion and validation  
- Category-based aggregation and trend analysis  
- Modular backend architecture (routes, processing, validation)  
- Auto-generated API documentation via FastAPI  

---

## Project Structure

transaction-insights-api/
├── app/
│ ├── main.py
│ ├── models.py
│ ├── routes.py
│ ├── processor.py
│ └── utils.py
├── data/
│ └── transactions.csv
├── requirements.txt
└── README.md

---

## Scope & Design Choices

This project is focused on building a clean backend API and working through data processing step by step.

To keep things simple and intentional, I didn’t include things like a database, authentication, or deployment in this version. The goal was to first understand how the API layer and data logic fit together.

These are things I’d build on next as I continue developing the project.

---

## Running the Project

Install dependencies:

```bash
pip install -r requirements.txt