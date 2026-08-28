"""
Test de fumée du batch_engine sur des données réelles, plusieurs joueurs.
Usage : place ton fichier .xlsx de profilage dans ce dossier, puis :
    python smoke_test_batch.py
"""
import pandas as pd

from data_loader import load_and_clean_excel, find_column, locate_excel_file
from config import GROUPES_PREPA, GROUPES_KINE
from batch_engine import BatchConfig, build_batch_zip

path = locate_excel_file(".")
assert path is not None, "Le fichier Excel n'a pas été trouvé automatiquement !"
df = load_and_clean_excel(path)

col_session = "Session" if "Session" in df.columns else None
sessions = sorted(df[col_session].dropna().unique().tolist()) if col_session else [None]
sel_session = sessions[-1]
df_session = df[df[col_session] == sel_session] if col_session else df

teams = sorted(df_session["Equipe"].dropna().astype(str).unique().tolist())
print("Équipes disponibles :", teams)

batch_teams = teams[:1]
batch_players = sorted(df_session[df_session["Equipe"].isin(batch_teams)]["Joueur"].dropna().unique().tolist())
extra_pool = sorted(set(df_session["Joueur"].dropna().unique()) - set(batch_players))
extra = extra_pool[:1]
all_players = batch_players + extra
print(f"Équipes du lot : {batch_teams} | +{len(extra)} joueur(s) ajouté(s) | total = {len(all_players)} joueurs")

selected_metrics = set()
for grp, lbls in {**GROUPES_PREPA, **GROUPES_KINE}.items():
    for l in lbls:
        c = find_column(df_session, l)
        if c is not None:
            selected_metrics.add(l)

cfg = BatchConfig(
    report_mode="Commun (Complet)", selected_metrics=selected_metrics, use_relative={},
    niveau_ref="Équipe", age_range=(10, 40), col_age="Age", context_test="Pré-saison", export_pdf=True,
)


def progress(done, total, name):
    print(f"  [{done}/{total}] {name}")


zip_bytes, errors = build_batch_zip(
    all_players, df_session, df, cfg, {},
    key_suffix_fn=lambda pl: f"{pl}_{sel_session}",
    progress_callback=progress,
    photo_lookup_fn=lambda pl: "",
)

print("\nErreurs :", errors if errors else "aucune")
print("Taille du zip :", len(zip_bytes), "bytes")

import zipfile
import io
zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
names = zf.namelist()
print(f"Fichiers dans le zip ({len(names)}) :")
for n in names:
    print(" -", n, f"({zf.getinfo(n).file_size} bytes)")

assert len(names) == len(all_players), "Un rapport par joueur attendu"

print("\n✅ BATCH SMOKE TEST OK")
