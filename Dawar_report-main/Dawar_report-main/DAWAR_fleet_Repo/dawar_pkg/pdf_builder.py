import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import CLR
from data_contracts import FleetReportPayload
from calculations import calc_executive, calc_fuel, calc_maintenance, calc_trips, calc_tco_breakdown
import charts as ch

LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo_final.png")

# ── Fonts ─────────────────────────────────────────────────────────────────────
for _name, _path in [("DV",  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                      ("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
    if os.path.exists(_path):
        pdfmetrics.registerFont(TTFont(_name, _path))
FN = "DV"  if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") else "Helvetica"
FB = "DVB" if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") else "Helvetica-Bold"

W, H = A4
ML, MR, MT, MB = 1.5*cm, 1.5*cm, 1.8*cm, 1.7*cm
IW = W - ML - MR        # usable inner width ≈ 17.8 cm

C   = {k: colors.HexColor(v) for k, v in CLR.items()}
_pn = [0]


# ── Page canvas (header line + footer + logo) ─────────────────────────────────
def _on_page(canvas, doc):
    _pn[0] += 1
    canvas.saveState()
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    if _pn[0] == 1:          # cover — no header/footer chrome
        canvas.restoreState()
        return

    # ── top accent line
    canvas.setStrokeColor(C["green_mid"])
    canvas.setLineWidth(1.2)
    canvas.line(ML, H - 1.0*cm, W - MR, H - 1.0*cm)

    # ── logo top-right
    if os.path.exists(LOGO_PATH):
        canvas.setFillColor(colors.white)
        canvas.roundRect(W - 4.1*cm, H - 1.1*cm, 3.0*cm, 0.95*cm, 4, fill=1, stroke=0)
        canvas.drawImage(LOGO_PATH, W - 4.0*cm, H - 1.05*cm,
                         width=2.8*cm, height=0.85*cm,
                         preserveAspectRatio=True, mask="auto")

    # ── footer bar
    canvas.setFillColor(C["bg_header"])
    canvas.rect(0, 0, W, 1.25*cm, fill=1, stroke=0)
    canvas.setFont(FN, 7.5)
    canvas.setFillColor(colors.HexColor("#AAAAAA"))
    canvas.drawString(ML, 0.44*cm, f"{doc.fleet_name}  ·  {doc.report_month}")
    canvas.setFillColor(C["green_bright"])
    canvas.drawRightString(W - MR, 0.44*cm, f"Page {_pn[0]}")
    canvas.restoreState()


# ── Style shortcuts ────────────────────────────────────────────────────────────
def _s(name, **kw):
    base = dict(fontName=FN, fontSize=10, textColor=C["text_dark"], leading=14)
    base.update(kw)
    return ParagraphStyle(name, **base)

def _sp(h=0.3):
    return Spacer(1, h*cm)

def _section_bar(title):
    """Dark green section header bar with left accent stripe."""
    return [Table([[
        Table([[""]], colWidths=[0.32*cm],
              style=TableStyle([
                  ("BACKGROUND",(0,0),(-1,-1), C["green_bright"]),
                  ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
              ])),
        Paragraph(f'<font color="{CLR["text_on_dark"]}"><b>{title}</b></font>',
                  _s("sh", fontName=FB, fontSize=13,
                     textColor=C["text_on_dark"],
                     backColor=colors.HexColor(CLR["bg_header"]))),
    ]], colWidths=[0.5*cm, IW - 0.5*cm],
    style=TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C["bg_header"]),
        ("TOPPADDING",    (0,0),(-1,-1), 8), ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 8), ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
        ("LINEBELOW",     (0,0),(-1,-1), 3, C["green_bright"]),
    ])), _sp(0.25)]


def _kpi_card(label, value, sub="", accent=None):
    """3-row KPI card: label / big value / subtitle."""
    ac = colors.HexColor(accent) if accent else C["green_bright"]
    return Table([
        [Paragraph(f'<font size="8.5" color="{CLR["text_mid"]}"><b>{label}</b></font>',
                   _s("kl", alignment=TA_CENTER))],
        [Paragraph(f'<font size="17" color="{accent or CLR["green_bright"]}"><b>{value}</b></font>',
                   _s("kv", fontName=FB, alignment=TA_CENTER, leading=20))],
        [sub if hasattr(sub, "wrap") else
         Paragraph(f'<font size="7.5" color="{CLR["text_muted"]}">{sub}</font>',
                   _s("ks", alignment=TA_CENTER))],
    ], colWidths=["100%"],
    style=TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C["bg_card"]),
        ("TOPPADDING",    (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",   (0,0),(-1,-1), 4), ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("LINEABOVE",     (0,0),(-1,0),  2.5, ac),
        ("LINEBELOW",     (0,-1),(-1,-1), 0.5, C["border"]),
        ("LINEBEFORE",    (0,0),(0,-1),   0.5, C["border"]),
        ("LINEAFTER",     (-1,0),(-1,-1), 0.5, C["border"]),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))


def _kpi_row(cards):
    n  = len(cards)
    cw = IW / n
    return [Table([cards], colWidths=[cw]*n,
                  style=TableStyle([
                      ("LEFTPADDING",  (0,0),(-1,-1), 3),
                      ("RIGHTPADDING", (0,0),(-1,-1), 3),
                      ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
                  ])), _sp(0.28)]


def _insight(text, warn=False):
    """Highlighted insight / recommendation strip."""
    bc  = colors.HexColor(CLR["gold_light"]) if warn else C["bg_insight"]
    dot = f'<font color="{CLR["gold"] if warn else CLR["green_bright"]}">●</font>'
    return [Table([[Paragraph(
        f'{dot}  <font color="{CLR["text_mid"]}"><b>Insight</b></font>  '
        f'<font color="{CLR["text_dark"]}">{text}</font>',
        _s("ins", fontSize=8.5, leading=13))]],
        colWidths=[IW],
        style=TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), bc),
            ("LEFTPADDING",  (0,0),(-1,-1), 12),
            ("RIGHTPADDING", (0,0),(-1,-1), 12),
            ("TOPPADDING",   (0,0),(-1,-1), 8),
            ("BOTTOMPADDING",(0,0),(-1,-1), 8),
            ("LINEBEFORE",   (0,0),(0,-1),  3,
             colors.HexColor(CLR["gold"] if warn else CLR["green_primary"])),
        ])), _sp(0.28)]


def _caption(text):
    return Paragraph(
        f'<font color="{CLR["text_muted"]}" size="7.5"><i>{text}</i></font>',
        _s("cap", alignment=TA_CENTER))


def _change_arrow(pct: float) -> str:
    """Returns colored arrow + percentage string."""
    if pct > 0:
        return f'<font color="{CLR["score_poor"]}">▲ +{pct}%</font>'
    elif pct < 0:
        return f'<font color="{CLR["score_great"]}">▼ {pct}%</font>'
    return f'<font color="{CLR["text_muted"]}">— 0%</font>'


# COVER
def _cover(meta):
    story = []

    # ── Logo zone (white strip) ───────────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        from reportlab.platypus import Image as RLImg
        logo_elem = RLImg(LOGO_PATH, width=5*cm, height=1.8*cm, kind="proportional")
    else:
        logo_elem = Paragraph(
            f'<font size="9" color="{CLR["text_muted"]}">[ Logo ]</font>',
            _s("lph", alignment=TA_LEFT))

    story.append(Table([[logo_elem]], colWidths=[IW],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.white),
            ("TOPPADDING",    (0,0),(-1,-1), 16),
            ("BOTTOMPADDING", (0,0),(-1,-1), 14),
            ("LEFTPADDING",   (0,0),(-1,-1), 4),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ])))

    # ── Brand + title band ────────────────────────────────────────────────────
    story.append(Table([[
        Paragraph(
            f'<font size="46" color="{CLR["green_bright"]}"><b>DAWAR</b></font>',
            _s("brand", fontName=FB, alignment=TA_LEFT)),
        Paragraph(
            f'<font size="20" color="{CLR["text_on_dark"]}"><b>Fleet Management</b></font><br/>'
            f'<font size="12" color="{CLR["green_bright"]}">Monthly Operations Report</font>',
            _s("rtitle", fontName=FB, alignment=TA_RIGHT)),
    ]], colWidths=[IW * 0.5, IW * 0.5],
    style=TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C["bg_header"]),
        ("TOPPADDING",    (0,0),(-1,-1), 22),
        ("BOTTOMPADDING", (0,0),(-1,-1), 22),
        ("LEFTPADDING",   (0,0),(-1,-1), 20),
        ("RIGHTPADDING",  (0,0),(-1,-1), 20),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEBELOW",     (0,0),(-1,-1), 3, C["green_bright"]),
    ])))

    # ── Year + tagline (mint card) ────────────────────────────────────────────
    story.append(Table([
        [Paragraph(
            f'<font size="96" color="{CLR["green_bright"]}"><b>{datetime.today().year}</b></font>',
            _s("yr", fontName=FB, alignment=TA_LEFT, leading=100))],
        [Paragraph(
            f'<font size="10" color="{CLR["text_mid"]}">Powered by DAWAR Fleet Intelligence</font>',
            _s("yrsub", fontName=FN, alignment=TA_LEFT))],
    ], colWidths=[IW],
    style=TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C["bg_card"]),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 16),
        ("LEFTPADDING",   (0,0),(-1,-1), 22),
    ])))

    # ── Metadata strip ────────────────────────────────────────────────────────
    labels = ["Fleet Name", "Report Period", "Generated On", "Prepared By"]
    values = [meta.fleet_name, meta.report_month, meta.report_date, meta.generated_by]
    story.append(Table(
        [[Paragraph(f'<font size="7" color="{CLR["text_muted"]}">{lb}</font>',
                    _s(f"ml{i}")) for i,lb in enumerate(labels)],
         [Paragraph(f'<font size="9.5" color="{CLR["text_on_dark"]}"><b>{v}</b></font>',
                    _s(f"mv{i}", fontName=FB)) for i,v in enumerate(values)]],
        colWidths=[IW/4]*4,
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C["bg_header"]),
            ("TOPPADDING",    (0,0),(-1,-1), 9),
            ("BOTTOMPADDING", (0,0),(-1,-1), 9),
            ("LEFTPADDING",   (0,0),(-1,-1), 12),
            ("LINEABOVE",     (0,0),(-1,0),  0.4, C["border_dark"]),
            ("LINEBELOW",     (0,-1),(-1,-1),0.4, C["border_dark"]),
        ])))

    # ── Confidential bar ──────────────────────────────────────────────────────
    story.append(Table([[
        Paragraph(
            f'<font color="{CLR["bg_header"]}"><b>CONFIDENTIAL  ·  FOR FLEET MANAGEMENT USE ONLY</b></font>',
            _s("conf", fontSize=8, alignment=TA_CENTER))
    ]], colWidths=[IW],
    style=TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C["green_primary"]),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
    ])))

    story.append(PageBreak())
    return story



# EXECUTIVE SNAPSHOT

def _section_executive(payload, kpis):
    story = _section_bar("Executive Snapshot")

    cs  = payload.cost_summary
    cpm = kpis["cpm"]

    # ── ROW 1 — The 4 headline numbers ───────────────────────────────────────

    story += _kpi_row([
        _kpi_card(
            "Total Cost of Ownership",
            f"EGP {cs.total_tco_egp:,.0f}",
            f"vs last month  {kpis['tco_change_pct']:+.1f}%",
            CLR["score_poor"] if kpis["tco_change_pct"] > 0 else CLR["green_primary"],
        ),
        _kpi_card(
            "Cost Per KM  (CPM)",
            f"EGP {cpm:.2f}",
            "most important fleet KPI",
            CLR["green_primary"] if cpm < 5.0 else CLR["score_poor"],
        ),
        _kpi_card(
            "Fleet Utilization",
            f"{kpis['utilization_pct']}%",
            f"{kpis['active']} active · {kpis['idle']} idle · {kpis['in_maintenance']} in maint.",
            CLR["score_poor"] if kpis["utilization_pct"] < 65 else CLR["green_primary"],
        ),
        _kpi_card(
            "Fleet Health Index",
            f"{kpis['health_index']} / 100",
            "based on sensor readings",
            CLR["score_poor"] if kpis["health_index"] < 60
            else CLR["score_avg"]  if kpis["health_index"] < 80
            else CLR["green_primary"],
        ),
    ])

    # ── Charts Row 1: Gauge + Fleet Status donut ─────────────────────────────
    gauge = ch.chart_health_gauge(kpis["health_index"])
    donut = ch.chart_fleet_status_donut(kpis)

    story.append(Table([[gauge, donut]],
        colWidths=[IW*0.38, IW*0.62],
        style=TableStyle([
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 0),
            ("TOPPADDING",   (0,0),(-1,-1), 2),
            ("BOTTOMPADDING",(0,0),(-1,-1), 2),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ])))
    story.append(_caption(
        "Left: Fleet Health Index (sensor-based 0–100)  ·  "
        "Right: vehicle health status distribution"))
    story.append(_sp(0.25))

    # ── Charts Row 2: Utilization bar (full width) ────────────────────────────
    ubar = ch.chart_utilization_bar(kpis)
    story.append(ubar)
    story.append(_caption("Fleet utilization — Active · Idle · In Maintenance vehicle count"))
    story.append(_sp(0.2))

    # ── Expert insight ─────────────────────────────────────────────────────────
    # TCO insight
    tco_flag = kpis["tco_change_pct"] > 8
    if tco_flag:
        story += _insight(
            f"TCO rose {kpis['tco_change_pct']}% vs last month — "
            f"main driver: fuel ({round(cs.fuel_cost_egp/cs.total_tco_egp*100,1)}% of total). "
            f"Investigate top consumers before next cycle.", warn=True)
    else:
        story += _insight(
            f"TCO: EGP {cs.total_tco_egp:,.0f}  ·  "
            f"CPM: EGP {cpm:.2f}/km  ·  "
            f"Fleet efficiency: {round(cs.total_km_driven / max(sum(f.liters_consumed for f in payload.fuel),1), 2)} km/L  ·  "
            f"{kpis['broken']} broken vehicle(s) — priority: restore to service.")

    # Health insight
    offline = kpis["overdue"] + kpis["broken"] + kpis["in_maint_count"]
    if offline > 2:
        story += _insight(
            f"{offline} vehicles offline or overdue  —  "
            f"potential revenue loss: EGP "
            f"{offline * round(cs.total_tco_egp / max(len(payload.vehicles),1) * 1.2, 0):,.0f}.  "
            f"Schedule immediate inspection.", warn=True)

    story.append(PageBreak())
    return story




# FUEL

def _section_fuel(payload, fuel_kpis):
    story = _section_bar("Fuel Consumption")

    def _chg(v):
        if v is None: return "no prior data"
        s = "+" if v > 0 else ""
        return f"vs last month  {s}{v}%"

    story += _kpi_row([
        _kpi_card("Total Fuel Cost",
                  f"EGP {fuel_kpis['total_cost']:,.0f}",
                  _chg(fuel_kpis["cost_change_pct"]),
                  CLR["score_poor"] if (fuel_kpis["cost_change_pct"] or 0) > 5
                  else CLR["gold"]),
        _kpi_card("Fleet Efficiency",
                  f"{fuel_kpis['fleet_efficiency']} km/L",
                  "km driven per liter"),
        _kpi_card("Total Liters",
                  f"{fuel_kpis['total_liters']:,.0f} L",
                  _chg(fuel_kpis["liters_change_pct"]),
                  CLR["score_poor"] if (fuel_kpis["liters_change_pct"] or 0) > 5
                  else CLR["text_muted"]),
        _kpi_card("Avg Price / Liter",
                  f"EGP {fuel_kpis['avg_price_per_liter']}",
                  "current market rate"),
    ])

    # Weekly trend chart (full width)
    story.append(ch.chart_fuel_weekly_trend(fuel_kpis))
    story.append(_caption(
        "Weekly fuel consumption this month (green) vs last month (amber)  ·  "
        "% labels show week-on-week change"))
    story.append(_sp(0.3))

    # Top 5 over-consumers
    top5_chart = ch.chart_top5_fuel(fuel_kpis.get("top5", []))
    if top5_chart:
        story.append(top5_chart)
        story.append(_caption(
            "Top 5 highest-consuming vehicles — green: this month · amber: historical avg · "
            "% = change vs historical average"))
        story.append(_sp(0.2))

    # ── Expert fuel insights ─────────────────────────────────────────────────
    top5    = fuel_kpis.get("top5", [])
    price   = fuel_kpis["avg_price_per_liter"]
    eff     = fuel_kpis["fleet_efficiency"]

    # Insight 1 — top consumer vs its own history
    if top5:
        worst = top5[0]
        pct   = worst.get("vs_hist_pct")
        lbl   = worst.get("months_label", "prior data")
        if pct is not None:
            extra_egp = round(abs(worst["liters"] - (worst["hist_avg"] or worst["liters"]))
                              * price)
            story += _insight(
                f"Highest consumer this month: {worst['vehicle_id']} "
                f"({worst['liters']:,.0f} L,  {worst['km_per_liter']} km/L). "
                f"{'Up' if pct > 0 else 'Down'} {abs(pct):.1f}% vs {lbl} "
                f"— extra spend: EGP {extra_egp:,}. "
                f"Check: tyre pressure (saves 3–5%), air filter (4–6%), "
                f"driver behaviour (8–15%).",
                warn=pct > 8)
        else:
            story += _insight(
                f"Highest consumer: {worst['vehicle_id']} ({worst['liters']:,.0f} L). "
                f"No historical data yet to compare — begin tracking from next month.")

    # Insight 2 — fleet efficiency
    if eff < 4.0:
        saving = round((fuel_kpis["total_km"] / 4.0 - fuel_kpis["total_km"] / max(eff,0.1))
                       * (-price), 0) if eff > 0 else 0
        story += _insight(
            f"Fleet efficiency {eff} km/L is below 4.0 km/L target. "
            f"Reaching 4.0 km/L saves ~EGP {abs(saving):,}/month. "
            f"Priority: tyre pressure audit + eco-driving programme.",
            warn=True)

    # Insight 3 — trend
    lc = fuel_kpis.get("liters_change_pct")
    if lc is not None and lc > 8:
        story += _insight(
            f"Fleet consumption up {lc}% vs last month — "
            f"if KM driven is similar, investigate engine health and idling patterns.",
            warn=True)

    story.append(PageBreak())
    return story



# MAINTENANCE — TOTAL INVESTMENT VIEW

def _section_maintenance(payload, maint_kpis):
    story = _section_bar("Maintenance & Fleet Health")

    total   = maint_kpis["total_cost"]
    chg     = maint_kpis["cost_change_pct"]
    chg_lbl = maint_kpis["cost_change_label"]
    cpv     = maint_kpis["cost_per_vehicle"]
    down    = maint_kpis["total_downtime_hrs"]
    events  = maint_kpis["total_events"]
    tco     = payload.cost_summary.total_tco_egp
    maint_pct_tco = round(total / max(tco, 1) * 100, 1)

    # ── KPI row: 4 investment numbers ────────────────────────────────────────
    story += _kpi_row([
        _kpi_card(
            "Total Maintenance Investment",
            f"EGP {total:,.0f}",
            f"vs last month  {chg_lbl}",
            CLR["score_poor"] if chg > 15 else CLR["gold"] if chg > 5 else CLR["green_primary"],
        ),
        _kpi_card(
            "% of Total TCO",
            f"{maint_pct_tco}%",
            "share of total fleet cost",
            CLR["score_poor"] if maint_pct_tco > 20 else CLR["text_muted"],
        ),
        _kpi_card(
            "Cost per Vehicle",
            f"EGP {cpv:,.0f}",
            f"avg across {len(payload.vehicles)} vehicles",
        ),
        _kpi_card(
            "Downtime Hours",
            f"{down} hrs",
            f"{events} maintenance events",
            CLR["score_poor"] if down > 120 else CLR["text_muted"],
        ),
    ])

    # ── Vehicle health status — 5 status cards ────────────────────────────────
    statuses = [
        ("Clear",           maint_kpis.get("clear",     0), CLR["score_great"],  CLR["green_light"], "No issues detected"),
        ("Needs Attention", maint_kpis.get("needs_attn",0), CLR["score_avg"],    CLR["gold_light"],  "Abnormal sensor readings"),
        ("Overdue",         maint_kpis.get("overdue",   0), "#C07820",           "#FFF3CD",          "Service overdue"),
        ("In Maintenance",  maint_kpis.get("in_maint",  0), CLR["status_maint"], CLR["bg_card2"],    "Currently in shop"),
        ("Broken",          maint_kpis.get("broken",    0), CLR["score_poor"],   "#FECACA",          "Out of service"),
    ]
    status_cards = []
    cw = IW / 5
    for label, count, fg, bg, note in statuses:
        status_cards.append(Table([
            [Paragraph(f'<font size="9" color="{fg}"><b>{label}</b></font>',
                       _s(f"sl{label}", alignment=TA_CENTER))],
            [Paragraph(f'<font size="28" color="{fg}"><b>{count}</b></font>',
                       _s(f"sn{label}", fontName=FB, alignment=TA_CENTER, leading=32))],
            [Paragraph(f'<font size="7.5" color="{CLR['text_muted']}">{note}</font>',
                       _s(f"ss{label}", alignment=TA_CENTER))],
        ], colWidths=["100%"],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor(bg)),
            ("TOPPADDING",    (0,0),(-1,-1), 9),
            ("BOTTOMPADDING", (0,0),(-1,-1), 9),
            ("LEFTPADDING",   (0,0),(-1,-1), 4),
            ("RIGHTPADDING",  (0,0),(-1,-1), 4),
            ("LINEABOVE",     (0,0),(-1,0),  2.5, colors.HexColor(fg)),
            ("LINEBELOW",     (0,-1),(-1,-1),0.5, C["border"]),
            ("LINEBEFORE",    (0,0),(0,-1),  0.5, C["border"]),
            ("LINEAFTER",     (-1,0),(-1,-1),0.5, C["border"]),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ])))
    story.append(Table([status_cards], colWidths=[cw]*5,
        style=TableStyle([
            ("LEFTPADDING",  (0,0),(-1,-1), 3),
            ("RIGHTPADDING", (0,0),(-1,-1), 3),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ])))
    story.append(_sp(0.3))

    # ── Charts: health donut (left) + category investment bar (right) ─────────
    donut = ch.chart_maintenance_status_donut(maint_kpis)
    inv_bar = ch.chart_maintenance_investment(maint_kpis)
    story.append(Table([[donut, inv_bar]],
        colWidths=[IW * 0.40, IW * 0.60],
        style=TableStyle([
            ("LEFTPADDING",  (0,0),(-1,-1), 2),
            ("RIGHTPADDING", (0,0),(-1,-1), 2),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ])))
    story.append(_caption(
        "Left: vehicle health status  ·  "
        "Right: maintenance investment by service category"))
    story.append(_sp(0.2))

    # ── Expert insights: total investment lens ────────────────────────────────
    n_offline = maint_kpis.get("overdue",0) + maint_kpis.get("in_maint",0) + maint_kpis.get("broken",0)

    # Insight 1 — TCO share
    if maint_pct_tco > 20:
        story += _insight(
            f"Maintenance represents {maint_pct_tco}% of TCO — above the 15–18% benchmark "
            f"for well-managed fleets. Total investment: EGP {total:,.0f}. "
            f"Cost per vehicle: EGP {cpv:,.0f}. "
            f"Benchmark for heavy trucks: EGP 8,000–12,000/vehicle/month.",
            warn=True)
    else:
        story += _insight(
            f"Maintenance at {maint_pct_tco}% of TCO — within acceptable range. "
            f"EGP {total:,.0f} total  ·  EGP {cpv:,.0f}/vehicle. "
            f"Monitor monthly trend: sustained increases signal aging fleet or deferred service catch-up.")

    # Insight 2 — MoM trend
    if abs(chg) > 15:
        direction = "increased" if chg > 0 else "decreased"
        story += _insight(
            f"Maintenance spend {direction} {abs(chg):.1f}% vs last month "
            f"(EGP {round(total - payload.cost_summary.maintenance_last_month):+,}). "
            f"{'A spike this size typically indicates emergency repairs or catch-up work — investigate root cause.' if chg > 0 else 'Significant reduction — verify no service was deferred rather than eliminated.'}",
            warn=chg > 15)

    # Insight 3 — downtime cost
    if down > 0:
        est_cost = round(down * (total / max(down, 1)) * 1.5)
        story += _insight(
            f"{down} hours of maintenance downtime this month. "
            f"Estimated productivity loss: EGP {est_cost:,} "
            f"(vehicle-hours × opportunity cost). "
            f"Each hour off-road for a heavy truck = EGP 800–1,500 in lost revenue capacity.")

    # Insight 4 — vehicles offline
    if n_offline >= 2:
        story += _insight(
            f"{n_offline} vehicles offline (overdue/in-maint/broken) — "
            f"availability at {round(maint_kpis.get('clear',0)/max(len(payload.vehicles),1)*100,0):.0f}%. "
            f"Each day offline costs EGP {round(cpv/26):,} in fixed costs with zero revenue contribution.",
            warn=True)

    story.append(PageBreak())
    return story



# TCO / CPM BREAKDOWN

def _section_tco(payload, tco_data):
    
    story = _section_bar("Cost Breakdown — Where the Money Goes")

    cs    = payload.cost_summary
    total = tco_data["total"]
    cpm   = tco_data["cpm"]
    km    = tco_data["km"]
    bd    = tco_data["breakdown"]   # list of {name, cost_egp, pct, cpm}

    # ── 4 KPIs that are NEW vs P2 ─────────────────────────────────────────────
    var_p  = tco_data["variable_pct"]
    fix_p  = round(100 - var_p, 1)
    cpv    = tco_data["cost_per_vehicle"]

    fuel_d  = next((d for d in bd if d["name"] == "Fuel"),        {"pct": 0, "cpm": 0})
    depr_d  = next((d for d in bd if d["name"] == "Depreciation"),{"pct": 0, "cpm": 0})
    sal_d   = next((d for d in bd if d["name"] == "Salaries"),    {"pct": 0, "cpm": 0})
    fines_d = next((d for d in bd if d["name"] == "Fines"),       {"cost_egp": 0, "pct": 0})

    story += _kpi_row([
        _kpi_card(
            "Fuel Share of TCO",
            f"{fuel_d['pct']}%",
            f"EGP {cs.fuel_cost_egp:,.0f}  ·  {fuel_d['cpm']:.3f} EGP/km",
            CLR["score_poor"] if fuel_d["pct"] > 55 else CLR["gold"],
        ),
        _kpi_card(
            "Fixed Cost Share",
            f"{fix_p}%",
            f"EGP {cs.fixed_cost_egp:,.0f}  committed monthly",
            CLR["text_muted"],
        ),
        _kpi_card(
            "Avg Cost / Vehicle",
            f"EGP {cpv:,.0f}",
            f"across {tco_data['n_vehicles']} vehicles  ·  {km // tco_data['n_vehicles']:,} km avg",
        ),
        _kpi_card(
            "Traffic Fines",
            f"EGP {fines_d['cost_egp']:,.0f}",
            f"{fines_d['pct']}% of TCO  ·  100% controllable",
            CLR["score_poor"] if fines_d["cost_egp"] > 2000 else CLR["text_muted"],
        ),
    ])

    # ── Charts: breakdown bar + variable/fixed donut ──────────────────────────
    bar_chart   = ch.chart_tco_breakdown_bar(bd)
    donut_chart = ch.chart_tco_donut_split(tco_data)

    if bar_chart:
        story.append(Table([[bar_chart, donut_chart]],
            colWidths=[IW * 0.62, IW * 0.38],
            style=TableStyle([
                ("LEFTPADDING",  (0,0),(-1,-1), 0),
                ("RIGHTPADDING", (0,0),(-1,-1), 0),
                ("TOPPADDING",   (0,0),(-1,-1), 0),
                ("BOTTOMPADDING",(0,0),(-1,-1), 0),
                ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
            ])))
        story.append(_caption(
            "Left: cost split by component (EGP · % of TCO · EGP/km)  ·  "
            "Right: variable vs fixed structure"))
        story.append(_sp(0.25))

    # ── Insights: cost levers only — no headline repetition ──────────────────
    # Insight 1 — biggest lever to pull
    top = bd[0] if bd else {}
    if top:
        story += _insight(
            f"Largest cost component: {top['name']} at {top['pct']}% of TCO "
            f"(EGP {top['cost_egp']:,.0f}  ·  EGP {top['cpm']:.3f}/km). "
            f"A 10% reduction here saves EGP {round(top['cost_egp'] * 0.10):,}/month "
            f"and cuts CPM by EGP {round(top['cpm'] * 0.10, 3):.3f}.")

    # Insight 2 — fixed cost structure
    story += _insight(
        f"Fixed costs ({fix_p}% = EGP {cs.fixed_cost_egp:,.0f}) are committed regardless of km driven. "
        f"Depreciation + salaries alone account for "
        f"EGP {cs.depreciation_egp + cs.salaries_egp:,.0f}. "
        f"To lower fixed CPM: increase utilisation — same fixed cost spread over more km = lower CPM.")

    # Insight 3 — fines (only if non-zero)
    if fines_d["cost_egp"] > 0:
        story += _insight(
            f"Fines (EGP {fines_d['cost_egp']:,.0f}) add EGP {fines_d['cpm']:.3f}/km to CPM — "
            f"entirely avoidable. Eliminate fines → CPM drops to EGP {cpm - fines_d['cpm']:.2f}.",
            warn=fines_d["cost_egp"] > 2000)

    # Insight 4 — variable vs fixed action
    if var_p > 60:
        story += _insight(
            f"Variable costs dominate at {var_p}% — the good news: these are operational levers. "
            f"Fuel eco-driving, maintenance scheduling, and fine elimination can realistically "
            f"reduce variable spend by 10–15% within 3 months.")

    story.append(PageBreak())
    return story



# TRIPS — COST & DELIVERY PERFORMANCE (no revenue data)

def _section_trips(payload, trip_kpis):
    story = _section_bar("Trips & Delivery Performance")

    tot_cost = trip_kpis["total_cost"]
    cpk      = trip_kpis["cost_per_km"]
    cpt      = trip_kpis["cost_per_trip"]
    canc_c   = trip_kpis["cancelled_cost"]
    dr       = trip_kpis["delivery_rate"]
    avg_del  = trip_kpis["avg_delay_min"]
    total    = trip_kpis["total"]

    # ── ROW 1: Delivery performance ───────────────────────────────────────────
    story += _kpi_row([
        _kpi_card("Total Trips",
                  str(total),
                  "this month"),
        _kpi_card("Delivery Rate",
                  f"{dr}%",
                  f"{trip_kpis['delivered']} delivered",
                  CLR["score_poor"] if dr < 80
                  else CLR["score_avg"] if dr < 92
                  else CLR["green_primary"]),
        _kpi_card("Delayed",
                  str(trip_kpis["delayed"]),
                  f"{trip_kpis['delay_rate']}%  ·  avg {avg_del} min",
                  CLR["score_poor"] if trip_kpis["delay_rate"] > 15 else CLR["score_avg"]),
        _kpi_card("Cancelled",
                  str(trip_kpis["cancelled"]),
                  f"{trip_kpis['cancel_rate']}% of total",
                  CLR["score_poor"] if trip_kpis["cancel_rate"] > 7 else CLR["text_muted"]),
    ])

    # ── ROW 2: Cost KPIs ──────────────────────────────────────────────────────
    story += _kpi_row([
        _kpi_card("Total Trip Cost",
                  f"EGP {tot_cost:,.0f}",
                  "all trips this month",
                  CLR["gold"]),
        _kpi_card("Cost per KM",
                  f"EGP {cpk:.2f}",
                  "fleet average"),
        _kpi_card("Cost per Trip",
                  f"EGP {cpt:,.0f}",
                  "avg across all trips"),
        _kpi_card("Wasted on Cancelled",
                  f"EGP {canc_c:,.0f}",
                  "cost with zero delivery",
                  CLR["score_poor"] if canc_c > 5000 else CLR["text_muted"]),
    ])

    # ── Charts: trips donut + cost bars ───────────────────────────────────────
    donut    = ch.chart_trips_status_donut(trip_kpis)
    cost_bar = ch.chart_trips_cost_bars(trip_kpis)

    story.append(Table([[donut, cost_bar]],
        colWidths=[IW * 0.46, IW * 0.54],
        style=TableStyle([
            ("LEFTPADDING",  (0,0),(-1,-1), 2),
            ("RIGHTPADDING", (0,0),(-1,-1), 2),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ])))
    story.append(_caption(
        "Left: trip outcome distribution  ·  "
        "Right: total cost · wasted on cancelled · avg cost per trip"))
    story.append(_sp(0.2))

    # ── Expert insights: cost lens ────────────────────────────────────────────
    # Insight 1 — delivery rate & its cost implication
    if dr < 80:
        story += _insight(
            f"Delivery rate {dr}% is below 80% — every undelivered trip still carries "
            f"its full operating cost (EGP {cpt:,.0f} avg). "
            f"With {trip_kpis['delayed']} delayed + {trip_kpis['cancelled']} cancelled, "
            f"wasted spend is compounding. "
            f"Lowest-performing vehicle: {trip_kpis['worst_vehicle']}.",
            warn=True)
    elif dr < 92:
        story += _insight(
            f"Delivery rate {dr}% — room to improve. "
            f"Each percentage point gained eliminates "
            f"~EGP {round(tot_cost / max(total, 1)):,} in wasted trip cost. "
            f"Focus on {trip_kpis['worst_vehicle']} which has the lowest delivery rate.")
    else:
        story += _insight(
            f"Delivery rate {dr}% — strong operational performance. "
            f"Cost per km: EGP {cpk:.2f}  ·  Cost per trip: EGP {cpt:,.0f}.")

    # Insight 2 — cancelled cost
    if canc_c > 0:
        pct_waste = round(canc_c / max(tot_cost, 1) * 100, 1)
        story += _insight(
            f"EGP {canc_c:,.0f} spent on {trip_kpis['cancelled']} cancelled trips "
            f"({pct_waste}% of total trip cost) — zero delivery for this spend. "
            f"Root causes: vehicle breakdowns, driver unavailability, or client-side cancellations. "
            f"Each root cause has a different corrective action.",
            warn=pct_waste > 8)

    # Insight 3 — delay cost
    if trip_kpis["delayed"] > 0 and avg_del > 0:
        story += _insight(
            f"{trip_kpis['delayed']} delayed trips averaging {avg_del} min. "
            f"Delays increase operating cost (idling, extended driver time) "
            f"and signal route sequencing or vehicle reliability issues. "
            f"Highest cost/km vehicle: {trip_kpis['highest_cost_vehicle']} "
            f"at EGP {trip_kpis['highest_cost_per_km']:.2f}/km.",
            warn=avg_del > 60)

    return story  



# MAIN BUILD

def build_pdf(payload: FleetReportPayload, output_path):
    kpis = calc_executive(payload)

    doc = SimpleDocTemplate(
        output_path,            
        pagesize=A4,
        topMargin=MT, bottomMargin=MB,
        leftMargin=ML, rightMargin=MR,
        title=f"DAWAR Fleet Report — {payload.metadata.report_month}",
        author=payload.metadata.generated_by,
    )
    doc.fleet_name   = payload.metadata.fleet_name
    doc.report_month = payload.metadata.report_month

    fuel_kpis  = calc_fuel(payload)
    maint_kpis = calc_maintenance(payload)
    trip_kpis  = calc_trips(payload)

    tco_data = calc_tco_breakdown(payload)

    story = []
    story += _cover(payload.metadata)
    story += _section_executive(payload, kpis)
    story += _section_fuel(payload, fuel_kpis)
    story += _section_maintenance(payload, maint_kpis)
    story += _section_tco(payload, tco_data)
    story += _section_trips(payload, trip_kpis)

    _pn[0] = 0
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    # output_path can be a string (file path) or a BytesIO buffer
    if isinstance(output_path, str):
        print(f"✓  PDF saved → {output_path}")
    
