
from data_contracts import FleetReportPayload, Vehicle
from collections import defaultdict


def compute_health_score(v: Vehicle) -> float:
    """Compute 0-100 health score from available device sensor aggregates."""

    if v.status in ("In Maintenance", "Broken"):
        # Off-road vehicles get a reduced base score
        return round(max(10.0, 45.0 - v.engine_load_max * 0.2), 1)

    score = 100.0

    # ── 1. RPM behaviour (25 pts) ────────────────────────────
    # High sustained RPM = driver aggression or mechanical issue
    if   v.rpm_avg > 2800: score -= 20
    elif v.rpm_avg > 2400: score -= 12
    elif v.rpm_avg > 2000: score -= 5

    if   v.rpm_max > 4000: score -= 5   # peak red-line events
    elif v.rpm_max > 3500: score -= 2

    # ── 2. Engine temperature (25 pts) ───────────────────────
    # Overheating is the #1 cause of catastrophic engine failure
    if   v.engine_temp_max > 118: score -= 25
    elif v.engine_temp_max > 112: score -= 15
    elif v.engine_temp_max > 108: score -= 7

    if   v.engine_temp_avg > 106: score -= 8
    elif v.engine_temp_avg > 102: score -= 3

    # ── 3. Engine load (20 pts) ──────────────────────────────
    # Replaces oil pressure — sustained high load = same risk signal
    # Source: "Engine load (%)" from device
    if   v.engine_load_avg > 85: score -= 15
    elif v.engine_load_avg > 75: score -= 8
    elif v.engine_load_avg > 65: score -= 3

    if   v.engine_load_max > 95: score -= 5
    elif v.engine_load_max > 90: score -= 2

    # ── 4. Battery voltage (15 pts) ──────────────────────────
    # Source: "Battery voltage (0.01V)" — already in V from device
    if   v.battery_voltage < 11.5: score -= 15
    elif v.battery_voltage < 12.0: score -= 10
    elif v.battery_voltage < 12.4: score -= 5
    elif v.battery_voltage > 15.0: score -= 8   # overcharging

    # ── 5. Intake air temp (10 pts) ──────────────────────────
    # Source: "Intake air temp (°C)"
    # Ambient in Egypt ~25-35°C. High intake = clogged air filter.
    if   v.intake_air_temp > 65: score -= 10
    elif v.intake_air_temp > 50: score -= 6
    elif v.intake_air_temp > 42: score -= 3

    # ── 6. Idle time % (5 pts) ───────────────────────────────
    # Computed by backend: % of engine-on time where speed < 5 km/h
    if   v.idle_time_pct > 50: score -= 5
    elif v.idle_time_pct > 35: score -= 3
    elif v.idle_time_pct > 25: score -= 1

    return round(max(0.0, score), 1)


def health_score_breakdown(v: Vehicle) -> dict:
    
    if v.status in ("In Maintenance", "Broken"):
        return {"note": "Vehicle off-road", "score": compute_health_score(v)}

    deductions = {}

    # RPM
    d = 0
    if   v.rpm_avg > 2800: d += 20
    elif v.rpm_avg > 2400: d += 12
    elif v.rpm_avg > 2000: d += 5
    if   v.rpm_max > 4000: d += 5
    elif v.rpm_max > 3500: d += 2
    if d: deductions["RPM"] = -d

    # Temperature
    d = 0
    if   v.engine_temp_max > 118: d += 25
    elif v.engine_temp_max > 112: d += 15
    elif v.engine_temp_max > 108: d += 7
    if   v.engine_temp_avg > 106: d += 8
    elif v.engine_temp_avg > 102: d += 3
    if d: deductions["Engine Temp"] = -d

    # Load
    d = 0
    if   v.engine_load_avg > 85: d += 15
    elif v.engine_load_avg > 75: d += 8
    elif v.engine_load_avg > 65: d += 3
    if   v.engine_load_max > 95: d += 5
    elif v.engine_load_max > 90: d += 2
    if d: deductions["Engine Load"] = -d

    # Battery
    d = 0
    if   v.battery_voltage < 11.5: d += 15
    elif v.battery_voltage < 12.0: d += 10
    elif v.battery_voltage < 12.4: d += 5
    elif v.battery_voltage > 15.0: d += 8
    if d: deductions["Battery"] = -d

    # Intake air
    d = 0
    if   v.intake_air_temp > 65: d += 10
    elif v.intake_air_temp > 50: d += 6
    elif v.intake_air_temp > 42: d += 3
    if d: deductions["Intake Air"] = -d

    # Idle
    d = 0
    if   v.idle_time_pct > 50: d += 5
    elif v.idle_time_pct > 35: d += 3
    elif v.idle_time_pct > 25: d += 1
    if d: deductions["Idle Time"] = -d

    total_ded = sum(abs(v) for v in deductions.values())
    return {
        "score":      round(max(0, 100 - total_ded), 1),
        "deductions": deductions,
        "components": {
            "RPM":         {"weight": 25, "source": "Engine RPM (avg+max)"},
            "Engine Temp": {"weight": 25, "source": "Engine coolant temp (avg+max)"},
            "Engine Load": {"weight": 20, "source": "Engine load % (avg+max)"},
            "Battery":     {"weight": 15, "source": "Battery voltage"},
            "Intake Air":  {"weight": 10, "source": "Intake air temp"},
            "Idle Time":   {"weight":  5, "source": "Computed: speed<5 % of time"},
        }
    }


# ── Executive KPIs ────────────────────────────────────────────────────────────
def calc_executive(payload: FleetReportPayload) -> dict:
    cs = payload.cost_summary
    vv = payload.vehicles

    total    = len(vv)
    active   = sum(1 for v in vv if v.status == "Active")
    in_maint = sum(1 for v in vv if v.status in ("In Maintenance","Broken"))
    idle     = sum(1 for v in vv if v.status == "Idle")

    cpm        = round(cs.total_tco_egp / max(cs.total_km_driven,1), 2)
    tco_change = round((cs.total_tco_egp - cs.tco_last_month)
                       / max(cs.tco_last_month,1) * 100, 1)
    fuel_change= round((cs.fuel_cost_egp - cs.fuel_last_month)
                       / max(cs.fuel_last_month,1) * 100, 1)
    util_pct   = round(active / total * 100, 1) if total else 0

    # Sensor-based health scores
    scores = [compute_health_score(v) for v in vv]
    health_index = round(sum(scores) / len(scores), 1) if scores else 0

    def hcount(s): return sum(1 for v in vv if v.health_status == s)

    return dict(
        total_tco=cs.total_tco_egp, tco_change_pct=tco_change,
        fuel_cost=cs.fuel_cost_egp, fuel_change_pct=fuel_change,
        maint_cost=cs.maintenance_cost_egp, fines_cost=cs.fines_cost_egp,
        cpm=cpm, total_km=cs.total_km_driven,
        total_vehicles=total, active=active, in_maintenance=in_maint,
        idle=idle, utilization_pct=util_pct,
        health_index=health_index,
        clear=hcount("Clear"), needs_attention=hcount("Needs Attention"),
        overdue=hcount("Overdue"), in_maint_count=hcount("In Maintenance"),
        broken=hcount("Broken"),
        vehicle_scores={v.id: compute_health_score(v) for v in vv},
    )


# ── Fuel KPIs ─────────────────────────────────────────────────────────────────
def calc_fuel(payload: FleetReportPayload) -> dict:
    fuel = payload.fuel
    if not fuel:
        return {}

    total_liters= sum(f.liters_consumed for f in fuel)
    total_cost  = sum(f.fuel_cost_egp   for f in fuel)
    total_km    = sum(f.km_driven        for f in fuel)
    avg_price   = round(total_cost / max(total_liters,1), 2)
    fleet_eff   = round(total_km   / max(total_liters,1), 2)

    # Month-on-month change (use month1 = last month)
    prev_liters = sum(f.liters_month1 for f in fuel if f.months_available >= 1)
    prev_cost   = sum(f.cost_month1   for f in fuel if f.months_available >= 1)
    liters_chg  = round((total_liters - prev_liters) / max(prev_liters,1) * 100, 1) \
                  if prev_liters > 0 else None
    cost_chg    = round((total_cost - prev_cost) / max(prev_cost,1) * 100, 1) \
                  if prev_cost > 0 else None

    # Weekly trend
    weekly_this = [round(sum(getattr(f,f"week{w}_liters") for f in fuel),1) for w in range(1,5)]
    weekly_prev = [round(sum(f.liters_month1/4 for f in fuel if f.months_available>=1),1)]*4 \
                  if prev_liters > 0 else None

    # Top-5 by absolute consumption this month (highest consumers)
    # Compare each against their own historical average (however many months available)
    top5_data = []
    for f in sorted(fuel, key=lambda x: x.liters_consumed, reverse=True)[:5]:
        hist = [f.liters_month1, f.liters_month2, f.liters_month3][:f.months_available]
        hist_avg = round(sum(hist) / len(hist), 1) if hist else None
        months_label = {0: None, 1: "last month", 2: "avg 2 months", 3: "avg 3 months"}
        top5_data.append(dict(
            vehicle_id=f.vehicle_id,
            vehicle_type=f.vehicle_type,
            liters=f.liters_consumed,
            km_driven=f.km_driven,
            km_per_liter=round(f.km_driven/max(f.liters_consumed,1),2),
            cost_egp=f.fuel_cost_egp,
            hist_avg=hist_avg,
            months_available=f.months_available,
            months_label=months_label.get(f.months_available),
            vs_hist_pct=round((f.liters_consumed - hist_avg)/max(hist_avg,1)*100,1)
                        if hist_avg else None,
        ))

    return dict(
        total_liters=round(total_liters,1), total_cost=round(total_cost,2),
        total_km=total_km, fleet_efficiency=fleet_eff,
        avg_price_per_liter=avg_price,
        liters_change_pct=liters_chg, cost_change_pct=cost_chg,
        weekly_this=weekly_this, weekly_prev=weekly_prev,
        top5=top5_data,
    )


# ── Maintenance KPIs ──────────────────────────────────────────────────────────
def calc_maintenance(payload: FleetReportPayload) -> dict:
    maint= payload.maintenance
    veh  = payload.vehicles
    if not maint:
        return {}

    total_cost  = round(sum(m.cost_egp for m in maint),2)
    total_events= len(maint)
    prev_cost   = payload.cost_summary.maintenance_last_month
    cost_change = round((total_cost-prev_cost)/max(prev_cost,1)*100,1)
    down_hrs    = round(sum(m.downtime_hours for m in maint),1)

    def hcount(s): return sum(1 for v in veh if v.health_status==s)

    by_cat = defaultdict(lambda: dict(events=0, vehicles=set(), cost=0.0))
    for m in maint:
        by_cat[m.category]["events"]   += 1
        by_cat[m.category]["vehicles"].add(m.vehicle_id)
        by_cat[m.category]["cost"]     += m.cost_egp

    categories = [
        dict(name=cat, events=d["events"],
             vehicle_count=len(d["vehicles"]),
             cost_egp=round(d["cost"],2))
        for cat,d in sorted(by_cat.items(), key=lambda x:-x[1]["cost"])
    ]

    # cost per vehicle (for benchmarking)
    cost_per_veh = round(total_cost / max(len(veh), 1), 2)

    # MoM change direction label
    chg_label = f"+{cost_change}%" if cost_change > 0 else f"{cost_change}%"

    return dict(
        total_cost=total_cost, total_events=total_events,
        cost_change_pct=cost_change, cost_change_label=chg_label,
        cost_per_vehicle=cost_per_veh,
        total_downtime_hrs=down_hrs,
        clear=hcount("Clear"), needs_attn=hcount("Needs Attention"),
        overdue=hcount("Overdue"), in_maint=hcount("In Maintenance"),
        broken=hcount("Broken"),
        categories=categories,
    )


# ── Trips KPIs (cost-only — no revenue data) ──────────────────────────────────
def calc_trips(payload: FleetReportPayload) -> dict:
    trips = payload.trips
    if not trips:
        return {}

    total     = len(trips)
    delivered = sum(1 for t in trips if t.status == "Delivered")
    delayed   = sum(1 for t in trips if t.status == "Delayed")
    cancelled = sum(1 for t in trips if t.status == "Cancelled")

    delivery_rate = round(delivered / total * 100, 1) if total else 0
    delay_rate    = round(delayed   / total * 100, 1)
    cancel_rate   = round(cancelled / total * 100, 1)

    total_cost  = round(sum(t.cost_egp    for t in trips), 2)
    total_km    = round(sum(t.distance_km for t in trips), 1)
    avg_km      = round(total_km / total, 1) if total else 0
    cost_per_km = round(total_cost / max(total_km, 1), 2)
    cost_per_trip = round(total_cost / max(total, 1), 2)

    delayed_trips = [t for t in trips if t.status == "Delayed"]
    avg_delay = round(sum(t.delay_minutes for t in delayed_trips)
                      / len(delayed_trips), 0) if delayed_trips else 0

    # Cost wasted on cancelled trips (full cost, zero delivery)
    cancelled_cost = round(sum(t.cost_egp for t in trips if t.status == "Cancelled"), 2)

    # Per-vehicle stats
    veh_stats = defaultdict(lambda: dict(total=0, delivered=0, cost=0.0, km=0.0))
    for t in trips:
        veh_stats[t.vehicle_id]["total"]     += 1
        veh_stats[t.vehicle_id]["cost"]      += t.cost_egp
        veh_stats[t.vehicle_id]["km"]        += t.distance_km
        if t.status == "Delivered":
            veh_stats[t.vehicle_id]["delivered"] += 1

    ranked = sorted(veh_stats.items(),
                    key=lambda x: x[1]["delivered"] / max(x[1]["total"], 1),
                    reverse=True)
    # highest cost-per-km vehicle
    worst_cost = sorted(
        [(vid, round(s["cost"] / max(s["km"], 1), 2)) for vid, s in veh_stats.items()],
        key=lambda x: x[1], reverse=True
    )

    return dict(
        total=total, delivered=delivered, delayed=delayed, cancelled=cancelled,
        delivery_rate=delivery_rate, delay_rate=delay_rate, cancel_rate=cancel_rate,
        total_cost=total_cost, total_km=total_km,
        avg_trip_km=avg_km, cost_per_km=cost_per_km,
        cost_per_trip=cost_per_trip,
        cancelled_cost=cancelled_cost,
        avg_delay_min=int(avg_delay),
        best_vehicle=ranked[0][0]  if ranked else "—",
        worst_vehicle=ranked[-1][0] if ranked else "—",
        highest_cost_vehicle=worst_cost[0][0] if worst_cost else "—",
        highest_cost_per_km=worst_cost[0][1]  if worst_cost else 0,
    )


# ── TCO / CPM breakdown for TCO page ──────────────────────────────────────────
def calc_tco_breakdown(payload: FleetReportPayload) -> dict:
    cs  = payload.cost_summary
    km  = max(cs.total_km_driven, 1)
    n   = max(len(payload.vehicles), 1)

    components = [
        ("Fuel",          cs.fuel_cost_egp),
        ("Maintenance",   cs.maintenance_cost_egp),
        ("Depreciation",  cs.depreciation_egp),
        ("Salaries",      cs.salaries_egp),
        ("Insurance",     cs.insurance_egp),
        ("Fines",         cs.fines_cost_egp),
        ("Other Fixed",   cs.other_fixed_egp),
    ]
    total = cs.total_tco_egp

    breakdown = [
        dict(
            name=name,
            cost_egp=round(cost, 2),
            pct=round(cost / max(total, 1) * 100, 1),
            cpm=round(cost / km, 3),
        )
        for name, cost in components if cost > 0
    ]

    # MoM changes
    tco_chg  = round((total - cs.tco_last_month) / max(cs.tco_last_month, 1) * 100, 1)
    fuel_chg = round((cs.fuel_cost_egp - cs.fuel_last_month)
                     / max(cs.fuel_last_month, 1) * 100, 1)
    maint_chg= round((cs.maintenance_cost_egp - cs.maintenance_last_month)
                     / max(cs.maintenance_last_month, 1) * 100, 1)

    return dict(
        total=total, km=km, n_vehicles=n,
        cpm=round(total / km, 2),
        cost_per_vehicle=round(total / n, 2),
        breakdown=breakdown,
        variable_egp=round(cs.fuel_cost_egp + cs.maintenance_cost_egp + cs.fines_cost_egp, 2),
        fixed_egp=cs.fixed_cost_egp,
        variable_pct=round((cs.fuel_cost_egp + cs.maintenance_cost_egp + cs.fines_cost_egp)
                           / max(total, 1) * 100, 1),
        tco_chg=tco_chg, fuel_chg=fuel_chg, maint_chg=maint_chg,
    )
