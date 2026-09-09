import random
from datetime import datetime
from data_contracts import (
    ReportMetadata, Vehicle, FuelRecord, MaintenanceRecord,
    TripRecord, CostSummary, FleetReportPayload
)
random.seed(42)
_TODAY  = datetime.today()
_PERIOD = _TODAY.strftime("%Y-%m")

_VEH = [
    ("V-001","Mercedes","Actros",  2021,"Heavy Truck","أ ب 1234"),
    ("V-002","Volvo",   "FH16",   2020,"Heavy Truck","أ ب 5678"),
    ("V-003","MAN",     "TGX",    2022,"Heavy Truck","أ ب 9012"),
    ("V-004","Ford",    "Transit",2023,"Delivery Van","ج د 1234"),
    ("V-005","Mercedes","Sprinter",2022,"Delivery Van","ج د 5678"),
    ("V-006","Peugeot", "Boxer",  2021,"Delivery Van","ج د 9012"),
    ("V-007","Toyota",  "Camry",  2023,"Sedan","ه و 1234"),
    ("V-008","Hyundai", "Sonata", 2022,"Sedan","ه و 5678"),
    ("V-009","Toyota",  "Hilux",  2023,"Pickup","ز ح 1234"),
    ("V-010","Ford",    "Ranger", 2021,"Pickup","ز ح 5678"),
]
_HS = ["Clear","Clear","Clear","Clear","Clear",
       "Needs Attention","Needs Attention","Overdue","In Maintenance","Broken"]
_ST_MAP = {
    "Clear":"Active","Needs Attention":"Active",
    "Overdue":"Active","In Maintenance":"In Maintenance","Broken":"Broken"
}
_BASE_KM = {"Heavy Truck":11500,"Delivery Van":6800,"Sedan":4200,"Pickup":5300}
_TGT_U   = {"Heavy Truck":85,"Delivery Van":80,"Sedan":75,"Pickup":80}
_FUEL_L  = {"Heavy Truck":32,"Delivery Van":12,"Sedan":8,"Pickup":14}
_CATS    = ["Routine Service","Emergency & Mechanical Repair",
            "Tires & Suspension","Collision & Bodywork",
            "Compliance & Renewals","Other"]
_MAINT_C = {"Routine Service":400,"Emergency & Mechanical Repair":1800,
            "Tires & Suspension":700,"Collision & Bodywork":2200,
            "Compliance & Renewals":350,"Other":300}
_DRIVERS = ["Ahmed Hassan","Mohamed Saleh","Khaled Ibrahim","Omar Mahmoud",
            "Youssef Adel","Tarek Nasser","Sara Ahmed","Nour El-Din",
            "Hossam Fawzy","Wael Shafik"]
_CITIES  = ["Cairo","Giza","Alexandria","Suez","Port Said",
            "Mansoura","Tanta","Zagazig","Ismailia","Damietta"]

# ── Sensor profiles per health status ─────────────────────────────────────────
def _sensors(hs, vtype):
    
    if hs == "Clear":
        return dict(
            rpm_avg          = random.uniform(1400, 1900),
            rpm_max          = random.uniform(2200, 2800),
            engine_temp_avg  = random.uniform(87,   100),
            engine_temp_max  = random.uniform(100,  108),
            battery_voltage  = random.uniform(13.5, 14.5),
            engine_load_avg  = random.uniform(25,   60),
            engine_load_max  = random.uniform(65,   80),
            intake_air_temp  = random.uniform(28,   40),
            fuel_pressure    = random.uniform(280,  420),
            idle_time_pct    = random.uniform(8,    20),
        )
    elif hs == "Needs Attention":
        return dict(
            rpm_avg          = random.uniform(1900, 2400),
            rpm_max          = random.uniform(3000, 3600),
            engine_temp_avg  = random.uniform(100,  108),
            engine_temp_max  = random.uniform(108,  116),
            battery_voltage  = random.uniform(12.0, 13.2),
            engine_load_avg  = random.uniform(65,   80),
            engine_load_max  = random.uniform(82,   92),
            intake_air_temp  = random.uniform(42,   55),
            fuel_pressure    = random.uniform(200,  270),
            idle_time_pct    = random.uniform(25,   40),
        )
    elif hs == "Overdue":
        return dict(
            rpm_avg          = random.uniform(2300, 2900),
            rpm_max          = random.uniform(3600, 4200),
            engine_temp_avg  = random.uniform(106,  113),
            engine_temp_max  = random.uniform(114,  122),
            battery_voltage  = random.uniform(11.5, 12.2),
            engine_load_avg  = random.uniform(78,   90),
            engine_load_max  = random.uniform(91,   97),
            intake_air_temp  = random.uniform(52,   66),
            fuel_pressure    = random.uniform(140,  210),
            idle_time_pct    = random.uniform(38,   55),
        )
    else:  # In Maintenance / Broken
        return dict(
            rpm_avg          = 0.0,
            rpm_max          = 0.0,
            engine_temp_avg  = random.uniform(110,  128),
            engine_temp_max  = random.uniform(126,  142),
            battery_voltage  = random.uniform(10.5, 11.7),
            engine_load_avg  = random.uniform(85,   98),
            engine_load_max  = random.uniform(95,  100),
            intake_air_temp  = random.uniform(60,   80),
            fuel_pressure    = random.uniform(80,   160),
            idle_time_pct    = 0.0,
        )


def _vehicles():
    out = []
    for i, (vid,make,model,year,vtype,plate) in enumerate(_VEH):
        hs  = _HS[i]
        st  = _ST_MAP[hs]
        km  = int(_BASE_KM[vtype] * random.uniform(0.85,1.15))
        km_p= int(km * random.uniform(0.88,1.12))
        avail = 26
        worked = int(avail * random.uniform(0.60,0.95)) if st=="Active" \
                 else int(avail * random.uniform(0.05,0.25))
        s = _sensors(hs, vtype)
        out.append(Vehicle(
            id=vid, make=make, model=model, year=year, plate=plate,
            type=vtype, status=st, health_status=hs,
            rpm_avg         = round(s["rpm_avg"], 0),
            rpm_max         = round(s["rpm_max"], 0),
            engine_temp_avg = round(s["engine_temp_avg"], 1),
            engine_temp_max = round(s["engine_temp_max"], 1),
            battery_voltage = round(s["battery_voltage"], 2),
            engine_load_avg = round(s["engine_load_avg"], 1),
            engine_load_max = round(s["engine_load_max"], 1),
            intake_air_temp = round(s["intake_air_temp"], 1),
            fuel_pressure   = round(s["fuel_pressure"], 1),
            idle_time_pct   = round(s["idle_time_pct"], 1),
            km_this_month   = km,
            km_last_month   = km_p,
            odometer_km     = km * (2026 - year) * 11,
            available_days  = avail,
            working_days    = worked,
            target_util_pct = float(_TGT_U[vtype]),
        ))
    return out


def _fuel(vehicles):
    out = []
    for v in vehicles:
        rate  = _FUEL_L[v.type]
        liters= round(v.km_this_month/100*rate*random.uniform(0.92,1.12),1)
        price = round(random.uniform(8.8,9.6),2)
        cost  = round(liters*price,2)
        w  = [random.random() for _ in range(4)]
        ws = [round(liters*x/sum(w),1) for x in w]; ws[3]=round(liters-sum(ws[:3]),1)
        # historical — all 3 months available in mock
        l1 = round(v.km_last_month/100*rate*random.uniform(0.90,1.10),1)
        l2 = round(v.km_last_month/100*rate*random.uniform(0.88,1.12),1)
        l3 = round(v.km_last_month/100*rate*random.uniform(0.85,1.15),1)
        out.append(FuelRecord(
            vehicle_id=v.id, vehicle_type=v.type,
            km_driven=v.km_this_month, liters_consumed=liters,
            price_per_liter=price, fuel_cost_egp=cost,
            week1_liters=ws[0],week2_liters=ws[1],
            week3_liters=ws[2],week4_liters=ws[3],
            months_available=3,
            liters_month1=l1, liters_month2=l2, liters_month3=l3,
            cost_month1=round(l1*price,2), cost_month2=round(l2*price,2),
            cost_month3=round(l3*price,2),
        ))
    return out


def _maintenance(vehicles):
    out = []
    for v in vehicles:
        for _ in range(random.randint(1,3)):
            cat  = random.choice(_CATS)
            day  = random.randint(1,28)
            out.append(MaintenanceRecord(
                vehicle_id=v.id, vehicle_type=v.type,
                date=f"{_TODAY.year}-{_TODAY.month:02d}-{day:02d}",
                category=cat,
                description=f"{cat} — {v.make} {v.model} ({v.plate})",
                cost_egp=round(_MAINT_C[cat]*random.uniform(0.85,1.3),2),
                downtime_hours=round(random.uniform(1,14),1),
                status=random.choice(["Completed","Completed","In Progress"]),
            ))
    return out


def _trips(vehicles):
    out=[]; tid=1
    for v in [v for v in vehicles if v.status=="Active"]:
        for _ in range(random.randint(12,35)):
            st=random.choices(["Delivered","Delayed","Cancelled"],weights=[75,18,7])[0]
            dist=round(random.uniform(45,380),1)
            out.append(TripRecord(
                trip_id=f"TR-{tid:04d}",vehicle_id=v.id,
                driver_name=random.choice(_DRIVERS),
                date=f"{_TODAY.year}-{_TODAY.month:02d}-{random.randint(1,28):02d}",
                origin=random.choice(_CITIES),destination=random.choice(_CITIES),
                distance_km=dist,status=st,
                delay_minutes=random.randint(15,180) if st=="Delayed" else 0,
                cost_egp=round(dist*random.uniform(1.8,3.2),2),
            ))
            tid+=1
    return out


def build_mock_payload():
    v=_vehicles(); f=_fuel(v); m=_maintenance(v); t=_trips(v)
    fuel_t=sum(r.fuel_cost_egp for r in f)
    maint_t=sum(r.cost_egp for r in m)
    fines=round(random.uniform(1200,5800),2)
    fixed=round(len(v)*random.uniform(8000,14000),2)
    tco=round(fuel_t+maint_t+fines+fixed,2)
    prev_fuel=round(sum(r.cost_month1 for r in f),2)
    prev_maint=round(maint_t*random.uniform(0.85,1.15),2)
    prev_tco=round(prev_fuel+prev_maint+fines*random.uniform(0.9,1.1)+fixed*random.uniform(0.95,1.05),2)
    n_veh = len(v)
    depreciation = round(n_veh * random.uniform(4000, 9000), 2)
    insurance    = round(n_veh * random.uniform(800,  1800), 2)
    salaries     = round(n_veh * random.uniform(4500, 7500), 2)
    other_fixed  = round(fixed - depreciation - insurance - salaries, 2)

    return FleetReportPayload(
        metadata=ReportMetadata(
            fleet_name="National Logistics Fleet",
            report_month=_TODAY.strftime("%B %Y"),
            report_date=_TODAY.strftime("%B %d, %Y"),
            generated_by="DAWAR Fleet System",
            fleet_size=len(v), currency="EGP", period=_PERIOD,
        ),
        vehicles=v, fuel=f, maintenance=m, trips=t,
        cost_summary=CostSummary(
            total_tco_egp=tco, fuel_cost_egp=round(fuel_t,2),
            maintenance_cost_egp=round(maint_t,2), fines_cost_egp=fines,
            fixed_cost_egp=fixed, total_km_driven=sum(x.km_this_month for x in v),
            tco_last_month=prev_tco, fuel_last_month=prev_fuel,
            maintenance_last_month=prev_maint,
            km_last_month=sum(x.km_last_month for x in v),
            depreciation_egp=depreciation, insurance_egp=insurance,
            salaries_egp=salaries, other_fixed_egp=max(0, other_fixed),
        ),
    )
