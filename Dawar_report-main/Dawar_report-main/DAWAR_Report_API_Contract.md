# DAWAR Fleet Report — API Contract

**One route.** The backend POSTs the full fleet data in the request body and gets the PDF report back in the response. No token is sent — authentication is handled on the backend before the request reaches this route.

> The example body in this document was run end-to-end through the actual report engine and returned a valid PDF with **no error**.

## The route

```
POST /generate-report
Content-Type: application/json
```

**Request body:** one JSON object with the six parts below.

**Response:** the PDF file — `Content-Type: application/pdf` (plus headers `X-Report-Period` and `X-Fleet-Name`).

On bad/incomplete data the route returns **HTTP 422** with a clear message; on an unexpected failure, **HTTP 500**.

There is also a `GET /health` liveness check.

> For local testing before the backend is wired up, POST with **no body** and the route generates a report from built-in mock data.

## Body shape

```
{
  "metadata":     { object },   // report-level info
  "vehicles":     [ objects ],  // one per vehicle
  "fuel":         [ objects ],  // one per vehicle
  "maintenance":  [ objects ],  // one per maintenance event
  "trips":        [ objects ],  // one per trip
  "cost_summary": { object }    // fleet-wide cost rollup
}
```

## Golden rules (to avoid runtime errors)

1. **Every field is required.** No optional fields, no defaults. A missing key returns 422.
2. **No extra fields.** Any key not listed below returns 422. Do not add `id`, `created_at`, `_id`, etc. to the objects.
3. **No `null` values.** Numeric fields must carry a real number — send `0` / `0.0`, never `null`.
4. **Lists vs objects:** `metadata` and `cost_summary` are single objects; the other four are arrays of objects.
5. **Respect the allowed enum values** for `type`, `status`, `health_status`, `category` (case-sensitive, exact match).
6. **Numbers as JSON numbers**, not strings: `9.2` not `"9.2"`.
7. The four lists should reflect a real, populated month (non-empty).


---

## Field reference

### `metadata` (object)

| Field | JSON type | Notes |
|---|---|---|
| `fleet_name` | string | Fleet display name. |
| `report_month` | string | Human label, e.g. "April 2026". |
| `report_date` | string | Generation date, e.g. "April 12, 2026". |
| `generated_by` | string | Source system / author. |
| `fleet_size` | integer | Number of vehicles. |
| `currency` | string | Currency code, e.g. "EGP". |
| `period` | string | Period key, e.g. "2026-04" (used in the output filename). |

### `vehicles` (array)

Sensor fields are monthly aggregates already computed on the backend.

| Field | JSON type | Notes |
|---|---|---|
| `id` | string | Vehicle ID. |
| `make` | string | Manufacturer. |
| `model` | string | Model. |
| `year` | integer | Model year. |
| `plate` | string | Plate number (display only). |
| `type` | string | `Heavy Truck` | `Delivery Van` | `Sedan` | `Pickup`. |
| `status` | string | `Active` | `In Maintenance` | `Idle` | `Broken`. |
| `rpm_avg` | number | Avg RPM (0 if off-road). |
| `rpm_max` | number | Max RPM. |
| `engine_temp_avg` | number | Avg coolant temp °C. |
| `engine_temp_max` | number | Max coolant temp °C. |
| `battery_voltage` | number | Avg voltage V. |
| `engine_load_avg` | number | Avg load %. |
| `engine_load_max` | number | Max load %. |
| `intake_air_temp` | number | Avg intake air temp °C. |
| `fuel_pressure` | number | Avg fuel pressure kPa. |
| `idle_time_pct` | number | % time at speed < 5 km/h. |
| `health_status` | string | `Clear` | `Needs Attention` | `Overdue` | `In Maintenance` | `Broken`. |
| `km_this_month` | integer | Distance this month. |
| `km_last_month` | integer | Distance previous month. |
| `odometer_km` | integer | Lifetime odometer. |
| `available_days` | integer | Days available. |
| `working_days` | integer | Days worked. |
| `target_util_pct` | number | Utilization target 0–100. |

### `fuel` (array)

| Field | JSON type | Notes |
|---|---|---|
| `vehicle_id` | string | Vehicle reference. |
| `vehicle_type` | string | Category. |
| `km_driven` | integer | Distance covered. |
| `liters_consumed` | number | Litres this month. |
| `price_per_liter` | number | Avg price/litre. |
| `fuel_cost_egp` | number | Total fuel cost. |
| `week1_liters` | number | Week 1 litres. |
| `week2_liters` | number | Week 2 litres. |
| `week3_liters` | number | Week 3 litres. |
| `week4_liters` | number | Week 4 litres. |
| `months_available` | integer | 0, 1, 2 or 3. |
| `liters_month1` | number | Litres last month (0.0 if absent). |
| `liters_month2` | number | Litres 2 months ago. |
| `liters_month3` | number | Litres 3 months ago. |
| `cost_month1` | number | Cost last month. |
| `cost_month2` | number | Cost 2 months ago. |
| `cost_month3` | number | Cost 3 months ago. |

### `maintenance` (array)

| Field | JSON type | Notes |
|---|---|---|
| `vehicle_id` | string | Vehicle reference. |
| `vehicle_type` | string | Category. |
| `date` | string | `YYYY-MM-DD`. |
| `category` | string | `Routine Service` | `Emergency & Mechanical Repair` | `Tires & Suspension` | `Collision & Bodywork` | `Compliance & Renewals` | `Other`. |
| `description` | string | Free text. |
| `cost_egp` | number | Event cost. |
| `downtime_hours` | number | Hours off-road. |
| `status` | string | `Completed` | `In Progress`. |

### `trips` (array)

No revenue field — trips are cost-and-delivery only.

| Field | JSON type | Notes |
|---|---|---|
| `trip_id` | string | Trip identifier. |
| `vehicle_id` | string | Vehicle reference. |
| `driver_name` | string | Driver (display only). |
| `date` | string | `YYYY-MM-DD`. |
| `origin` | string | Origin city. |
| `destination` | string | Destination city. |
| `distance_km` | number | Trip distance. |
| `status` | string | `Delivered` | `Delayed` | `Cancelled`. |
| `delay_minutes` | integer | Minutes late (0 if on time / cancelled). |
| `cost_egp` | number | Operating cost. |

### `cost_summary` (object)

`depreciation_egp + insurance_egp + salaries_egp + other_fixed_egp` should sum to `fixed_cost_egp`; variable + fixed should reconcile to `total_tco_egp`.

| Field | JSON type | Notes |
|---|---|---|
| `total_tco_egp` | number | Total cost of ownership. |
| `fuel_cost_egp` | number | Total fuel cost. |
| `maintenance_cost_egp` | number | Total maintenance cost. |
| `fines_cost_egp` | number | Traffic fines. |
| `fixed_cost_egp` | number | Sum of the four fixed components. |
| `total_km_driven` | integer | Fleet distance this month. |
| `tco_last_month` | number | Previous TCO. |
| `fuel_last_month` | number | Previous fuel cost. |
| `maintenance_last_month` | number | Previous maintenance cost. |
| `km_last_month` | integer | Previous distance. |
| `depreciation_egp` | number | Monthly depreciation. |
| `insurance_egp` | number | Insurance. |
| `salaries_egp` | number | Driver salaries. |
| `other_fixed_egp` | number | Registration, admin, etc. |

---

## Full example request body

This exact body produced a 6-page PDF with no error:

```json
{
  "metadata": {
    "fleet_name": "National Logistics Fleet",
    "report_month": "April 2026",
    "report_date": "April 12, 2026",
    "generated_by": "DAWAR Fleet System",
    "fleet_size": 3,
    "currency": "EGP",
    "period": "2026-04"
  },
  "vehicles": [
    {
      "id": "V-001",
      "make": "Mercedes",
      "model": "Actros",
      "year": 2021,
      "plate": "أ ب 1234",
      "type": "Heavy Truck",
      "status": "Active",
      "rpm_avg": 1650.0,
      "rpm_max": 2550.0,
      "engine_temp_avg": 94.0,
      "engine_temp_max": 104.0,
      "battery_voltage": 14.1,
      "engine_load_avg": 48.0,
      "engine_load_max": 72.0,
      "intake_air_temp": 34.0,
      "fuel_pressure": 360.0,
      "idle_time_pct": 14.0,
      "health_status": "Clear",
      "km_this_month": 11800,
      "km_last_month": 11200,
      "odometer_km": 564000,
      "available_days": 26,
      "working_days": 22,
      "target_util_pct": 85.0
    },
    {
      "id": "V-002",
      "make": "Ford",
      "model": "Transit",
      "year": 2023,
      "plate": "ج د 5678",
      "type": "Delivery Van",
      "status": "Active",
      "rpm_avg": 2100.0,
      "rpm_max": 3200.0,
      "engine_temp_avg": 103.0,
      "engine_temp_max": 111.0,
      "battery_voltage": 12.6,
      "engine_load_avg": 70.0,
      "engine_load_max": 88.0,
      "intake_air_temp": 47.0,
      "fuel_pressure": 250.0,
      "idle_time_pct": 30.0,
      "health_status": "Needs Attention",
      "km_this_month": 6900,
      "km_last_month": 6500,
      "odometer_km": 142000,
      "available_days": 26,
      "working_days": 20,
      "target_util_pct": 80.0
    },
    {
      "id": "V-003",
      "make": "Toyota",
      "model": "Camry",
      "year": 2022,
      "plate": "ه و 1234",
      "type": "Sedan",
      "status": "In Maintenance",
      "rpm_avg": 0.0,
      "rpm_max": 0.0,
      "engine_temp_avg": 118.0,
      "engine_temp_max": 130.0,
      "battery_voltage": 11.2,
      "engine_load_avg": 90.0,
      "engine_load_max": 98.0,
      "intake_air_temp": 68.0,
      "fuel_pressure": 120.0,
      "idle_time_pct": 0.0,
      "health_status": "In Maintenance",
      "km_this_month": 1200,
      "km_last_month": 4200,
      "odometer_km": 88000,
      "available_days": 26,
      "working_days": 4,
      "target_util_pct": 75.0
    }
  ],
  "fuel": [
    {
      "vehicle_id": "V-001",
      "vehicle_type": "Heavy Truck",
      "km_driven": 11800,
      "liters_consumed": 3776.0,
      "price_per_liter": 9.2,
      "fuel_cost_egp": 34739.2,
      "week1_liters": 940.0,
      "week2_liters": 980.0,
      "week3_liters": 905.0,
      "week4_liters": 951.0,
      "months_available": 3,
      "liters_month1": 3600.0,
      "liters_month2": 3700.0,
      "liters_month3": 3550.0,
      "cost_month1": 33120.0,
      "cost_month2": 34040.0,
      "cost_month3": 32660.0
    },
    {
      "vehicle_id": "V-002",
      "vehicle_type": "Delivery Van",
      "km_driven": 6900,
      "liters_consumed": 828.0,
      "price_per_liter": 9.2,
      "fuel_cost_egp": 7617.6,
      "week1_liters": 210.0,
      "week2_liters": 205.0,
      "week3_liters": 200.0,
      "week4_liters": 213.0,
      "months_available": 3,
      "liters_month1": 800.0,
      "liters_month2": 790.0,
      "liters_month3": 810.0,
      "cost_month1": 7360.0,
      "cost_month2": 7268.0,
      "cost_month3": 7452.0
    },
    {
      "vehicle_id": "V-003",
      "vehicle_type": "Sedan",
      "km_driven": 1200,
      "liters_consumed": 96.0,
      "price_per_liter": 9.2,
      "fuel_cost_egp": 883.2,
      "week1_liters": 30.0,
      "week2_liters": 24.0,
      "week3_liters": 22.0,
      "week4_liters": 20.0,
      "months_available": 3,
      "liters_month1": 330.0,
      "liters_month2": 320.0,
      "liters_month3": 340.0,
      "cost_month1": 3036.0,
      "cost_month2": 2944.0,
      "cost_month3": 3128.0
    }
  ],
  "maintenance": [
    {
      "vehicle_id": "V-001",
      "vehicle_type": "Heavy Truck",
      "date": "2026-04-05",
      "category": "Routine Service",
      "description": "Routine Service — Mercedes Actros",
      "cost_egp": 420.0,
      "downtime_hours": 3.0,
      "status": "Completed"
    },
    {
      "vehicle_id": "V-002",
      "vehicle_type": "Delivery Van",
      "date": "2026-04-11",
      "category": "Tires & Suspension",
      "description": "Tires & Suspension — Ford Transit",
      "cost_egp": 760.0,
      "downtime_hours": 5.0,
      "status": "Completed"
    },
    {
      "vehicle_id": "V-003",
      "vehicle_type": "Sedan",
      "date": "2026-04-18",
      "category": "Emergency & Mechanical Repair",
      "description": "Emergency & Mechanical Repair — Toyota Camry",
      "cost_egp": 2100.0,
      "downtime_hours": 26.0,
      "status": "In Progress"
    }
  ],
  "trips": [
    {
      "trip_id": "TR-0001",
      "vehicle_id": "V-001",
      "driver_name": "Ahmed Hassan",
      "date": "2026-04-03",
      "origin": "Cairo",
      "destination": "Alexandria",
      "distance_km": 220.0,
      "status": "Delivered",
      "delay_minutes": 0,
      "cost_egp": 528.0
    },
    {
      "trip_id": "TR-0002",
      "vehicle_id": "V-001",
      "driver_name": "Ahmed Hassan",
      "date": "2026-04-07",
      "origin": "Cairo",
      "destination": "Suez",
      "distance_km": 130.0,
      "status": "Delayed",
      "delay_minutes": 45,
      "cost_egp": 312.0
    },
    {
      "trip_id": "TR-0003",
      "vehicle_id": "V-002",
      "driver_name": "Mohamed Saleh",
      "date": "2026-04-09",
      "origin": "Giza",
      "destination": "Tanta",
      "distance_km": 95.0,
      "status": "Delivered",
      "delay_minutes": 0,
      "cost_egp": 228.0
    },
    {
      "trip_id": "TR-0004",
      "vehicle_id": "V-002",
      "driver_name": "Mohamed Saleh",
      "date": "2026-04-15",
      "origin": "Giza",
      "destination": "Mansoura",
      "distance_km": 120.0,
      "status": "Cancelled",
      "delay_minutes": 0,
      "cost_egp": 288.0
    },
    {
      "trip_id": "TR-0005",
      "vehicle_id": "V-001",
      "driver_name": "Khaled Ibrahim",
      "date": "2026-04-21",
      "origin": "Cairo",
      "destination": "Ismailia",
      "distance_km": 140.0,
      "status": "Delivered",
      "delay_minutes": 0,
      "cost_egp": 336.0
    }
  ],
  "cost_summary": {
    "total_tco_egp": 118000.0,
    "fuel_cost_egp": 43240.0,
    "maintenance_cost_egp": 3280.0,
    "fines_cost_egp": 1500.0,
    "fixed_cost_egp": 69980.0,
    "total_km_driven": 19900,
    "tco_last_month": 112000.0,
    "fuel_last_month": 41000.0,
    "maintenance_last_month": 3000.0,
    "km_last_month": 21900,
    "depreciation_egp": 21000.0,
    "insurance_egp": 4200.0,
    "salaries_egp": 18000.0,
    "other_fixed_egp": 26780.0
  }
}
```