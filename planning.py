# -*- coding: utf-8 -*-
"""
planning.py
============
Génération du "planning type" hebdomadaire d'un joueur, organisé autour du
jour de match (Match Day) : MD-2, MD-1, MD, MD+1, MD+2, MD+3, chacun
découpé en Matin / Après-midi.

Ce planning est rempli manuellement par le staff (aucun calcul automatique
ici, contrairement au reste de l'app) : ce module ne fait que structurer et
mettre en forme visuellement ce que le staff a saisi.

DESIGN
------
Le rendu est volontairement différent du rapport de profilage (grille
hebdomadaire en paysage plutôt que fiche en portrait), car l'usage est
différent : un coup d'œil rapide sur toute la semaine plutôt qu'une lecture
détaillée page par page. La charte graphique (rouge/blanc Stade de Reims,
logo) est reprise à l'identique — le thème visuel plus poussé sera affiné
plus tard sur indication du staff.
"""
from __future__ import annotations

JOURS = ["MD-2", "MD-1", "MD", "MD+1", "MD+2", "MD+3"]
MOMENTS = ["Matin", "Après-midi"]

# Catégories d'activités proposées. Couleurs choisies pour rester lisibles
# sur fond blanc et cohérentes avec la charte SDR (rouge = coeur du métier
# terrain, le reste décliné en teintes distinctes pour un repérage rapide).
# NOTE : pas d'emoji ici — les polices emoji couleur ne sont pas disponibles
# sur un serveur de rendu PDF (WeasyPrint), ce qui produisait des icônes
# cassées/illisibles. La distinction se fait uniquement par couleur + texte,
# via une puce ronde dessinée en CSS (fiable partout, y compris à l'impression).
CATEGORIES = {
    "Entraînement": {"color": "#D71920"},
    "Renforcement": {"color": "#F39C12"},
    "Soins": {"color": "#3498DB"},
    "Protocole Récup": {"color": "#1ABC9C"},
    "Prévention": {"color": "#27AE60"},
    "Vidéo / Analyse": {"color": "#8E44AD"},
    "Nutrition": {"color": "#B8860B"},
    "Repos": {"color": "#7F8C8D"},
}

SDR_RED = "#D71920"
DARK = "#222222"


def empty_planning() -> dict:
    """Structure vide : un slot {tags: [], note: ''} par jour x moment."""
    return {jour: {moment: {"tags": [], "note": ""} for moment in MOMENTS} for jour in JOURS}


def _tag_pill_html(tag: str) -> str:
    meta = CATEGORIES.get(tag, {"color": "#999"})
    dot = f'<span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:{meta["color"]}; margin-right:5px; vertical-align:middle;"></span>'
    return (
        f'<span style="display:inline-block; background:{meta["color"]}18; '
        f'color:{meta["color"]}; border:1px solid {meta["color"]}55; border-radius:12px; padding:3px 9px 3px 7px; '
        f'font-size:8pt; font-weight:700; margin:2px 3px 0 0; white-space:nowrap;">{dot}<span style="vertical-align:middle;">{tag}</span></span>'
    )


def _slot_html(slot: dict) -> str:
    tags = slot.get("tags", [])
    note = (slot.get("note") or "").strip()
    if not tags and not note:
        return '<div style="color:#ccc; font-size:8pt; font-style:italic; padding:6px 0;">—</div>'
    pills = "".join(_tag_pill_html(t) for t in tags)
    note_html = f'<div style="font-size:7.5pt; color:#555; margin-top:5px; line-height:1.3;">{note}</div>' if note else ""
    return f'<div style="min-height:40px;">{pills}{note_html}</div>'


def _day_column_html(jour: str, data: dict) -> str:
    is_match_day = jour == "MD"
    header_bg = SDR_RED if is_match_day else "#2c2c2c"
    match_badge = '<div style="font-size:6.5pt; font-weight:700; letter-spacing:0.5px; opacity:0.85;">JOUR DE MATCH</div>' if is_match_day else ""
    matin = _slot_html(data.get("Matin", {}))
    aprem = _slot_html(data.get("Après-midi", {}))
    return f"""
    <div style="flex:1; min-width:0; border:1px solid #e5e5e5; border-radius:10px; overflow:hidden; background:#fff; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
        <div style="background:{header_bg}; color:#fff; text-align:center; padding:8px 4px;">
            <div style="font-weight:900; font-size:12pt; letter-spacing:0.5px;">{jour}</div>
            {match_badge}
        </div>
        <div style="padding:10px 8px; border-bottom:1px dashed #eee;">
            <div style="font-size:7pt; font-weight:800; color:#999; text-transform:uppercase; margin-bottom:4px;">Matin</div>
            {matin}
        </div>
        <div style="padding:10px 8px;">
            <div style="font-size:7pt; font-weight:800; color:#999; text-transform:uppercase; margin-bottom:4px;">Après-midi</div>
            {aprem}
        </div>
    </div>
    """


def _legend_html() -> str:
    items = "".join(_tag_pill_html(t) for t in CATEGORIES)
    return f"""
    <div style="margin-top:16px; padding:10px 14px; background:#f8f9fa; border:1px solid #eee; border-radius:8px;">
        <div style="font-size:7pt; font-weight:800; color:#888; text-transform:uppercase; margin-bottom:6px;">Légende</div>
        <div>{items}</div>
    </div>
    """


def build_planning_html(player_name: str, poste: str, planning_data: dict, logo_b64: str = "",
                         logo_ext: str = "png", week_label: str = "") -> str:
    """Construit le HTML complet (paysage A4) du planning hebdomadaire d'un joueur."""
    columns_html = "".join(_day_column_html(j, planning_data.get(j, {})) for j in JOURS)
    logo_img = f'<img src="data:image/{logo_ext};base64,{logo_b64}" style="height:70px;">' if logo_b64 else ""
    week_html = f'<div style="font-size:9pt; color:#888; margin-top:2px;">{week_label}</div>' if week_label else ""

    return f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        body {{ font-family: 'Helvetica','Arial',sans-serif; background:#eee; margin:0; padding:0;
                -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        .container {{ background:#fff; max-width:297mm; margin:10px auto; padding:12mm; box-sizing:border-box;
                      box-shadow:0 0 10px rgba(0,0,0,0.1); }}
        @media print {{
            @page {{ size: A4 landscape; margin: 10mm; }}
            body {{ background:#fff; }}
            .container {{ margin:0; box-shadow:none; max-width:100%; padding:0; }}
        }}
    </style>
    </head><body>
    <div class="container">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:3px solid {SDR_RED}; padding-bottom:12px; margin-bottom:16px;">
            <div>
                <div style="font-size:9pt; color:#888; font-weight:700; text-transform:uppercase; letter-spacing:1px;">Département Performance</div>
                <h1 style="margin:2px 0 0 0; color:{SDR_RED}; font-size:22pt; text-transform:uppercase; font-weight:900;">Planning Type Hebdomadaire</h1>
                <div style="font-size:12pt; font-weight:800; color:{DARK}; margin-top:4px;">{player_name} <span style="color:#999; font-weight:600;">— {poste}</span></div>
                {week_html}
            </div>
            {logo_img}
        </div>
        <div style="display:flex; gap:10px;">
            {columns_html}
        </div>
        {_legend_html()}
        <div style="margin-top:18px; font-size:7pt; color:#aaa; text-align:right;">Document confidentiel — usage interne club</div>
    </div>
    </body></html>
    """


def build_kpi_department_plan_html(logo_b64: str = "", logo_ext: str = "png") -> str:
    """
    Construit le document (A4 paysage) du plan hebdomadaire du département
    performance par groupe de KPI — le tableau "GROUPES DE TRAVAIL" du
    document de réflexion individualisation, tel quel (indépendant d'un
    joueur en particulier, à la différence de build_planning_html). Sert de
    document de référence pour le staff, téléchargeable en HTML/PDF.
    """
    from config import KPI_WEEKLY_PLAN, KPI_WEEKLY_PLAN_DAYS_ORDER

    kpi_groups = list(KPI_WEEKLY_PLAN.keys())
    short_labels = {
        "Développement du RFD": "RFD",
        "Développement de la force": "Force",
        "Prévention des blessures": "Prévention",
        "Développement de la répétition des efforts": "Répétition des efforts",
        "Optimisation de la composition corporelle": "Composition corporelle",
    }

    header_cells = "".join(
        f'<th style="padding:10px 12px; text-align:left; background:{SDR_RED}; color:#fff; font-size:9pt; text-transform:uppercase;">{short_labels.get(g, g)}</th>'
        for g in kpi_groups
    )
    rows_html = ""
    for day in KPI_WEEKLY_PLAN_DAYS_ORDER:
        is_match_day = day == "MD"
        row_bg = "#fff5f5" if is_match_day else ("#fafafa" if KPI_WEEKLY_PLAN_DAYS_ORDER.index(day) % 2 else "#fff")
        cells = "".join(
            f'<td style="padding:10px 12px; font-size:8.5pt; color:#333; border-bottom:1px solid #eee;">{KPI_WEEKLY_PLAN[g].get(day, "-")}</td>'
            for g in kpi_groups
        )
        rows_html += (
            f'<tr style="background:{row_bg};">'
            f'<td style="padding:10px 12px; font-weight:900; color:{SDR_RED if is_match_day else DARK}; border-bottom:1px solid #eee; white-space:nowrap;">{day}</td>'
            f'{cells}</tr>'
        )

    logo_img = f'<img src="data:image/{logo_ext};base64,{logo_b64}" style="height:70px;">' if logo_b64 else ""

    return f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        body {{ font-family: 'Helvetica','Arial',sans-serif; background:#eee; margin:0; padding:0;
                -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        .container {{ background:#fff; max-width:297mm; margin:10px auto; padding:12mm; box-sizing:border-box;
                      box-shadow:0 0 10px rgba(0,0,0,0.1); }}
        table {{ width:100%; border-collapse:collapse; }}
        @media print {{
            @page {{ size: A4 landscape; margin: 10mm; }}
            body {{ background:#fff; }}
            .container {{ margin:0; box-shadow:none; max-width:100%; padding:0; }}
        }}
    </style>
    </head><body>
    <div class="container">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:3px solid {SDR_RED}; padding-bottom:12px; margin-bottom:20px;">
            <div>
                <div style="font-size:9pt; color:#888; font-weight:700; text-transform:uppercase; letter-spacing:1px;">Département Performance</div>
                <h1 style="margin:2px 0 0 0; color:{SDR_RED}; font-size:22pt; text-transform:uppercase; font-weight:900;">Plan Hebdomadaire par Groupe de KPI</h1>
                <div style="font-size:9pt; color:#888; margin-top:4px;">Individualisation — semaine type autour du jour de match</div>
            </div>
            {logo_img}
        </div>
        <table>
            <tr><th style="padding:10px 12px; text-align:left; background:#2c2c2c; color:#fff; font-size:9pt; text-transform:uppercase;">Jour</th>{header_cells}</tr>
            {rows_html}
        </table>
        <div style="margin-top:16px; font-size:7.5pt; color:#999; font-style:italic;">
            MD = jour de match. MD+4 et MD-3 correspondent au même jour du cycle hebdomadaire (semaine à 1 match).
        </div>
        <div style="margin-top:18px; font-size:7pt; color:#aaa; text-align:right;">Document confidentiel — usage interne club</div>
    </div>
    </body></html>
    """
