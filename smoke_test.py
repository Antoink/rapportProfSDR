"""
Test de fumée : simule le pipeline complet de génération de rapport
(chargement -> nettoyage -> calculs -> HTML -> PDF) pour un joueur réel,
sans passer par l'UI Streamlit.

Usage : place ton fichier .xlsx de profilage dans ce dossier, puis :
    python smoke_test.py
"""
import pandas as pd

from data_loader import load_and_clean_excel, find_column, clean_numeric_value, locate_excel_file
from stats_engine import calculate_percentile, calculate_zscore, get_value_for_metric, compute_group_zscores
from config import COL_MAPPING, GROUPES_PREPA, GROUPES_KINE
from suggestions import get_theme_suggestions_advanced
from report_prepa import build_prepa_report
from report_kine import build_kine_report
from pdf_export import html_to_pdf_bytes, is_pdf_export_available

path = locate_excel_file(".")
print("Fichier détecté :", path)
assert path is not None, "Le fichier Excel n'a pas été trouvé automatiquement !"

df = load_and_clean_excel(path)
print("Shape après nettoyage :", df.shape)

teams = sorted(df["Equipe"].dropna().astype(str).unique().tolist())
team = "PRO" if "PRO" in teams else teams[0]
df_team = df[df["Equipe"] == team]
player = df_team["Joueur"].dropna().iloc[0]
row = df_team[df_team["Joueur"] == player].iloc[0]
print("Joueur test :", player, "| Équipe :", team)

df_ref = df[df["Equipe"] == team]
print("n_ref =", len(df_ref))

selected_metrics = set()
for grp, lbls in {**GROUPES_PREPA, **GROUPES_KINE}.items():
    for l in lbls:
        c = find_column(df, l)
        if c and pd.notna(row.get(c)):
            selected_metrics.add(l)
print("Nb métriques sélectionnées auto :", len(selected_metrics))

use_relative = {}
staff_evals = {}

comp_zscores = compute_group_zscores(df, df_ref, row, GROUPES_PREPA, selected_metrics, use_relative, find_column)
print("Z-scores composites (prepa) :", comp_zscores)

themes = get_theme_suggestions_advanced(row, df)
print("Thèmes suggérés (indicatif) :", [(t["etat"], t["qualite"], t["zone"]) for t in themes])

anthro = {"Age": int(clean_numeric_value(row.get("Age")) or 0), "Taille": row.get("Taille (cm)"), "Poids": row.get("Poids (kg)")}

radar_labels = ["CMJ 2JB", "Peak Force CMJ", "Vmax"]
radar_values = [70, 55, 80]

html_prepa = build_prepa_report(
    player, row, df_ref, df, row.get(COL_MAPPING["Poste"], "-"), row.get("Latéralité", "-"), anthro,
    selected_metrics, use_relative, radar_labels, radar_values,
    themes, "Bonne détente", "Vitesse à travailler", "Squat + gainage", "Sprints courts",
    "", "", "png", staff_evals, "Pré-saison", None, "01/09/2026", "20/08/2026", "Pré-saison",
    f"Équipe {team} (n={len(df_ref)})", comp_zscores, GROUPES_PREPA,
)
print("HTML prepa généré :", len(html_prepa), "caractères")
assert "<!DOCTYPE html>" in html_prepa
assert player in html_prepa

html_kine = build_kine_report(
    player, row, df_ref, df, row.get(COL_MAPPING["Poste"], "-"), row.get("Latéralité", "-"), anthro,
    selected_metrics, use_relative, ["Sit And Reach"], [90],
    themes, "Bonne détente", "Vitesse à travailler", "Renfo excentrique", "",
    "", "", "png", staff_evals, "Pré-saison", None, "01/09/2026", "20/08/2026", "Pré-saison",
    f"Équipe {team} (n={len(df_ref)})", comp_zscores, "pubalgie ischio", {"frappe": "D", "appui": "G"}, [85],
)
print("HTML kine généré :", len(html_kine), "caractères")
assert "<!DOCTYPE html>" in html_kine

print("PDF disponible :", is_pdf_export_available())
if is_pdf_export_available():
    pdf_bytes = html_to_pdf_bytes(html_prepa)
    with open("/tmp/rapport_test_prepa.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF généré :", len(pdf_bytes), "bytes -> /tmp/rapport_test_prepa.pdf")

    pdf_bytes_kine = html_to_pdf_bytes(html_kine)
    with open("/tmp/rapport_test_kine.pdf", "wb") as f:
        f.write(pdf_bytes_kine)
    print("PDF kine généré :", len(pdf_bytes_kine), "bytes -> /tmp/rapport_test_kine.pdf")

print("\n✅ SMOKE TEST OK")
