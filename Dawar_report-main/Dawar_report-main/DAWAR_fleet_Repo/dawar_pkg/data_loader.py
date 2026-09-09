import os
from datetime import datetime

USE_MOCK  = True   
API_BASE  = os.getenv("FLEET_API_URL",   "http://localhost:8000/api")
API_TOKEN = os.getenv("FLEET_API_TOKEN", "")


def load_payload(period: str = None):
    if period is None:
        period = os.getenv("FLEET_PERIOD", datetime.today().strftime("%Y-%m"))
    return _load_mock() if USE_MOCK else _load_from_api(period)


def _load_mock():
    from mock_data import build_mock_payload
    return build_mock_payload()


def build_payload_from_dict(data: dict):
    """Build a FleetReportPayload from a single JSON object that already contains
    all six parts. Used both by the push-style API route (data arrives in the
    request body) and by the pull-style backend loader below.

    Expected top-level keys: metadata, vehicles, fuel, maintenance, trips,
    cost_summary. Field names inside each part must match the data contracts
    exactly (the dataclasses are built with **unpacking)."""
    from data_contracts import (
        ReportMetadata, Vehicle, FuelRecord, MaintenanceRecord,
        TripRecord, CostSummary, FleetReportPayload
    )

    required = ("metadata", "vehicles", "fuel", "maintenance", "trips", "cost_summary")
    missing  = [k for k in required if k not in data]
    if missing:
        raise KeyError(f"Missing top-level key(s): {', '.join(missing)}")

    return FleetReportPayload(
        metadata     = ReportMetadata(**data["metadata"]),
        vehicles     = [Vehicle(**v)           for v in data["vehicles"]],
        fuel         = [FuelRecord(**f)        for f in data["fuel"]],
        maintenance  = [MaintenanceRecord(**m) for m in data["maintenance"]],
        trips        = [TripRecord(**t)        for t in data["trips"]],
        cost_summary = CostSummary(**data["cost_summary"]),
    )


def _load_from_api(period: str):
    import requests

    h = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}
    p = {"period": period}

    def get(path, params=None):
        r = requests.get(f"{API_BASE}{path}", headers=h,
                         params=params or p, timeout=30)
        r.raise_for_status()
        return r.json()

    return build_payload_from_dict({
        "metadata":     get("/report-config", {}),
        "vehicles":     get("/vehicles"),
        "fuel":         get("/fuel"),
        "maintenance":  get("/maintenance"),
        "trips":        get("/trips"),
        "cost_summary": get("/cost-summary"),
    })
