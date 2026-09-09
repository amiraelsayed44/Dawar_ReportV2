import io
import os
import sys
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(__file__))
from data_loader import load_payload, build_payload_from_dict
from pdf_builder import build_pdf

app = FastAPI(
    title="DAWAR Fleet Report API",
    description="POST the fleet data, get the PDF report back.",
    version="2.0.0",
)

# Backend handles auth; CORS kept open here (tighten to the app domain if this
# route is ever exposed directly to browsers).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.post("/generate-report")
def generate_report(payload: Optional[dict] = Body(default=None)):
    """
    Build the fleet PDF report.

    Body (application/json) — the full report data:
        {
          "metadata":     { ... },
          "vehicles":     [ ... ],
          "fuel":         [ ... ],
          "maintenance":  [ ... ],
          "trips":        [ ... ],
          "cost_summary": { ... }
        }

    Send no body to generate a report from the built-in mock data instead
    (handy for local testing before the backend is connected).

    Returns: the PDF file (application/pdf).
    """
    try:
        # 1. Data: from the request body if provided, else mock.
        report = build_payload_from_dict(payload) if payload else load_payload()

        # 2. Build the PDF into memory (no disk write).
        buf = io.BytesIO()
        build_pdf(report, buf)
        buf.seek(0)

        # 3. Stream the file back.
        period   = report.metadata.period
        filename = f"DAWAR_Fleet_Report_{period}.pdf"
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Report-Period":     period,
                "X-Fleet-Name":        report.metadata.fleet_name,
            },
        )

    except (KeyError, TypeError, ValueError) as e:
        # Bad / incomplete payload — surface a clear 422 instead of a 500.
        raise HTTPException(status_code=422, detail=f"Invalid report data: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"DAWAR Report Server → http://localhost:{port}")
    print(f"  Docs              → http://localhost:{port}/docs")
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
