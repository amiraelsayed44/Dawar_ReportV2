
OUTPUT_PATH = "Fleet_Management_Report.pdf"
import os
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo_final.png")

DRIVER_SCORE_EXCELLENT = 85
DRIVER_SCORE_AVERAGE   = 70

CLR = {
    # ── Page / Section Backgrounds ──────────────────────────────────────────
    "bg_page":       "#F7F5F0",   
    "bg_header":     "#1C3226",   
    "bg_card":       "#EEF2EB",   
    "bg_card2":      "#E4EBE0",   
    "bg_table_hdr":  "#1C3226",   
    "bg_table_row":  "#F2F5EF",   
    "bg_cover_band": "#1C3226",   

    # ── Brand Greens ─────────────────────────────────────────────────────────
    "green_primary": "#2D6A4F",   
    "green_bright":  "#40916C",   
    "green_dark":    "#1B4332",   
    "green_light":   "#D8EDDF",   
    "green_mid":     "#95D5B2",   
    "green_muted":   "#B7D4C0",  

    # ── Accent Gold ──────────────────────────────────────────────────────────
    "gold":          "#D4A017",   
    "gold_light":    "#FFF3CD",   

    # ── Status Colors ────────────────────────────────────────────────────────
    "status_active": "#2D6A4F",
    "status_maint":  "#C07820",
    "status_idle":   "#7A8E99",

    # ── Score Colors ─────────────────────────────────────────────────────────
    "score_great":   "#2D6A4F",   
    "score_avg":     "#C07820",   
    "score_poor":    "#B5342A",   
    # ── Text ─────────────────────────────────────────────────────────────────
    "text_black":    "#1A1A1A",   
    "text_dark":     "#2C2C2C",   
    "text_mid":      "#4A5240",   
    "text_muted":    "#7A8875",  
    "text_on_dark":  "#F0F4EE",   
    "text_green":    "#1B4332",   

    # ── Borders & Lines ──────────────────────────────────────────────────────
    "bg_insight":    "#EAF4EE",   
    "border":        "#C9DEC9",   
    "border_dark":   "#40916C",   
    "border_black":  "#1C3226",   
}
