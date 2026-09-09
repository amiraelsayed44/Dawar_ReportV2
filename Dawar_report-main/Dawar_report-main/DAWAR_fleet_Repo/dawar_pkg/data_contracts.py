from dataclasses import dataclass
from typing import List, Literal


@dataclass
class ReportMetadata:
    fleet_name:   str
    report_month: str   # "April 2026"
    report_date:  str   # "April 12, 2026"
    generated_by: str
    fleet_size:   int
    currency:     str   # "EGP"
    period:       str   # "2026-04"


@dataclass
class Vehicle:
    id:    str
    make:  str
    model: str
    year:  int
    plate: str
    type:  Literal["Heavy Truck", "Delivery Van", "Sedan", "Pickup"]
    status: Literal["Active", "In Maintenance", "Idle", "Broken"]

    # ── Sensor readings (monthly aggregates from device) ──────
    

    rpm_avg:          float  # avg "Engine RPM"              normal: 1200-2200
    rpm_max:          float  # max "Engine RPM" this month   alert: >3000
    engine_temp_avg:  float  # avg "Engine coolant temp (C)" normal: 85-105
    engine_temp_max:  float  # max "Engine coolant temp (C)" alert: >110
    battery_voltage:  float  # avg "Battery voltage (0.01V)" normal: 12.4-14.8
    engine_load_avg:  float  # avg "Engine load (%)"         normal: 20-70
    engine_load_max:  float  # max "Engine load (%)"         alert: >90
    intake_air_temp:  float  # avg "Intake air temp (C)"     normal: ambient±15
    fuel_pressure:    float  # avg "Fuel pressure (kPa)"     normal: 250-450 petrol
    idle_time_pct:    float  # % engine-on time at speed<5   backend computes this

    # ── Status (set by backend from aggregated sensor logic) ──
    health_status: Literal[
        "Clear", "Needs Attention", "Overdue", "In Maintenance", "Broken"
    ]

    # ── Mileage ──────────────────────────────────────────────
    km_this_month: int
    km_last_month: int
    odometer_km:   int

    # ── Utilization ──────────────────────────────────────────
    available_days:  int
    working_days:    int
    target_util_pct: float   # 0-100


@dataclass
class FuelRecord:
    vehicle_id:   str
    vehicle_type: str
    km_driven:    int
    liters_consumed: float
    price_per_liter: float
    fuel_cost_egp:   float

    # ── Weekly breakdown (trend chart) ────────────────────────
    week1_liters: float
    week2_liters: float
    week3_liters: float
    week4_liters: float

    # ── Historical consumption for Top-5 comparison ───────────
    # Send 0.0 for months with no data. Report auto-detects how many months available.
    months_available: int    # 0, 1, 2, or 3
    liters_month1: float     # last month       (0.0 if unavailable)
    liters_month2: float     # 2 months ago     (0.0 if unavailable)
    liters_month3: float     # 3 months ago     (0.0 if unavailable)
    cost_month1:   float     # fuel cost last month EGP
    cost_month2:   float     # fuel cost 2 months ago EGP
    cost_month3:   float     # fuel cost 3 months ago EGP


MAINT_CATEGORIES = Literal[
    "Routine Service",
    "Emergency & Mechanical Repair",
    "Tires & Suspension",
    "Collision & Bodywork",
    "Compliance & Renewals",
    "Other"
]


@dataclass
class MaintenanceRecord:
    vehicle_id:     str
    vehicle_type:   str
    date:           str
    category:       MAINT_CATEGORIES
    description:    str
    cost_egp:       float
    downtime_hours: float
    status: Literal["Completed", "In Progress"]


@dataclass
class TripRecord:
    trip_id:       str
    vehicle_id:    str
    driver_name:   str
    date:          str
    origin:        str
    destination:   str
    distance_km:   float
    status: Literal["Delivered", "Delayed", "Cancelled"]
    delay_minutes: int    # 0 if on time or cancelled
    cost_egp:      float  # operating cost of this trip (fuel share + driver share)
    # NOTE: no revenue field — not tracked at trip level


@dataclass
class CostSummary:
    # ── This month totals ────────────────────────────────────
    total_tco_egp:          float   # sum of all cost components below
    fuel_cost_egp:          float
    maintenance_cost_egp:   float
    fines_cost_egp:         float   # traffic fines & penalties
    fixed_cost_egp:         float   # depreciation + insurance + salaries
    total_km_driven:        int

    # ── Last month (for MoM % change) ────────────────────────
    tco_last_month:         float
    fuel_last_month:        float
    maintenance_last_month: float
    km_last_month:          int

    # ── Fixed cost breakdown (for TCO page) ──────────────────
    # These should sum to fixed_cost_egp
    depreciation_egp:       float   # monthly depreciation across fleet
    insurance_egp:          float   # insurance premiums
    salaries_egp:           float   # driver salaries
    other_fixed_egp:        float   # registration, admin, parking, etc.


@dataclass
class FleetReportPayload:
    metadata:     ReportMetadata
    vehicles:     List[Vehicle]
    fuel:         List[FuelRecord]
    maintenance:  List[MaintenanceRecord]
    trips:        List[TripRecord]
    cost_summary: CostSummary
