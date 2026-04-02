# Transaction Insights API

A backend REST API built with Python and FastAPI that processes transaction data and turns it into useful insights.

The system reads transaction records from a CSV file, validates the data, calculates key metrics, and exposes everything through simple API endpoints.

The goal of this project was to move beyond small scripts and build something that behaves more like a real backend service, with clear separation between routing, data processing, and validation.

---

## Key Features

- REST API with clearly defined endpoints  
- CSV data loading and validation  
- Spending breakdown by category and over time  
- Modular backend structure (routes, processing, utilities)  
- Interactive API docs generated with FastAPI  

---

## Project Structure

```
transaction-insights-api/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── processor.py
│   └── utils.py
├── data/
│   └── transactions.csv
├── requirements.txt
└── README.md

---

Scope & Design Choices

This project is focused on building a clean backend API and understanding how data flows through a system.

To keep things simple, I didn’t include a database, authentication, or deployment in this version. I wanted to first get comfortable structuring the API and handling data properly before adding more complexity.

These are things I’d build on next.

Running the Project

Install dependencies:

pip install -r requirements.txt

Run the server:

uvicorn app.main:app --reload

Then open:

http://127.0.0.1:8000/docs
