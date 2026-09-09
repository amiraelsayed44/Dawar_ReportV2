# DAWAR Fleet Report Engine

Generates a 6-page A4 PDF fleet report from one month of fleet data.
Built with ReportLab, matplotlib, and FastAPI.

## Requirements

- Python 3.10+
- Install dependencies:

```bash
pip install -r dawar_pkg/requirements.txt
```

## Run as an API (recommended)

```bash
python dawar_pkg/api_server.py        # serves on PORT (default 8080)
```

Interactive docs: `http://localhost:8080/docs`

### Single route

```
POST /generate-report
Content-Type: application/json
```

- **Body:** one JSON object with all the data — keys:
  `metadata`, `vehicles`, `fuel`, `maintenance`, `trips`, `cost_summary`.
  (See `DAWAR_Report_API_Contract.md` for the exact field shapes and rules.)
- **Response:** the PDF file (`application/pdf`).
- **No auth token** — authentication is handled upstream by the backend.

Send **no body** to generate a report from the built-in mock data
(useful for local testing before the backend is connected):

```bash
curl -X POST http://localhost:8080/generate-report -o report.pdf
```

Health check: `GET /health`

## Run from the command line (mock data)

```bash
python dawar_pkg/main.py --period 2026-04 --output report.pdf
```

## Connect to a live backend (later)

Data currently comes from the request body (or mock). If you ever want the
engine to *pull* data from backend endpoints instead, set `USE_MOCK = False`
in `dawar_pkg/data_loader.py` and point `FLEET_API_URL` / `FLEET_API_TOKEN`
at the backend.

## Structure

```
dawar_pkg/
├── api_server.py      # FastAPI app — single /generate-report route
├── main.py            # CLI entry point
├── data_loader.py     # Builds the payload (from body / mock / live API)
├── data_contracts.py  # Input schema (dataclasses)
├── mock_data.py       # Sample data for local testing
├── calculations.py    # KPIs + health-score engine
├── charts.py          # matplotlib charts
├── pdf_builder.py     # PDF assembly
├── config.py          # Colour palette
├── requirements.txt
└── logo_final.png
```
