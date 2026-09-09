import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from data_loader import load_payload
from pdf_builder import build_pdf

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", default=None)
    ap.add_argument("--output", default="DAWAR_Fleet_Report.pdf")
    a = ap.parse_args()
    payload = load_payload(period=a.period)
    print(f"Fleet: {payload.metadata.fleet_name}  |  {payload.metadata.report_month}")
    build_pdf(payload, a.output)
