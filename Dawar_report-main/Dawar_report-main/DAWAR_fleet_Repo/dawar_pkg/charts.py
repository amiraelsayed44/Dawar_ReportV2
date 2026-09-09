
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from reportlab.platypus import Image

# ── Design tokens (match config.py palette) ────────────────────────────────
BG      = "#F7F5F0"   # warm cream
CARD    = "#EEF2EB"   # sage card
GREEN   = "#2D6A4F"   # forest primary
GREEN2  = "#40916C"   # emerald
SAGE    = "#95D5B2"   # soft sage
AMBER   = "#D4A017"   # gold/warning
RED     = "#B5342A"   # danger
MUTED   = "#7A8875"   # muted text
TEXT    = "#2C2C2C"
GRID_C  = "#C9DEC9"

STATUS_COLORS = {
    "Clear":           GREEN,
    "Needs Attention": AMBER,
    "Overdue":         "#C07820",
    "In Maintenance":  "#7A8E99",
    "Broken":          RED,
}

# ── Helpers ────────────────────────────────────────────────────────────────
def _style(fig, axes):
    """Clean styling — white background, no fills, crisp grid lines."""
    fig.patch.set_facecolor("white")
    for ax in axes:
        ax.set_facecolor("white")
        ax.tick_params(colors="#444444", labelsize=8.5, length=3, width=0.6)
        ax.xaxis.label.set_color("#555555")
        ax.yaxis.label.set_color("#555555")
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["bottom", "left"]:
            ax.spines[spine].set_color(GRID_C)
            ax.spines[spine].set_linewidth(0.8)
        ax.grid(color=GRID_C, linewidth=0.5, alpha=0.6, linestyle="--")


def _img(fig, w_cm, h_cm):
    """Convert figure to a ReportLab Image flowable."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=w_cm * 28.35, height=h_cm * 28.35)



# EXECUTIVE SNAPSHOT


def chart_health_gauge(health_index: float):
    """Semi-circle gauge: Fleet Health Index 0-100."""
    fig, ax = plt.subplots(figsize=(5, 3.2), subplot_kw=dict(aspect="equal"))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # gauge arc zones
    zones = [(0.33, RED, "0–60"), (0.22, AMBER, "60–80"), (0.22, GREEN, "80–100")]
    theta = np.linspace(np.pi, 0, 200)
    r_in, r_out = 0.55, 0.85

    start = 0.0
    for frac, color, _ in zones:
        end   = start + frac
        th    = np.linspace(np.pi * (1 - start), np.pi * (1 - end), 60)
        x_out = r_out * np.cos(th); y_out = r_out * np.sin(th)
        x_in  = r_in  * np.cos(th); y_in  = r_in  * np.sin(th)
        xs = np.concatenate([x_out, x_in[::-1]])
        ys = np.concatenate([y_out, y_in[::-1]])
        ax.fill(xs, ys, color=color, alpha=0.85)
        start = end

    # needle
    angle  = np.pi * (1 - health_index / 100)
    nx = 0.70 * np.cos(angle); ny = 0.70 * np.sin(angle)
    ax.annotate("", xy=(nx, ny), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=TEXT, lw=2))
    ax.add_patch(plt.Circle((0, 0), 0.06, color=TEXT, zorder=5))

    # score text
    color = GREEN if health_index >= 80 else AMBER if health_index >= 60 else RED
    ax.text(0, -0.18, f"{health_index:.0f}", ha="center", va="center",
            fontsize=22, fontweight="bold", color=color)
    ax.text(0, -0.36, "Fleet Health Index", ha="center", va="center",
            fontsize=8, color=MUTED)

    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-0.55, 1.05)
    ax.axis("off")
    fig.tight_layout(pad=0.8)
    return _img(fig, 7.5, 4.8)


def chart_fleet_status_donut(kpis: dict):
    
    labels = ["Clear", "Needs Attention", "Overdue", "In Maint.", "Broken"]
    vals   = [
        kpis.get("clear", 0),
        kpis.get("needs_attention", 0),
        kpis.get("overdue", 0),
        kpis.get("in_maint_count", 0),
        kpis.get("broken", 0),
    ]
    colors = [STATUS_COLORS[s] for s in
              ["Clear","Needs Attention","Overdue","In Maintenance","Broken"]]

    fig, ax = plt.subplots(figsize=(7, 5.2))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    wedges, _, autotexts = ax.pie(
        vals,
        labels=None,
        colors=colors,
        autopct=lambda p: f"{p:.0f}%" if p > 4 else "",
        startangle=90,
        wedgeprops=dict(width=0.52, edgecolor=BG, linewidth=1.5),
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color("white")
        at.set_fontweight("bold")

    ax.legend(
        [f"{l}  ({v})" for l, v in zip(labels, vals)],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=3,
        fontsize=8.5,
        frameon=False,
        labelcolor=TEXT,
    )
    ax.set_title("Fleet Health Status", fontsize=11,
                 fontweight="bold", color=GREEN, pad=8)

    fig.tight_layout(pad=1.0)
    return _img(fig, 9, 5.5)


def chart_utilization_bar(kpis: dict):
    """Simple 3-bar chart: Active / Idle / In Maintenance."""
    cats   = ["Active", "Idle", "In Maint."]
    values = [kpis.get("active",0), kpis.get("idle",0), kpis.get("in_maintenance",0)]
    colors = [GREEN, MUTED, AMBER]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(cats, values, color=colors, width=0.5, edgecolor=BG)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(v), ha="center", va="bottom", fontsize=12,
                fontweight="bold", color=TEXT)
    ax.set_ylabel("Vehicles", fontsize=9); ax.set_ylim(0, max(values)+2)
    ax.set_title("Fleet Utilization", fontsize=10, fontweight="bold", color=GREEN)
    _style(fig, [ax])
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=GRID_C, linewidth=0.5, alpha=0.5, linestyle="--")
    fig.tight_layout(pad=1.0)
    return _img(fig, 8, 4.8)



# FUEL SECTION


def chart_fuel_weekly_trend(fuel_kpis: dict):
    """Area chart: weekly fuel consumption this month vs last month."""
    weeks      = ["Week 1", "Week 2", "Week 3", "Week 4"]
    this_month = fuel_kpis.get("weekly_this", [0]*4)
    last_month = fuel_kpis.get("weekly_prev")
    has_prev   = last_month is not None and any(v > 0 for v in last_month)
    if last_month is None:
        last_month = [0]*4

    fig, ax = plt.subplots(figsize=(13, 4))
    x = np.arange(4)

    ax.fill_between(x, this_month, alpha=0.15, color=GREEN2)
    ax.plot(x, this_month, "o-", color=GREEN2, linewidth=2.2,
            markersize=7, label="This Month", zorder=3,
            markerfacecolor="white", markeredgewidth=2)
    if has_prev:
        ax.fill_between(x, last_month, alpha=0.08, color=AMBER)
        ax.plot(x, last_month, "s--", color=AMBER, linewidth=1.6,
                markersize=5, label="Last Month", alpha=0.9,
                markerfacecolor="white", markeredgewidth=1.5)

    y_max = max(this_month + (last_month if has_prev else [])) * 1.0
    for xi, y in enumerate(this_month):
        ax.annotate(f"{y:,.0f}L", (xi, y),
                    textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8.5, color=GREEN2, fontweight="bold")
        if has_prev and last_month[xi] > 0:
            diff = round((y - last_month[xi]) / last_month[xi] * 100, 1)
            sign = "+" if diff > 0 else ""
            col  = RED if diff > 5 else GREEN2 if diff < -3 else MUTED
            ax.annotate(f"{sign}{diff}%", (xi, y),
                        textcoords="offset points", xytext=(0, -16),
                        ha="center", fontsize=7.5, color=col)

    ax.set_xticks(x)
    ax.set_xticklabels(weeks, fontsize=9)
    ax.set_ylabel("Liters", fontsize=9)
    ax.set_ylim(0, y_max * 1.28)
    ax.set_title("Weekly Fuel Consumption — This Month vs Last Month",
                 fontsize=11, fontweight="bold", color=GREEN, pad=10)
    ax.legend(fontsize=9, frameon=False, loc="upper right")
    _style(fig, [ax])
    fig.tight_layout(pad=1.0)
    return _img(fig, 16, 4.5)


def chart_top5_fuel(top5: list):
    """
    Top 5 highest-consuming vehicles vs their own historical average.
    Shows this month vs avg of up to 3 previous months.
    If hist_avg is None → no history available → show single bar only.
    """
    if not top5:
        return None

    ids      = [d["vehicle_id"]    for d in top5]
    actual   = [d["liters"]        for d in top5]
    hist_avg = [d.get("hist_avg")  for d in top5]
    months_l = [d.get("months_label") for d in top5]
    vs_pct   = [d.get("vs_hist_pct") for d in top5]
    has_hist = any(h is not None for h in hist_avg)

    n = len(ids)
    y = np.arange(n)
    fig, ax = plt.subplots(figsize=(14, max(3.5, n * 0.75 + 1.5)))

    # ── Bars ─────────────────────────────────────────────────
    bar_h = 0.36 if has_hist else 0.50
    bars_this = ax.barh(y + (bar_h/2 if has_hist else 0), actual, bar_h,
                        color=GREEN2, alpha=0.88, label="This Month",
                        edgecolor="white", linewidth=0.5)
    if has_hist:
        ax.barh(y - bar_h/2,
                [h if h is not None else 0 for h in hist_avg],
                bar_h, color=AMBER, alpha=0.65,
                label="Historical Avg", edgecolor="white", linewidth=0.5)

    # ── Value labels — right of longest bar ──────────────────
    max_v = max(actual) if actual else 1
    for i, (a, h, pct) in enumerate(zip(actual, hist_avg, vs_pct)):
        y_pos = i + (bar_h/2 if has_hist else 0)
        ax.text(a + max_v * 0.02, y_pos,
                f"{a:,.0f} L", va="center", fontsize=8.5,
                color=TEXT, fontweight="bold")
        if h is not None and pct is not None:
            sign = "+" if pct > 0 else ""
            col  = RED if pct > 8 else AMBER if pct > 3 else GREEN2
            ax.text(max_v * 1.12, y_pos - (bar_h/2 if has_hist else 0),
                    f"{sign}{pct:.1f}%", va="center",
                    fontsize=8, color=col, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels(ids, fontsize=9.5, fontweight="bold", color=TEXT)
    ax.set_xlabel("Liters Consumed", fontsize=9, color=MUTED)

    # ── Dynamic title based on how many months of history ────
    # Use the label from the first vehicle with history
    hist_label = next((m for m in months_l if m), "no history")
    title = f"Top 5 Fuel Consumers — This Month vs {hist_label.title()}"             if has_hist else "Top 5 Fuel Consumers — This Month"
    ax.set_title(title, fontsize=11, fontweight="bold", color=GREEN, pad=10)

    if has_hist:
        ax.legend(fontsize=9, frameon=False, labelcolor=TEXT,
                  loc="lower right")

    ax.invert_yaxis()
    ax.set_xlim(0, max(actual) * 1.45)
    _style(fig, [ax])
    fig.tight_layout(pad=1.2)
    return _img(fig, 14, min(6.5, max(4, n * 0.75 + 1)))



# MAINTENANCE SECTION


def chart_maintenance_status_donut(maint_kpis: dict):
    """Donut: vehicle health status — sized to fit 40% column width."""
    keys   = ["clear","needs_attn","overdue","in_maint","broken"]
    labels = ["Clear","Needs Attention","Overdue","In Maint.","Broken"]
    colors = [STATUS_COLORS[s] for s in
              ["Clear","Needs Attention","Overdue","In Maintenance","Broken"]]
    vals   = [maint_kpis.get(k, 0) for k in keys]

    fig, ax = plt.subplots(figsize=(4.5, 4.2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    wedges, _, autotexts = ax.pie(
        vals, colors=colors, labels=None,
        autopct=lambda p: f"{p:.0f}%" if p > 4 else "",
        startangle=90,
        wedgeprops=dict(width=0.50, edgecolor="white", linewidth=1.5),
        pctdistance=0.73,
        radius=0.85,
    )
    for at in autotexts:
        at.set_fontsize(8.5); at.set_color("white"); at.set_fontweight("bold")

    ax.legend(
        [f"{l} ({v})" for l, v in zip(labels, vals)],
        loc="lower center", bbox_to_anchor=(0.5, -0.14),
        ncol=2, fontsize=7.5, frameon=False,
    )
    ax.set_title("Vehicle Health Status", fontsize=10,
                 fontweight="bold", color=GREEN, pad=6)
    fig.subplots_adjust(top=0.88, bottom=0.18)
    return _img(fig, 7, 4.8)


def chart_maintenance_investment(maint_kpis: dict):
    
    cats = maint_kpis.get("categories", [])
    if not cats:
        return None

    # Filter out zero-cost categories
    cats = [d for d in cats if d["cost_egp"] > 0]
    if not cats:
        return None

    labels = [d["name"]       for d in cats]
    values = [d["cost_egp"]   for d in cats]
    counts = [d["vehicle_count"] for d in cats]

    # Color by category type
    CAT_COLORS = {
        "Routine Service":               GREEN2,
        "Emergency & Mechanical Repair": RED,
        "Tires & Suspension":            AMBER,
        "Collision & Bodywork":          "#C07820",
        "Compliance & Renewals":         "#1D6E8B",
        "Other":                         MUTED,
    }
    bar_colors = [CAT_COLORS.get(l, MUTED) for l in labels]

    n = len(labels)
    fig, ax = plt.subplots(figsize=(8, max(3.0, n * 0.65 + 0.8)))

    y = np.arange(n)
    bars = ax.barh(y, values, 0.55, color=bar_colors, edgecolor=BG, alpha=0.88)

    # Labels: EGP value + vehicle count
    max_val = max(values) if values else 1
    for i, (val, cnt) in enumerate(zip(values, counts)):
        ax.text(val + max_val * 0.02, i,
                f"EGP {val:,.0f}",
                va="center", fontsize=8.5, color=TEXT, fontweight="bold")
        ax.text(max_val * 1.35, i,
                f"{cnt}v",
                va="center", ha="right", fontsize=8, color=MUTED)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=TEXT)
    ax.set_xlabel("Investment (EGP)", fontsize=9, color=MUTED)
    ax.set_xlim(0, max_val * 1.50)
    ax.set_title("Investment by Service Category", fontsize=10,
                 fontweight="bold", color=GREEN, pad=8)
    ax.invert_yaxis()
    _style(fig, [ax])
    ax.grid(axis="x", color=GRID_C, linewidth=0.4, alpha=0.7)
    ax.grid(axis="y", visible=False)
    fig.tight_layout(pad=1.2)
    return _img(fig, 10, max(3.5, n * 0.70 + 1.0))





# TRIPS SECTION


def chart_trips_status_donut(trip_kpis: dict):
    """Donut: Delivered / Delayed / Cancelled — sized for 48% column."""
    vals   = [trip_kpis.get("delivered", 0),
              trip_kpis.get("delayed",   0),
              trip_kpis.get("cancelled", 0)]
    labels = ["Delivered", "Delayed", "Cancelled"]
    colors = [GREEN2, AMBER, RED]
    total  = sum(vals)

    fig, ax = plt.subplots(figsize=(4.8, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    _, _, autotexts = ax.pie(
        vals, colors=colors, labels=None,
        autopct=lambda p: f"{p:.0f}%" if p > 3 else "",
        startangle=90,
        wedgeprops=dict(width=0.50, edgecolor="white", linewidth=1.5),
        pctdistance=0.73,
        radius=0.85,
    )
    for at in autotexts:
        at.set_fontsize(10); at.set_color("white"); at.set_fontweight("bold")

    ax.legend(
        [f"{l} ({v})" for l, v in zip(labels, vals)],
        loc="lower center", bbox_to_anchor=(0.5, -0.10),
        ncol=3, fontsize=8.5, frameon=False,
    )
    ax.set_title("Trip Status Distribution", fontsize=10,
                 fontweight="bold", color=GREEN, pad=6)
    fig.subplots_adjust(top=0.88, bottom=0.14)
    return _img(fig, 7.5, 5)


def chart_revenue_vs_cost(trip_kpis: dict):
    """Bar chart: Revenue vs Cost vs Margin — sized for 52% column."""
    cats  = ["Revenue", "Cost", "Margin"]
    vals  = [trip_kpis.get("total_revenue", 0),
             trip_kpis.get("total_cost",    0),
             trip_kpis.get("total_margin",  0)]
    colors = [GREEN2, AMBER, GREEN]

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    fig.patch.set_facecolor("white")

    bars = ax.bar(cats, vals, color=colors, width=0.50,
                  edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.015,
                f"EGP {v:,.0f}", ha="center", va="bottom",
                fontsize=8.5, fontweight="bold", color=TEXT)

    ax.set_ylabel("EGP", fontsize=9, color="#555555")
    ax.set_ylim(0, max(vals) * 1.20)
    ax.set_title("Revenue vs Cost vs Margin", fontsize=10,
                 fontweight="bold", color=GREEN, pad=8)
    _style(fig, [ax])
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=GRID_C, linewidth=0.5, linestyle="--", alpha=0.6)
    fig.subplots_adjust(top=0.88, bottom=0.10)
    return _img(fig, 8.5, 5)



# TCO PAGE CHARTS


def chart_tco_breakdown_bar(breakdown: list):
    """
    Horizontal bar — cost components sorted largest to smallest.
    Each bar shows EGP amount + % of TCO.
    """
    if not breakdown:
        return None

    labels = [d["name"]     for d in breakdown]
    values = [d["cost_egp"] for d in breakdown]
    pcts   = [d["pct"]      for d in breakdown]
    cpms   = [d["cpm"]      for d in breakdown]

    CAT_COLORS = {
        "Fuel":         GREEN2,
        "Maintenance":  AMBER,
        "Depreciation": "#7A8E99",
        "Salaries":     "#5B8A72",
        "Insurance":    "#8B7355",
        "Fines":        RED,
        "Other Fixed":  MUTED,
    }
    colors = [CAT_COLORS.get(l, MUTED) for l in labels]

    n   = len(labels)
    fig, ax = plt.subplots(figsize=(10, max(3.5, n * 0.70 + 1.0)))
    fig.patch.set_facecolor("white")

    y    = np.arange(n)
    bars = ax.barh(y, values, 0.55, color=colors, edgecolor="white", linewidth=0.5)

    max_v = max(values) if values else 1
    for i, (val, pct, cpm) in enumerate(zip(values, pcts, cpms)):
        ax.text(val + max_v * 0.02, i,
                f"EGP {val:,.0f}",
                va="center", fontsize=8.5, color=TEXT, fontweight="bold")
        ax.text(max_v * 1.42, i,
                f"{pct}%",
                va="center", ha="right", fontsize=8.5,
                color=TEXT, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=TEXT)
    ax.set_xlabel("EGP", fontsize=9, color="#555555")
    ax.set_xlim(0, max_v * 1.55)
    ax.set_title("TCO Cost Components", fontsize=11,
                 fontweight="bold", color=GREEN, pad=10)
    ax.invert_yaxis()
    _style(fig, [ax])
    ax.grid(axis="x", color=GRID_C, linewidth=0.5, linestyle="--", alpha=0.5)
    ax.grid(axis="y", visible=False)
    fig.tight_layout(pad=1.2)
    return _img(fig, 14, max(4, n * 0.80 + 1.2))


def chart_tco_donut_split(tco_data: dict):
    
    variable = tco_data.get("variable_egp", 0)
    fixed    = tco_data.get("fixed_egp",    0)
    total    = variable + fixed

    fig, ax = plt.subplots(figsize=(4.5, 4.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    vals   = [variable, fixed]
    labels = ["Variable\n(Fuel+Maint+Fines)", "Fixed\n(Depr+Salary+Ins)"]
    colors = [GREEN2, "#7A8E99"]

    _, _, autotexts = ax.pie(
        vals, colors=colors, labels=None,
        autopct=lambda p: f"{p:.0f}%",
        startangle=90,
        wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2),
        pctdistance=0.72,
    )
    for at in autotexts:
        at.set_fontsize(11); at.set_color("white"); at.set_fontweight("bold")

    ax.legend(
        [f"{l.replace(chr(10),' ')} — EGP {v:,.0f}" for l, v in zip(labels, vals)],
        loc="lower center", bbox_to_anchor=(0.5, -0.12),
        ncol=1, fontsize=8, frameon=False,
    )
    ax.set_title("Variable vs Fixed", fontsize=10,
                 fontweight="bold", color=GREEN, pad=6)
    fig.subplots_adjust(top=0.88, bottom=0.22)
    return _img(fig, 7, 4.8)


def chart_trips_cost_bars(trip_kpis: dict):
    
    cats   = ["Total Trip Cost", "Wasted on\nCancelled", "Avg Cost\nper Trip"]
    vals   = [
        trip_kpis.get("total_cost",      0),
        trip_kpis.get("cancelled_cost",  0),
        trip_kpis.get("cost_per_trip",   0),
    ]
    colors = [GREEN2, RED, AMBER]

    # Use two y-axes: left for totals, right for per-trip avg (different scale)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    fig.patch.set_facecolor("white")

    bars = ax.bar([0, 1], vals[:2], 0.50, color=colors[:2],
                  edgecolor="white", linewidth=0.5)
    ax2  = ax.twinx()
    ax2.bar([2], vals[2:], 0.50, color=colors[2],
            edgecolor="white", linewidth=0.5)
    ax2.set_ylabel("EGP / Trip", fontsize=8.5, color=AMBER)
    ax2.tick_params(colors=AMBER, labelsize=8)
    for spine in ["top"]:
        ax2.spines[spine].set_visible(False)
    ax2.spines["right"].set_color(AMBER)

    for bar, v in zip(bars, vals[:2]):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + max(vals[:2]) * 0.02,
                f"EGP {v:,.0f}", ha="center", va="bottom",
                fontsize=8.5, fontweight="bold", color=TEXT)
    ax2.text(2, vals[2] + vals[2] * 0.05,
             f"EGP {vals[2]:,.0f}", ha="center", va="bottom",
             fontsize=8.5, fontweight="bold", color=AMBER)

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(cats, fontsize=8.5)
    ax.set_ylabel("EGP", fontsize=9, color="#555555")
    ax.set_ylim(0, max(vals[:2]) * 1.22 if vals[:2] else 1)
    ax2.set_ylim(0, vals[2] * 1.22 if vals[2] else 1)
    ax.set_title("Trip Cost Overview", fontsize=10,
                 fontweight="bold", color=GREEN, pad=8)
    _style(fig, [ax])
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=GRID_C, linewidth=0.5, linestyle="--", alpha=0.5)
    fig.tight_layout(pad=1.0)
    return _img(fig, 8.5, 5)
