import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
import os
import re
import unicodedata
import uuid
import json
from io import BytesIO
from math import pi
from datetime import datetime
from github import Github, GithubException

GITHUB_FILE_PATH = "profiling_comments.json"

def get_github_repo():
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo_name = st.secrets.get("GITHUB_REPO")
        if not token or not repo_name:
            return None
        g = Github(token)
        return g.get_repo(repo_name)
    except Exception:
        return None

def load_profiling_data():
    # En local sans secret, on se rabat sur le fichier local
    repo = get_github_repo()
    if repo:
        try:
            contents = repo.get_contents(GITHUB_FILE_PATH)
            return json.loads(contents.decoded_content.decode('utf-8'))
        except GithubException as e:
            if e.status == 404:
                return {}
            st.warning(f"Impossible de lire le fichier depuis GitHub : {e}")
            return {}
    elif os.path.exists(GITHUB_FILE_PATH):
        try:
            with open(GITHUB_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_profiling_data(data, key_suffix):
    repo = get_github_repo()
    content_str = json.dump_s(data) if hasattr(json, 'dump_s') else json.dumps(data, ensure_ascii=False, indent=4)
    commit_message = f"Mise à jour profilage : {key_suffix} ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
    
    if repo:
        try:
            try:
                contents = repo.get_contents(GITHUB_FILE_PATH)
                repo.update_file(contents.path, commit_message, content_str, contents.sha)
            except GithubException as e:
                if e.status == 404:
                    repo.create_file(GITHUB_FILE_PATH, commit_message, content_str)
                else:
                    raise e
            return True
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde sur GitHub : {e}")
            return False
    else:
        # Fallback local
        with open(GITHUB_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(content_str)
        return True

st.set_page_config(page_title="Rapport de Profilage", layout="wide")

st.title("Rapport de Profilage Individuel")
# MODIFICATION: Ajout du mode "Commun (Complet)"
report_mode = st.radio("Type de rapport", ["Préparation Physique", "Kiné / Prévention", "Commun (Complet)"], horizontal=True)

SDR_RED = "#D71920"
GREEN = "#27AE60"
ORANGE = "#F39C12"
BLUE_ELITE = "#00E5FF"
DARK = "#333333"

COL_MAPPING = {
    "Joueur": "Joueur", "Equipe": "Equipe", "Age": "Age",
    "Poids": "Poids (kg)", "Taille": "Taille (cm)", "Masse Grasse": "Masse grasse",
    "Poste": "Position", "Latéralité": "Latéralité",
    "Sit And Reach": "Sit and reach", "Knee To Wall (D)": "Knee to wall D", "Knee To Wall (G)": "Knee to wall G",
    "Adducteurs (G)": "Adducteur G", "Adducteurs (D)": "Adducteur D",
    "Somme ADD": "Somme ADD", "Ratio Squeeze": "Ratio Squeeze (ADD/ABD)",
    "Abducteurs (G)": "Abducteur G", "Abducteurs (D)": "Abducteur D", "Somme ABD": "Somme ABD",
    "Nordic Ischio (G)": "Nordic G", "Nordic Ischio (D)": "Nordic D",
    "Inverseur (G)": "Inverseur G", "Inverseur (D)": "Inverseur D",
    "Everseur (G)": "Everseur G", "Everseur (D)": "Everseur D",
    "Endurance Heel Raise (G)": "Endurance Heel Raise G", "Endurance Heel Raise (D)": "Endurance Heel Raise D",
    "CMJ 2JB": "CMJ 2JB", "Peak Force CMJ": "Peak Force CMJ", "RFD CMJ": "RFD CMJ", "RSI CMJ": "RSI", "Drop jump": "Drop jump",
    "Wattbike (6s)": "Wattbike 6s (W)", "Squat belt (N)": "Squat belt (N)",
    "VMA": "VMA", "FC": "FC", "SV1": "SV1", "SV2": "SV2", "Test 1km (s)": "Test 1km (s)",
    "Temps sur 10m": "Temps sur 10m",
    "Amax": "Amax", "Dmax": "Dmax", "Vmax": "Vmax",
    "Distance HSR": "Distance HSR", "Distance Totale": "Distance totale", "Distance Sprint (92% Vimax)": "Distance Sprint (92% Vimax)",
    "Q Conc 60° (G)": "Q G conc 60°/s", "Q Conc 60° (D)": "Q Dt conc 60°/s",
    "Q Conc 240° (G)": "Q G conc 240°/s", "Q Conc 240° (D)": "Q Dt conc 240°/s",
    "IJ Conc 60° (G)": "IJ G conc 60°/s", "IJ Conc 60° (D)": "IJ Dt conc 60°/s",
    "IJ Conc 240° (G)": "IJ G conc 240°/s", "IJ Conc 240° (D)": "IJ Dt conc 240°/s",
    "IJ Exc 30° (G)": "IJ G Exc 30°/s", "IJ Exc 30° (D)": "IJ Dt exc 30°/s",
    "Ratio Mixte (G)": "Ratio Mixte G", "Ratio Mixte (D)": "Ratio Mixte D"
}

GROUPES_PREPA = {
    "Puissance": ["Wattbike (6s)"],
    "Force": ["Squat belt (N)"],
    "Saut": ["CMJ 2JB", "Peak Force CMJ", "RFD CMJ", "RSI CMJ", "Drop jump"],
    "Aérobie": ["VMA", "FC", "SV1", "SV2", "Test 1km (s)"],
    "Vitesse / GPS": ["Temps sur 10m", "Amax", "Dmax", "Vmax", "Distance HSR", "Distance Totale", "Distance Sprint (92% Vimax)"],
}

GROUPES_KINE = {
    "Mobilité": [
        "Sit And Reach", "Knee To Wall (G)", "Knee To Wall (D)"
    ],
    "Adducteurs & Abducteurs": [
        "Adducteurs (G)", "Adducteurs (D)", "Somme ADD", 
        "Abducteurs (G)", "Abducteurs (D)", "Somme ABD",
        "Ratio Squeeze"
    ],
    "Ischio-Jambiers": [
        "Nordic Ischio (G)", "Nordic Ischio (D)"
    ],
    "Mollets": [
        "Endurance Heel Raise (G)", "Endurance Heel Raise (D)"
    ],
    "Pieds": [
        "Inverseur (G)", "Inverseur (D)", "Everseur (G)", "Everseur (D)"
    ],
    "Biodex - Concentrique": [
        "Q Conc 60° (G)", "Q Conc 60° (D)", "Q Conc 240° (G)", "Q Conc 240° (D)",
        "IJ Conc 60° (G)", "IJ Conc 60° (D)", "IJ Conc 240° (G)", "IJ Conc 240° (D)"
    ],
    "Biodex - Excentrique": [
        "IJ Exc 30° (G)", "IJ Exc 30° (D)", "Ratio Mixte (G)", "Ratio Mixte (D)"
    ]
}

# MODIFICATION: Gérer GROUPES pour le mode Commun
if report_mode == "Préparation Physique":
    GROUPES = GROUPES_PREPA
elif report_mode == "Kiné / Prévention":
    GROUPES = GROUPES_KINE
else:
    GROUPES = {**GROUPES_PREPA, **GROUPES_KINE}

KINE_LABELS = [
    "Q Conc 60° (G)", "Q Conc 60° (D)", "Q Conc 240° (G)", "Q Conc 240° (D)",
    "IJ Conc 60° (G)", "IJ Conc 60° (D)", "IJ Conc 240° (G)", "IJ Conc 240° (D)",
    "IJ Exc 30° (G)", "IJ Exc 30° (D)", "Nordic Ischio (G)", "Nordic Ischio (D)",
    "Adducteurs (G)", "Adducteurs (D)", "Abducteurs (G)", "Abducteurs (D)",
    "Inverseur (G)", "Inverseur (D)", "Everseur (G)", "Everseur (D)"
]

NORMES_ABSOLUES = {
    "VMA": 16, "FC": 180, "SV1": 14, "SV2": 16, "Vmax": 32, "CMJ 2JB": 40, "Drop jump": 30,
    "Knee To Wall": 9, "Sit And Reach": 20, "Distance HSR": 800,
    "Distance Totale": 8000, "Amax": 5, "Dmax": 5, "Distance Sprint (92% Vimax)": 60,
    "Somme ADD": 35, "Somme ABD": 35, "Ratio Squeeze": [0.90, 1.10],
    "Adducteur": 26, "Abducteur": 26, "Nordic": 36, 
    "Inverseur": 10, "Everseur": 10, "Endurance Heel Raise": 15,
    "Wattbike": 1100, "Squat belt": 1500, "Temps sur 10m": 1.90, "Test 1km (s)": 220,
    "Peak Force CMJ": 2000, "RFD CMJ": 10000, "RSI": 2.5
}

NORMES_RELATIVES = {
    "Wattbike": 15.0, # W/kg
    "Squat belt": 20.0, # N/kg
    "Peak Force CMJ": 25.0, # N/kg
    "Adducteur": 0.2, # N/kg
    "Abducteur": 0.2, # N/kg
    "Nordic": 0.08, # N/kg
    "Inverseur": 0.2, # N/kg
    "Everseur": 0.18 # N/kg
}

REPORT_NORMES = {**NORMES_ABSOLUES, **NORMES_RELATIVES}

UNITS = {
    "Knee To Wall (G)": "cm", "Knee To Wall (D)": "cm", "Sit And Reach": "cm",
    "Somme ADD": "Kg", "Somme ABD": "Kg", "Ratio Squeeze": "",
    "Adducteurs (G)": "Kg", "Adducteurs (D)": "Kg", "Abducteurs (G)": "Kg", "Abducteurs (D)": "Kg",
    "Nordic Ischio (G)": "Kg", "Nordic Ischio (D)": "Kg",
    "Inverseur (G)": "Kg", "Inverseur (D)": "Kg",
    "Everseur (G)": "Kg", "Everseur (D)": "Kg",
    "Endurance Heel Raise (G)": "reps", "Endurance Heel Raise (D)": "reps",
    "Q Conc 60° (G)": "Nm", "Q Conc 60° (D)": "Nm", "Q Conc 240° (G)": "Nm", "Q Conc 240° (D)": "Nm",
    "IJ Conc 60° (G)": "Nm", "IJ Conc 60° (D)": "Nm", "IJ Conc 240° (G)": "Nm", "IJ Conc 240° (D)": "Nm",
    "IJ Exc 30° (G)": "Nm", "IJ Exc 30° (D)": "Nm",
    "CMJ 2JB": "cm", "Peak Force CMJ": "N", "RFD CMJ": "N/s", "RSI CMJ": "", "Drop jump": "cm",
    "Wattbike (6s)": "W", "Squat belt (N)": "N",
    "VMA": "km/h", "Vmax": "km/h", "Temps sur 10m": "s", "Test 1km (s)": "s", "SV1": "km/h", "SV2": "km/h", "FC": "bpm",
    "Distance Totale": "m", "Distance HSR": "m", "Distance Sprint (92% Vimax)": "m", "Amax": "m/s²", "Dmax": "m/s²",
    "Ratio Mixte (G)": "", "Ratio Mixte (D)": ""
}

ETATS_ACTIONS = ["En manque de", "Renforcement de", "Maintien de", "Prévention de", "Rééquilibrage de"]
QUALITES_PHYSIQUES = ["Force", "Mobilité", "Puissance", "Vitesse", "Endurance", "Stabilité", "Explosivité", "Réactivité", "Blessure (Ratio)"]
ZONES_CIBLEES = [
    "Pied / Orteil", "Cheville", "Mollets", "Genou", 
    "Ischio-jambiers", "Quadriceps", "Adducteurs", "Abducteurs", 
    "Hanche", "Hanche / Pubis", "Fessiers", "Bassin", 
    "Tronc / Gainage", "Dos / Lombaires", "Cervicales",
    "Épaule", "Coude", "Poignet / Main",
    "Membre supérieur", "Membre inférieur", 
    "Chaîne postérieure", "Chaîne antérieure", "Chaîne croisée", "Global"
]
THEME_MAPPING = {
    "CMJ 2JB": ("Puissance", "Membre inférieur"), "Peak Force CMJ": ("Force", "Membre inférieur"),
    "RFD CMJ": ("Explosivité", "Membre inférieur"), "RSI CMJ": ("Réactivité", "Membre inférieur"),
    "Drop jump": ("Réactivité", "Membre inférieur"), "Squat belt (N)": ("Force", "Membre inférieur"),
    "Wattbike (6s)": ("Puissance", "Membre inférieur"), "Vmax": ("Vitesse", "Global"),
    "Somme ADD": ("Force", "Chaîne antérieure"), "Somme ABD": ("Force", "Chaîne antérieure"),
    "Sit And Reach": ("Mobilité", "Chaîne postérieure"), "Knee To Wall (D)": ("Mobilité", "Cheville"), "Knee To Wall (G)": ("Mobilité", "Cheville"),
}

def remove_accents(s):
    if not isinstance(s, str): return str(s)
    return "".join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def clean_numeric_value(val, col_name=""):
    if pd.isna(val) or val == "" or val == "-": return None
    try:
        if isinstance(val, (int, float)): 
            v = float(val)
        else:
            val_str = str(val).replace(',', '.')
            m = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
            v = float(m.group()) if m else None
        
        if v == 0.0 and col_name and not any(k in str(col_name).lower() for k in ['knee', 'sit']):
            return None
        return v
    except Exception:
        return None

def find_column(df, label):
    mapped = COL_MAPPING.get(label)
    if mapped and mapped in df.columns: return mapped
    label_clean = remove_accents(label).lower().strip().replace("(g)", "").replace("(d)", "").strip()
    for c in df.columns:
        if label_clean in remove_accents(str(c)).lower().strip():
            return c
    return None

def is_inverted(label):
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', '1km']
    return any(k in str(label).lower() for k in keywords)

@st.cache_data
def get_column_series(df, col, use_rel=False):
    if col not in df.columns: return None
    series = pd.to_numeric(df[col], errors='coerce')
    
    if col and not any(k in col.lower() for k in ['knee', 'sit']):
        series = series.replace(0.0, np.nan)
        
    if use_rel and "Poids (kg)" in df.columns:
        weights = pd.to_numeric(df["Poids (kg)"], errors='coerce')
        series = series / weights
    return series.dropna()

def calculate_percentile(df, col, value, use_rel=False):
    if col is None or value is None: return None, None
    series = get_column_series(df, col, use_rel)
    if series is None or series.empty: return None, None
    if "Ratio Squeeze" in col:
        d_all = (series - 1.0).abs()
        d_val = abs(value - 1.0)
        pct = (d_all >= d_val).mean() * 100
        return series.mean(), pct
    inverted = is_inverted(col)
    pct = (series >= value).mean() * 100 if inverted else (series <= value).mean() * 100
    return series.mean(), pct

def calculate_zscore(df, col, value, use_rel=False):
    if col is None or value is None: return None
    series = get_column_series(df, col, use_rel)
    if series is None or series.empty or len(series) < 2: return None
    mean_val = series.mean()
    std_val = series.std()
    if std_val == 0: return 0
    z = (value - mean_val) / std_val
    if "Ratio Squeeze" in col:
        return -abs(z)
    if is_inverted(col):
        z = -z
    return z

def get_norm_info(label, value, use_rel=False):
    norm_dict = NORMES_RELATIVES if use_rel else NORMES_ABSOLUES
    label_clean = label.replace("(G)", "").replace("(D)", "").strip()
    key = next((k for k in norm_dict if k in label_clean), None)
    
    if key is None or value is None: return "-", DARK
    norm = norm_dict[key]
    inverted = is_inverted(label)
    
    if isinstance(norm, list):
        low, high = norm
        txt = f"{low} - {high}"
        ok = low <= value <= high
    else:
        txt = f"< {norm}" if inverted else f"> {norm}"
        ok = (value <= norm) if inverted else (value >= norm)
    return txt, (GREEN if ok else SDR_RED)

def get_kine_radar_pct(label, val, df_ref, col, use_rel, row_data):
    if val is None: return 0
    label_clean = label.replace("(G)", "").replace("(D)", "").strip()
    
    norm_dict = NORMES_RELATIVES if use_rel else NORMES_ABSOLUES
    target = norm_dict.get(label_clean)
    
    if target is None:
        series = get_column_series(df_ref, col, use_rel)
        target = series.median() if series is not None and not series.empty else 0
    
    if target == 0: return 0
    
    cible_brute = target * row_data.get("Poids (kg)", 1) if use_rel else target
    
    if is_inverted(label):
        pct = (cible_brute / val) * 100
    else:
        pct = (val / cible_brute) * 100
        
    return max(50, min(pct, 150)) 

def img_to_b64(img_path):
    try:
        if not os.path.exists(img_path): return ""
        with open(img_path, "rb") as f: 
            return base64.b64encode(f.read()).decode()
    except: return ""

def get_logo_b64():
    b64 = img_to_b64("logo_sdr.png")
    if b64: return b64, "png"
    b64 = img_to_b64("logo_sdr.ico")
    if b64: return b64, "x-icon"
    return "", "png"

def get_best_photo_path(player_name):
    folder = "Photos"
    if not os.path.exists(folder): return None
    clean_player = remove_accents(player_name).lower()
    player_parts = clean_player.split()
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    for f in files:
        clean_filename = remove_accents(f).lower()
        match = True
        for part in player_parts:
            if part not in clean_filename:
                match = False
                break
        if match: return os.path.join(folder, f)
    return None

def create_radar_chart(categories, values):
    if not categories: return ""
    N = len(categories)
    values_closed = values + values[:1]
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill_between(angles, 0, 33, color=SDR_RED, alpha=0.12)
    ax.fill_between(angles, 33, 66, color=ORANGE, alpha=0.12)
    ax.fill_between(angles, 66, 95, color=GREEN, alpha=0.12)
    ax.fill_between(angles, 95, 100, color=BLUE_ELITE, alpha=0.12)
    plt.xticks(angles[:-1], categories, color=DARK, size=10, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([33, 66, 100], ["33", "66", ""], color="#888", size=8)
    plt.ylim(0, 100)
    ax.yaxis.grid(True, color="#ccc", linestyle='dashed')
    ax.xaxis.grid(True, color="#ccc")
    ax.spines['polar'].set_color("#ccc")
    ax.plot(angles, values_closed, linewidth=2, linestyle='solid', color=DARK, marker='o', markersize=6)
    ax.fill(angles, values_closed, color=DARK, alpha=0.35)
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=200)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64

def create_radar_chart_kine(categories, vals_g, vals_d):
    if not categories: return ""
    N = len(categories)
    vg = vals_g + vals_g[:1]
    vd = vals_d + vals_d[:1]
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill_between(angles, 50, 80, color=SDR_RED, alpha=0.12)
    ax.fill_between(angles, 80, 100, color=ORANGE, alpha=0.12)
    ax.fill_between(angles, 100, 120, color=GREEN, alpha=0.12)
    ax.fill_between(angles, 120, 150, color=BLUE_ELITE, alpha=0.12)
    plt.xticks(angles[:-1], categories, color=DARK, size=10, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([80, 100, 120], ["80%", "100%", "120%"], color="#888", size=8)
    plt.ylim(50, 150)
    ax.yaxis.grid(True, color="#ccc", linestyle='dashed')
    ax.xaxis.grid(True, color="#ccc")
    ax.spines['polar'].set_color("#ccc")
    
    ax.plot(angles, vg, linewidth=2, linestyle='solid', color='#3498DB', marker='o', markersize=6, label='Gauche')
    ax.plot(angles, vd, linewidth=2, linestyle='solid', color='#E74C3C', marker='o', markersize=6, label='Droite')
    
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=200)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64

def create_biodex_radar_matplotlib(cats, vals_l, vals_r, vals_norm):
    if not cats: return ""
    N = len(cats)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    n_closed = vals_norm + [vals_norm[0]]
    l_closed = vals_l + [vals_l[0]]
    r_closed = vals_r + [vals_r[0]]
    
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    plt.xticks(angles[:-1], cats, color=DARK, size=9, weight='bold')
    ax.set_rlabel_position(0)
    
    limit = max(max(vals_l + vals_r + vals_norm) * 1.1, 4.0)
    plt.ylim(0, limit)
    
    ax.plot(angles, n_closed, linewidth=2, linestyle='dashed', color='#2ECC71', label='Objectif')
    ax.fill(angles, n_closed, color='#2ECC71', alpha=0.1)
    
    ax.plot(angles, l_closed, linewidth=2, linestyle='solid', color='#1ABC9C', marker='o', label='Gauche')
    ax.fill(angles, l_closed, color='#1ABC9C', alpha=0.15)
    
    ax.plot(angles, r_closed, linewidth=2, linestyle='solid', color='#9B59B6', marker='o', label='Droite')
    ax.fill(angles, r_closed, color='#9B59B6', alpha=0.15)
    
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64

def create_evolution_chart(df, player, col_name, label, use_rel=False):
    if 'Session' not in df.columns: return ""
    player_data = df[df['Joueur'] == player].dropna(subset=[col_name, 'Session']).sort_values('Session')
    if len(player_data) < 2: return ""
    
    y_vals = player_data[col_name]
    if use_rel and 'Poids (kg)' in player_data.columns:
        w_vals = pd.to_numeric(player_data['Poids (kg)'], errors='coerce')
        y_vals = y_vals / w_vals

    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.plot(player_data['Session'].astype(str), y_vals, marker='o', color=SDR_RED, linewidth=2, markersize=5)
    ax.set_title(label.upper(), fontsize=9, color=DARK, weight='bold')
    ax.tick_params(axis='x', labelsize=7, colors='#666', rotation=30)
    ax.tick_params(axis='y', labelsize=7, colors='#666')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#ccc')
    ax.spines['bottom'].set_color('#ccc')
    ax.yaxis.grid(True, color="#eee", linestyle='dashed')
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64

def get_percentile_color(pct):
    if pct is None: return "#888"
    pct = max(0, min(100, pct))
    if pct < 33: return SDR_RED
    if pct < 66: return ORANGE
    if pct < 95: return GREEN
    return BLUE_ELITE

def get_percentile_bar_html(pct):
    if pct is None: return ""
    pct = max(0, min(100, pct))
    marker_color = get_percentile_color(pct)
    return f"""<div style="position:relative; width:100%; height:6px; border-radius:3px; margin-top:6px; background:linear-gradient(90deg, {SDR_RED} 0%, {SDR_RED} 33%, {ORANGE} 33%, {ORANGE} 66%, {GREEN} 66%, {GREEN} 95%, {BLUE_ELITE} 95%, {BLUE_ELITE} 100%); opacity:0.3;"><div style="position:absolute; left:calc({pct}% - 3px); top:-3px; width:6px; height:12px; background:{marker_color}; opacity:1; border-radius:2px; border:1px solid white; box-shadow:0 1px 2px rgba(0,0,0,0.4);"></div></div>"""

def format_pct(pct):
    if pct is None: return "-"
    p = int(pct)
    if p >= 95: return f"Top {max(1, 100 - p)}%"
    if p >= 66: return f"Top {max(1, 100 - p)}%"
    if p >= 33: return f"{p}%"
    return f"Flop {max(1, p)}%"

def get_zscore_gauge_html(group, z, count):
    if z is None: return ""
    z_clamped = max(-2.0, min(2.0, z))
    pct = (z_clamped + 2) / 4 * 100
    
    if z < -1.0: label, col = "Très en dessous", SDR_RED
    elif z < -0.5: label, col = "En dessous", ORANGE
    elif z < 0.5: label, col = "Dans la moyenne", "#888"
    elif z < 1.65: label, col = "Au-dessus", GREEN
    else: label, col = "Élite", BLUE_ELITE
    
    return f"""
    <div class="no-break" style="margin-bottom:8px; background:#fff; border:1px solid #eee; border-radius:6px; padding:6px 10px; box-shadow:0 1px 2px rgba(0,0,0,0.05); min-width: 250px; flex: 1;">
        <div style="display:flex; justify-content:space-between; margin-bottom:2px; font-size:8pt; font-weight:bold; color:#444;">
            <span>{group} <span style="font-size:6.5pt; color:#888; font-weight:normal;">({count})</span></span>
            <span style="color:{col};">{label}</span>
        </div>
        <div style="position:relative; width:100%; height:6px; border-radius:3px; background:linear-gradient(90deg, {SDR_RED} 0%, {ORANGE} 25%, #ddd 50%, {GREEN} 75%, {BLUE_ELITE} 100%); opacity:0.6;">
            <div style="position:absolute; left:calc({pct}% - 3px); top:-3px; width:6px; height:12px; background:#333; border-radius:3px; border:1px solid #fff; box-shadow:0 1px 2px rgba(0,0,0,0.5);"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:4px; font-size:5pt; color:#aaa;">
            <span>-2 SD</span><span>Moyenne</span><span>+2 SD</span>
        </div>
    </div>
    """

def generate_kine_comment(z_dict, avg_z):
    if not z_dict or avg_z is None: return ""
    
    if avg_z < -1.0: pos = "très en dessous de la moyenne"
    elif avg_z < -0.5: pos = "légèrement en dessous de la moyenne"
    elif avg_z < 0.5: pos = "dans la moyenne"
    elif avg_z < 1.65: pos = "au-dessus de la moyenne"
    else: pos = "dans la zone élite"
    
    sorted_tests = sorted(z_dict.items(), key=lambda item: item[1])
    bottom_tests = [t[0] for t in sorted_tests[:2] if t[1] < -0.5]
    top_tests = [t[0] for t in sorted_tests[-2:] if t[1] > 0.5]
    
    text = f"Le profil kiné/isocinétique global se situe <b>{pos}</b> du groupe de référence (Z = {avg_z:.2f}). "
    if top_tests:
        text += f"Les valeurs tirant le profil vers le haut sont : <i>{', '.join(top_tests)}</i>. "
    if bottom_tests:
        text += f"Les points d'attention concernent : <i>{', '.join(bottom_tests)}</i>. "
    
    return f"""
    <div style="background:#f9f9f9; border-left:4px solid #3498DB; padding:10px; margin-top:10px; border-radius:4px; font-size:8.5pt; color:#444;">
        <div style="font-weight:bold; color:#3498DB; margin-bottom:4px; text-transform:uppercase; font-size:8pt;">Bilan descriptif Kiné / Isocinétisme</div>
        {text}
    </div>
    """

def get_trend_html(curr_val, prev_val, label):
    if curr_val is None or prev_val is None: return ""
    delta = curr_val - prev_val
    if abs(delta) < 0.01: return "<span style='font-size:7pt; color:#888;'>→ (=)</span>"
    inv = is_inverted(label)
    is_good = (delta > 0) if not inv else (delta < 0)
    col = GREEN if is_good else SDR_RED
    arr = "↗" if delta > 0 else "↘"
    sign = "+" if delta > 0 else ""
    return f"<span style='font-size:8pt; color:{col}; font-weight:bold; margin-left:6px;'>{arr} {sign}{delta:.2f}</span>"

def get_metric_card_html(label, col, value, unit, pct, z_score, eval_data, prev_val, use_rel=False, is_report=False, is_kine=False):
    val_str = "-" if value is None else (f"{int(value)}" if float(value).is_integer() else f"{value:.2f}")
    norm_txt, norm_color = get_norm_info(label, value, use_rel)
    label_disp = label.replace("(G)", "· G").replace("(D)", "· D")
    
    pct_color = get_percentile_color(pct)
    trend_html = get_trend_html(value, prev_val, label)
    
    pdc_html = ""
    if use_rel and unit == "N/kg" and value is not None:
        pdc_html = f"<span style='font-size:9pt; color:#888; font-weight:normal; margin-left:6px;'>&middot; &approx;{value/9.81:.2f}&times; PDC</span>"
        
    z_html = f"<span style='font-size:7.5pt; color:#888; font-weight:normal; margin-left:8px;'>(Z: {z_score:.2f})</span>" if z_score is not None else ""
    
    eval_html = ""
    if eval_data:
        if eval_data['statut'] == 'Acquis':
            eval_html = f"<div style='margin-top:6px; padding-top:4px; border-top:1px solid #eee; font-size:7.5pt; color:{GREEN}; font-weight:bold;'>✅ Objectif Acquis</div>"
        elif eval_data['statut'] == 'Proche':
            eval_html = f"<div style='margin-top:6px; padding-top:4px; border-top:1px solid #eee; font-size:7.5pt; color:{ORANGE}; font-weight:bold;'>⚠️ Proche de l'objectif</div>"
        else:
            obj_str = eval_data.get('objectif', 'N/A')
            delai_str = eval_data.get('delai', '')
            if report_mode == "Préparation Physique" or not delai_str or delai_str == "Aucun":
                eval_html = f"<div style='margin-top:6px; padding-top:4px; border-top:1px solid #eee; font-size:7.5pt; color:{SDR_RED};'><b>❌ Non Acquis</b> | Obj: <b>{obj_str}</b></div>"
            else:
                eval_html = f"<div style='margin-top:6px; padding-top:4px; border-top:1px solid #eee; font-size:7.5pt; color:{SDR_RED};'><b>❌ Non Acquis</b> | Obj: <b>{obj_str}</b> | Délai: <b>{delai_str}</b></div>"

    bar_html = get_percentile_bar_html(pct)

    if is_report:
        if is_kine:
            width_style = "width: calc(33.333% - 6px);"
            pad = "4px 6px"
            font_val = "10pt"
            font_lbl = "5.5pt"
            font_unit = "5.5pt"
        else:
            width_style = "width: calc(50% - 6px);"
            pad = "8px 10px"
            font_val = "14pt"
            font_lbl = "7.5pt"
            font_unit = "7.5pt"
    else:
        width_style = "width: calc(50% - 4px);"
        pad = "12px 14px"
        font_val = "18pt"
        font_lbl = "9pt"
        font_unit = "9pt"
        
    return f"""<div class="no-break" style="background:#fff; border:1px solid #eee; border-left:3px solid {norm_color}; border-radius:4px; padding:{pad}; box-shadow:0 1px 2px rgba(0,0,0,0.03); {width_style} display:inline-block; vertical-align:top; margin-bottom:8px; box-sizing:border-box;">
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
            <div style="font-size:{font_lbl}; font-weight:bold; color:#555; text-transform:uppercase; overflow-wrap: break-word;">{label_disp}{z_html}</div>
            <div style="font-size:6.5pt; color:{norm_color}; font-weight:bold;">Obj. {norm_txt}</div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:4px;">
            <div style="font-size:{font_val}; font-weight:900; color:{DARK};">{val_str} <span style="font-size:{font_unit}; color:#888;">{unit}</span>{pdc_html}{trend_html}</div>
            <div style="font-size:7.5pt; font-weight:900; color:{pct_color};">{format_pct(pct)}</div>
        </div>
        {bar_html}{eval_html}
    </div>"""

def get_theme_card_html(theme, is_report=False):
    couleur = SDR_RED if theme["etat"] in ("En manque de", "Prévention de", "Rééquilibrage de") else GREEN
    w_style = "width: calc(33.333% - 10px); display: inline-block; flex-grow: 1; min-width: 200px;" if is_report else "width: 100%; display: block;"
    return f"""
    <div class="no-break" style="background:#fff; border-left:4px solid {couleur}; padding:12px; border-radius:6px; box-shadow:0 1px 3px rgba(0,0,0,0.05); border: 1px solid #eee; box-sizing: border-box; overflow-wrap: break-word; {w_style}">
        <div style="font-size:7pt; color:{couleur}; font-weight:bold; text-transform:uppercase; margin-bottom:4px; background: rgba(0,0,0,0.03); display: inline-block; padding: 2px 6px; border-radius: 3px;">{theme['etat']}</div>
        <div style="font-size:10pt; font-weight:900; color:#333; line-height:1.2;">{theme['qualite']}</div>
        <div style="font-size:8pt; color:#666; margin-top:4px;">📍 {theme['zone']}</div>
        <div style="font-size:7.5pt; color:#444; margin-top:6px; border-top:1px dashed #eee; padding-top:4px;">
            <b>Obj:</b> {theme.get('objectif', '-')} <br>
            <b>Fréq:</b> {theme.get('freq', '-')} | <b>Moment:</b> {theme.get('moment', '-')}
        </div>
    </div>
    """

def get_theme_suggestions_advanced(row, df):
    suggestions = []
    col_ratio = find_column(df, "Ratio Squeeze")
    val_ratio = clean_numeric_value(row.get(col_ratio), col_ratio)
    if val_ratio and (val_ratio < 0.85 or val_ratio > 1.15):
        suggestions.append({"etat": "Prévention de", "qualite": "Blessure (Ratio)", "zone": "Hanche / Pubis", "score": 100})
        
    for base in ["Adducteurs", "Abducteurs", "Nordic Ischio", "Inverseur", "Everseur"]:
        col_g = find_column(df, f"{base} (G)")
        col_d = find_column(df, f"{base} (D)")
        v_g = clean_numeric_value(row.get(col_g), col_g)
        v_d = clean_numeric_value(row.get(col_d), col_d)
        if v_g and v_d and max(v_g, v_d) > 0:
            diff = abs(v_g - v_d) / max(v_g, v_d) * 100
            if diff >= 15:
                suggestions.append({"etat": "Rééquilibrage de", "qualite": "Force", "zone": base, "score": diff + 50})

    for label, (qualite, zone) in THEME_MAPPING.items():
        col = find_column(df, label)
        val = clean_numeric_value(row.get(col), col)
        if val is None: continue
        _, pct = calculate_percentile(df, col, val)
        if pct is not None and pct < 33:
            severity = 100 - pct 
            suggestions.append({"etat": "En manque de", "qualite": qualite, "zone": zone, "score": severity})
            
    seen = set()
    uniq = []
    for s in sorted(suggestions, key=lambda x: x["score"], reverse=True):
        key = (s["etat"], s["qualite"], s["zone"])
        if key not in seen:
            seen.add(key)
            uniq.append({"id": str(uuid.uuid4()), "etat": s["etat"], "qualite": s["qualite"], "zone": s["zone"], "objectif": "", "freq": "1x/sem", "moment": "Pré séance"})
            
    return uniq[:3] 

def get_value_for_metric(row, df, col, use_rel):
    val = clean_numeric_value(row.get(col), col)
    if use_rel and val is not None:
        w = clean_numeric_value(row.get("Poids (kg)"), "Poids (kg)")
        if w and w > 0: val = val / w
        else: val = None
    return val

def auto_eval_metric(label, value, pct, use_rel=False):
    if value is None: return "Non Acquis", ""
    norm_dict = NORMES_RELATIVES if use_rel else NORMES_ABSOLUES
    label_clean = label.replace("(G)", "").replace("(D)", "").strip()
    key = next((k for k in norm_dict if k in label_clean), None)
    unit = UNITS.get(label, "")
    
    if key:
        norm = norm_dict[key]
        inverted = is_inverted(label)
        if isinstance(norm, list):
            if norm[0] <= value <= norm[1]: return "Acquis", ""
            return "Proche" if (norm[0]*0.95 <= value) else "Non Acquis", f"Cible: {norm[0]}-{norm[1]} {unit}"
        else:
            if (not inverted and value >= norm*0.95) or (inverted and value <= norm*1.05):
                return "Acquis" if (not inverted and value >= norm) or (inverted and value <= norm) else "Proche", ""
            return "Non Acquis", f"Cible: {'<' if inverted else '>'} {norm} {unit}"
    return "Non Acquis", ""

# MODIFICATION: Ajout de is_commun dans les arguments de build_prepa_report
def build_prepa_report(player_name, row, df_ref, df_full, poste, latéralité, anthro, selected_metrics, use_relative, radar_labels, radar_values, themes, dominant, weak, strat_salle, strat_terrain, photo_b64, logo_b64, logo_ext, staff_evals, current_session, df_prev_session, rdv_date, entretien_date, context_test, ref_group_label, comp_zscores, is_commun=False):
    metric_cards_by_group = {}
    sorted_groups = list(GROUPES_PREPA.items())

    for group, labels in sorted_groups:
        if "Biodex" in group: continue 
        
        cards = []
        for label in labels:
            if label not in selected_metrics: continue
            col = find_column(df_full, label)
            use_rel = use_relative.get(label, False)
            value = get_value_for_metric(row, df_full, col, use_rel) if col else None
            unit = UNITS.get(label, "")
            if use_rel and unit:
                unit = f"{unit}/kg"
            _, pct = calculate_percentile(df_ref, col, value, use_rel) if col and value is not None else (None, None)
            z_score = calculate_zscore(df_ref, col, value, use_rel) if col and value is not None else None
            prev_val = None
            if df_prev_session is not None and col in df_prev_session.columns:
                prev_val = get_value_for_metric(df_prev_session.iloc[0], df_full, col, use_rel)
            eval_data = staff_evals.get(label, None)
            cards.append(get_metric_card_html(label, col, value, unit, pct, z_score, eval_data, prev_val, use_rel, is_report=True, is_kine=False))
        if cards:
            metric_cards_by_group[group] = cards

    metrics_html = ""
    for group, cards in metric_cards_by_group.items():
        if not cards: continue
        metrics_html += f"""
        <div class="no-break" style="margin-bottom:12px;">
            <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                <span>{group}</span>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap: 8px;">{''.join(cards)}</div>
        </div>
        """

    zscore_html = ""
    if comp_zscores:
        zscore_html += f"""
        <div style="margin-bottom:20px;">
            <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:12px;">INDICES COMPOSITES (Z-SCORES)</div>
            <div style="display:flex; flex-wrap:wrap; gap:12px; justify-content:flex-start;">
        """
        for group, data in comp_zscores.items():
            # MODIFICATION: Limiter aux groupes prépa pour éviter doublons en mode commun
            if group in GROUPES_PREPA:
                zscore_html += get_zscore_gauge_html(group, data["score"], data["count"])
        zscore_html += "</div></div>"

    radar_b64 = create_radar_chart(radar_labels, radar_values) if radar_labels else ""
    radar_html = f'<div class="no-break" style="text-align:center; margin: 5px 0;"><img src="data:image/png;base64,{radar_b64}" style="width:100%; max-width:450px;"></div>' if radar_b64 else "<p style='font-size:8pt; color:#999; text-align:center;'>Aucune variable sélectionnée pour le radar.</p>"
    themes_html = ""
    for t in themes:
        themes_html += get_theme_card_html(t, is_report=True)
    if not themes_html: themes_html = "<p style='margin:0; font-size:9pt; color:#999;'>Aucune recommandation thématique définie.</p>"

    age_val = str(anthro.get('Age', '-')).strip()
    taille_val = str(anthro.get('Taille', '-')).strip()
    poids_val = str(anthro.get('Poids', '-')).strip()
    age_html = f"{age_val} <span style='font-size:7pt; color:#888; font-weight:normal;'>ans</span>" if age_val != "-" else "-"
    taille_html = f"{taille_val} <span style='font-size:7pt; color:#888; font-weight:normal;'>cm</span>" if taille_val != "-" else "-"
    poids_html = f"{poids_val} <span style='font-size:7pt; color:#888; font-weight:normal;'>kg</span>" if poids_val != "-" else "-"
    
    photo_img = f'<img src="data:image/png;base64,{photo_b64}" style="width:110px; height:110px; object-fit:cover; object-position:top center; display:block; border-radius:12px; border:2px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.08); flex-shrink:0;">' if photo_b64 else f'<div style="width:110px; height:110px; background:#f0f0f0; display:flex; align-items:center; justify-content:center; text-align:center; color:#aaa; font-weight:bold; font-size:32px; border-radius:12px; border:2px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.08); flex-shrink:0; line-height:110px;">{player_name[:1]}</div>'
    logo_img = f'<img src="data:image/{logo_ext};base64,{logo_b64}" style="width:75px; margin-bottom:5px;">' if logo_b64 else ''
    
    legend_html = f"""
    <div class="no-break" style="margin-top:5px; margin-bottom:0px; padding:12px; background:#f8f9fa; border:1px solid #e9ecef; border-radius:8px; font-size:8pt; color:#495057; box-shadow: 0 2px 4px rgba(0,0,0,0.02); width:100%; box-sizing:border-box;">
        <div style="display:flex; justify-content:space-around; align-items:flex-start;">
            <div style="flex:1;">
                <div style="font-weight:bold; color:#333; margin-bottom:6px; font-size:7.5pt; letter-spacing:0.5px;">🎯 STATUT OBJECTIF</div>
                <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{GREEN};"><div style="width:8px; height:8px; border-radius:50%; background:{GREEN};"></div> Acquis</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{ORANGE};"><div style="width:8px; height:8px; border-radius:50%; background:{ORANGE};"></div> Proche</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{SDR_RED};"><div style="width:8px; height:8px; border-radius:50%; background:{SDR_RED};"></div> Non Acquis</span>
                </div>
            </div>
            <div style="flex:2; border-left:1px dashed #ccc; padding-left:15px;">
                <div style="font-weight:bold; color:#333; margin-bottom:6px; font-size:7.5pt; letter-spacing:0.5px;">📊 RANG (Percentile vs Référence)</div>
                <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{BLUE_ELITE};"><div style="width:10px; height:4px; border-radius:2px; background:{BLUE_ELITE};"></div> Élite (≥ 95% / Z ≥ 1.65)</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{GREEN};"><div style="width:10px; height:4px; border-radius:2px; background:{GREEN};"></div> Bon (≥ 66%)</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{ORANGE};"><div style="width:10px; height:4px; border-radius:2px; background:{ORANGE};"></div> Moyen (≥ 33%)</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{SDR_RED};"><div style="width:10px; height:4px; border-radius:2px; background:{SDR_RED};"></div> Flop (&lt; 33%)</span>
                </div>
            </div>
        </div>
    </div>
    """

    css = f"""
    <style>
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; background: #eee; margin:0; padding:0; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        .report-container {{ background: white; max-width: 210mm; margin: 10px auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); padding: 10mm 15mm 20mm 15mm; box-sizing: border-box; position: relative; }}
        .page-break {{ page-break-before: always; margin: 0; padding: 0; }}
        .no-break {{ page-break-inside: avoid; break-inside: avoid; }}
        .footer-print {{ display: none; }}
        
        @media print {{
            @page {{ size: A4; margin: 10mm 15mm; }}
            body {{ background: white; margin: 0; padding: 0; }}
            .report-container {{ margin: 0; box-shadow: none; max-width: 100%; padding: 0; width: 100%; }}
            .page-break {{ margin-top: 0; padding-top: 0; }}
            .footer-print {{ display: flex !important; position: fixed; bottom: 0; left: 0; right: 0; justify-content: space-between; font-size: 7pt; color: #aaa; border-top: 1px solid #eee; padding: 5px 0 0 0; background: white; }}
        }}
    </style>
    """

    context_html = f"<div style='margin-top:10px; font-size:8.5pt; color:#666; overflow-wrap: break-word;'><b>Contexte du test :</b> {context_test}</div>" if context_test else ""

    header_html = f"""
        <div class="no-break" style="display:flex; justify-content:space-between; align-items:center; border-bottom: 3px solid {SDR_RED}; padding-bottom: 15px; margin-bottom: 15px;">
            <div style="display:flex; align-items:center; gap: 20px; flex-grow:1;">
                {photo_img}
                <div style="flex-grow:1; display:flex; flex-direction:column; justify-content:center;">
                    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:5px;">
                        <h1 style="margin:0; color:{SDR_RED}; font-size:26pt; font-weight:900; text-transform:uppercase; line-height:1; overflow-wrap: break-word;">
                            {player_name}
                        </h1>
                    </div>
                    <div style="font-size:11pt; font-weight:bold; color:#555; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">
                        {poste} &bull; {latéralité}
                    </div>
                    <div style="display:flex; gap:10px; width:100%;">
                        <div style="flex:1; background:#f8f9fa; border:1px solid #eee; padding:6px; border-radius:6px; text-align:center;">
                            <span style="color:#888; font-size:7pt; text-transform:uppercase; display:block;">Âge</span>
                            <span style="font-weight:900; font-size:11pt; color:{DARK};">{age_html}</span>
                        </div>
                        <div style="flex:1; background:#f8f9fa; border:1px solid #eee; padding:6px; border-radius:6px; text-align:center;">
                            <span style="color:#888; font-size:7pt; text-transform:uppercase; display:block;">Taille</span>
                            <span style="font-weight:900; font-size:11pt; color:{DARK};">{taille_html}</span>
                        </div>
                        <div style="flex:1; background:#f8f9fa; border:1px solid #eee; padding:6px; border-radius:6px; text-align:center;">
                            <span style="color:#888; font-size:7pt; text-transform:uppercase; display:block;">Poids</span>
                            <span style="font-weight:900; font-size:11pt; color:{DARK};">{poids_html}</span>
                        </div>
                    </div>
                    {context_html}
                </div>
            </div>
            <div style="text-align:right; border-left:2px solid #eee; padding-left:20px; margin-left:20px; min-width:100px;">
                {logo_img}
                <div style="font-weight:900; color:#333; font-size:8.5pt; text-transform:uppercase; line-height:1.3; margin-top:5px; overflow-wrap: break-word;">
                    Département<br><span style="color:{SDR_RED}">Performance</span>
                </div>
            </div>
        </div>
        <div class="no-break" style="font-size:8pt; color:#666; background:#eefaf3; border:1px solid {GREEN}; padding:6px 12px; border-radius:4px; display:inline-block; margin-bottom:15px; font-weight:bold; overflow-wrap: break-word;">
            Comparé à : {ref_group_label}
        </div>
    """

    evol_charts = ""
    top_metrics = []
    if 'Vmax' in selected_metrics: top_metrics.append('Vmax')
    if 'CMJ 2JB' in selected_metrics: top_metrics.append('CMJ 2JB')
    if 'VMA' in selected_metrics: top_metrics.append('VMA')
    if 'Peak Force CMJ' in selected_metrics: top_metrics.append('Peak Force CMJ')
    
    if len(top_metrics) < 4:
        for m in selected_metrics:
            if m not in top_metrics and "Distance" not in m and "(G)" not in m and "(D)" not in m:
                top_metrics.append(m)
            if len(top_metrics) == 4: break

    has_evolution = False
    for m in top_metrics:
        col = find_column(df_full, m)
        if col:
            use_rel = use_relative.get(m, False)
            b64_chart = create_evolution_chart(df_full, player_name, col, m, use_rel)
            if b64_chart:
                evol_charts += f'<div class="no-break" style="text-align:center; background:#fff; border:1px solid #eee; border-radius:8px; padding:10px; margin-bottom:15px; width: calc(50% - 8px); box-sizing:border-box;"><img src="data:image/png;base64,{b64_chart}" style="width:100%; max-width:400px;"></div>'
                has_evolution = True

    dominant_txt = dominant.strip() if dominant else ""
    weak_txt = weak.strip() if weak else ""
    strat_salle_txt = strat_salle.strip() if strat_salle else ""
    strat_terrain_txt = strat_terrain.strip() if strat_terrain else ""

    strategy_html = f"""
        <div class="no-break" style="padding:10px 14px; margin-bottom:10px; border-radius:6px; border-left:6px solid #3498DB; background:#f0f7fd; word-wrap: break-word; overflow-wrap: break-word;">
            <div style="color:#3498DB; font-weight:bold; font-size:9pt; margin-bottom:4px;">STRATÉGIE SALLE</div>
            <div style="font-size:8.5pt; color:#333; white-space: pre-wrap; margin:0; padding:0;">{strat_salle_txt}</div>
        </div>
        <div class="no-break" style="padding:10px 14px; margin-bottom:10px; border-radius:6px; border-left:6px solid #8E44AD; background:#f9f0fd; word-wrap: break-word; overflow-wrap: break-word;">
            <div style="color:#8E44AD; font-weight:bold; font-size:9pt; margin-bottom:4px;">STRATÉGIE TERRAIN</div>
            <div style="font-size:8.5pt; color:#333; white-space: pre-wrap; margin:0; padding:0;">{strat_terrain_txt}</div>
        </div>
    """

    # MODIFICATION: Gestion du mode "Commun" où l'on s'arrête avant la page de recommandations
    doc_html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">{css}</head><body>
    <div class="report-container">
        
        <div class="report-section">
            {header_html}
            {zscore_html}
            {radar_html}
            {legend_html}
        </div>
        
        <div class="page-break"></div>
        <div class="report-section">
            <div class="no-break" style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 16px;">
                <h2 style="margin:0; color:{DARK}; font-size:14pt; text-transform:uppercase;">Détail des Métriques</h2>
                <div style="font-size:10pt; color:#888; font-weight:bold;">{player_name}</div>
            </div>
            {metrics_html}
        </div>

<!-- MARQUEUR_RECO -->
        <div class="page-break"></div>
        <div class="report-section">
            <div class="no-break" style="display:flex; align-items:center; gap: 20px; border-bottom: 3px solid {SDR_RED}; padding-bottom: 15px; margin-bottom: 20px;">
                {photo_img}
                <div>
                    <h1 style="margin:0; color:{SDR_RED}; font-size:24pt; text-transform:uppercase; line-height:1; overflow-wrap: break-word;">{player_name}</h1>
                    <div style="font-size:12pt; font-weight:bold; color:#555; text-transform:uppercase; margin-top:4px;">Bilan, Thématiques & Entretien</div>
                </div>
            </div>
            
            <div class="no-break" style="margin-bottom: 20px; margin-top: 10px;">
                <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:12px;">RECOMMANDATIONS THÉMATIQUES</div>
                <div style="display: flex; flex-wrap: wrap; gap: 15px;">{themes_html}</div>
            </div>

            <div class="no-break" style="margin-top:20px;">
                <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:12px;">SYNTHÈSE</div>
                <div class="no-break" style="padding:10px 14px; margin-bottom:10px; border-radius:6px; border-left:6px solid {GREEN}; background:#eefaf3; word-wrap: break-word; overflow-wrap: break-word;">
                    <div style="color:{GREEN}; font-weight:bold; font-size:9pt; margin-bottom:4px;">POINT(S) FORT(S)</div>
                    <div style="font-size:8.5pt; color:#333; white-space: pre-wrap; margin:0; padding:0;">{dominant_txt}</div>
                </div>
                <div class="no-break" style="padding:10px 14px; margin-bottom:10px; border-radius:6px; border-left:6px solid {SDR_RED}; background:#fef5f5; word-wrap: break-word; overflow-wrap: break-word;">
                    <div style="color:{SDR_RED}; font-weight:bold; font-size:9pt; margin-bottom:4px;">AXES D'AMÉLIORATION</div>
                    <div style="font-size:8.5pt; color:#333; white-space: pre-wrap; margin:0; padding:0;">{weak_txt}</div>
                </div>
                {strategy_html}
            </div>
            
            <div class="no-break" style="margin-top:20px; border:1px solid #ccc; border-radius:8px; padding:15px; background:#fafafa;">
                <div style="font-weight:bold; color:#555; font-size:9pt; margin-bottom:8px; text-transform:uppercase;">Conclusion de l'entretien</div>
                <div style="display:flex; justify-content:space-between; font-size:8.5pt; margin-bottom:8px;">
                    <div><b>Date de l'entretien :</b> {entretien_date if entretien_date else "...................."}</div>
                </div>
                <div style="font-size:8.5pt;"><b>Prochain RDV / Test :</b> {rdv_date if rdv_date else "........................................"}</div>
            </div>
        </div>
    """
    
    if has_evolution:
        doc_html += f"""
        <div class="page-break"></div>
        <div class="report-section">
            <div class="no-break" style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin:0; color:{DARK}; font-size:14pt; text-transform:uppercase;">Suivi Longitudinal</h2>
                <div style="font-size:10pt; color:#888; font-weight:bold;">{player_name}</div>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap:15px;">
                {evol_charts}
            </div>
            <div class="no-break" style="margin-top:20px; text-align:center; font-size:8pt; color:#888; font-style:italic;">
                Note : Les variations de faible amplitude peuvent relever du bruit de mesure inhérent aux tests. À interpréter avec prudence.
            </div>
        </div>
        """
        
    doc_html += """
        <div class="footer-print">
            <span>Département Performance · Stade de Reims</span>
            <span>Document confidentiel — usage interne club</span>
        </div>
    </div>
    </body></html>
    """
    return doc_html

# MODIFICATION: Ajout de is_commun dans les arguments de build_kine_report
def build_kine_report(player_name, row, df_ref, df_full, poste, latéralité, anthro, selected_metrics, use_relative, radar_labels, radar_values, themes, dominant, weak, strat_salle, strat_terrain, photo_b64, logo_b64, logo_ext, staff_evals, current_session, df_prev_session, rdv_date, entretien_date, context_test, ref_group_label, comp_zscores, antecedents, leg_overrides, radar_vals_d, is_commun=False):
    
    metric_cards_by_group = {}
    sorted_groups = list(GROUPES_KINE.items())
    
    if antecedents:
        prioritaires = []
        ant_lower = antecedents.lower()
        for lbl in selected_metrics:
            is_prio = False
            lbl_lower = lbl.lower()
            if "ischio" in ant_lower and ("ij" in lbl_lower or "ischio" in lbl_lower or "mixte" in lbl_lower): is_prio = True
            elif ("adducteur" in ant_lower or "pubalgie" in ant_lower) and ("add" in lbl_lower or "abd" in lbl_lower or "squeeze" in lbl_lower): is_prio = True
            elif "cheville" in ant_lower and ("verseur" in lbl_lower): is_prio = True
            elif "quadri" in ant_lower and ("q conc" in lbl_lower or "quadri" in lbl_lower): is_prio = True
            if is_prio: prioritaires.append(lbl)
        if prioritaires:
            sorted_groups.insert(0, ("Priorité Antécédents", prioritaires))

    for group, labels in sorted_groups:
        cards = []
        for label in labels:
            if label not in selected_metrics: continue
            if group != "Priorité Antécédents" and antecedents and any(label in p_list for g, p_list in sorted_groups if g == "Priorité Antécédents"):
                continue

            col = find_column(df_full, label)
            use_rel = use_relative.get(label, False)
            value = get_value_for_metric(row, df_full, col, use_rel) if col else None
            unit = UNITS.get(label, "")
            if use_rel and unit:
                unit = f"{unit}/kg"
            _, pct = calculate_percentile(df_ref, col, value, use_rel) if col and value is not None else (None, None)
            z_score = calculate_zscore(df_ref, col, value, use_rel) if col and value is not None else None
            prev_val = None
            if df_prev_session is not None and col in df_prev_session.columns:
                prev_val = get_value_for_metric(df_prev_session.iloc[0], df_full, col, use_rel)

            eval_data = staff_evals.get(label, None)
            cards.append(get_metric_card_html(label, col, value, unit, pct, z_score, eval_data, prev_val, use_rel, is_report=True, is_kine=True))
        if cards:
            metric_cards_by_group[group] = cards

    metrics_html = ""
    for group, cards in metric_cards_by_group.items():
        if not cards: continue
        metrics_html += f"""
        <div class="no-break" style="margin-bottom:12px;">
            <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                <span>{group}</span>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap: 6px;">{''.join(cards)}</div>
        </div>
        """

    asym_html = ""
    pairs = []
    for m in selected_metrics:
        if "(G)" in m and m != "Ratio Mixte (G)":
            base = m.replace("(G)", "").strip()
            if f"{base} (D)" in selected_metrics:
                pairs.append((base, m, f"{base} (D)"))
    
    if pairs:
        asym_html += f"""
        <div style="margin-bottom:12px;">
            <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:6px;">PROFIL D'ASYMÉTRIE (Jambe Dominante / Appui)</div>
            <div style="font-size:7pt; color:#666; margin-bottom:8px; font-style:italic;">* Seuils indicatifs (<10% vert, 10-15% orange, >15% rouge). À valider par le staff médical. Convention utilisée : Dominante = Frappe.</div>
            <div style="display:flex; flex-wrap:wrap; gap:6px;">
        """
        for base, g_lbl, d_lbl in set(pairs):
            c_g = find_column(df_full, g_lbl)
            c_d = find_column(df_full, d_lbl)
            use_rel = use_relative.get(g_lbl, False) or use_relative.get(d_lbl, False)
            v_g = get_value_for_metric(row, df_full, c_g, use_rel)
            v_d = get_value_for_metric(row, df_full, c_d, use_rel)
            
            if v_g and v_d and max(v_g, v_d) > 0:
                diff_pct = abs(v_g - v_d) / max(v_g, v_d) * 100
                col_asym = GREEN if diff_pct < 10 else (ORANGE if diff_pct <= 15 else SDR_RED)
                
                if leg_overrides:
                    lbl_dom = leg_overrides.get("frappe", "D")
                    lbl_app = leg_overrides.get("appui", "G")
                    v_dom = v_d if lbl_dom == "D" else v_g
                    v_app = v_g if lbl_app == "G" else v_d
                else:
                    lat_val = str(latéralité).strip().upper()
                    if lat_val == "D":
                        v_dom, v_app = v_d, v_g
                        lbl_dom, lbl_app = "D", "G"
                    elif lat_val == "G":
                        v_dom, v_app = v_g, v_d
                        lbl_dom, lbl_app = "G", "D"
                    else:
                        v_dom, v_app = v_d, v_g
                        lbl_dom, lbl_app = "D", "G"

                deficit = f"Dom ({lbl_dom})" if v_dom < v_app else (f"Appui ({lbl_app})" if v_app < v_dom else "=")
                
                asym_html += f"""
                <div class="no-break" style="background:#fff; border-top:3px solid {col_asym}; padding:6px; border-radius:4px; border-bottom:1px solid #eee; border-left:1px solid #eee; border-right:1px solid #eee; font-size:7.5pt; text-align:center; width: calc(25% - 5px); box-sizing:border-box;">
                    <div style="font-weight:bold; color:#555; margin-bottom:4px; overflow-wrap: break-word;">{base}</div>
                    <div style="font-size:11pt; font-weight:900; color:{col_asym};">{diff_pct:.1f}%</div>
                    <div style="color:#888; font-size:6.5pt; margin-top:2px;">Dom: {v_dom:.1f} | App: {v_app:.1f} <br>Déficit: <b>{deficit}</b></div>
                </div>
                """
        asym_html += "</div></div>"

    ratio_html = ""
    if "Ratio Mixte (G)" in selected_metrics or "Ratio Mixte (D)" in selected_metrics:
        ratio_html += f"""
        <div style="margin-bottom:12px;">
            <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:6px;">RATIO MIXTE (Fonctionnel Ischio-Jambiers)</div>
            <div style="display:flex; flex-wrap:wrap; gap:6px;">
        """
        for lbl in ["Ratio Mixte (G)", "Ratio Mixte (D)"]:
            if lbl in selected_metrics:
                c = find_column(df_full, lbl)
                v = clean_numeric_value(row.get(c), c) if c else None
                _, p = calculate_percentile(df_ref, c, v) if c and v is not None else (None, None)
                v_str = f"{v:.2f}" if v is not None else "-"
                p_col = get_percentile_color(p)
                bar = get_percentile_bar_html(p)
                ratio_html += f"""
                <div class="no-break" style="background:#fff; border:1px solid #eee; border-radius:6px; padding:8px; width: calc(50% - 3px); box-sizing:border-box;">
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <div style="font-size:7.5pt; font-weight:bold; color:#555; overflow-wrap: break-word;">{lbl}</div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:2px;">
                        <div style="font-size:12pt; font-weight:900; color:{DARK};">{v_str}</div>
                        <div style="font-size:7.5pt; font-weight:900; color:{p_col};">{format_pct(p)}</div>
                    </div>
                    {bar}
                </div>
                """
        ratio_html += """
            </div>
            <div style="margin-top:8px; border:1px dashed #ccc; padding:10px; border-radius:4px; font-size:8pt; color:#666; min-height:50px;">
                <i>Espace réservé à l'interprétation du staff médical / préparation physique :</i><br><br>
            </div>
        </div>
        """

    targets = {"Q 60°": 3.1, "Q 240°": 2.2, "IJ 60°": 1.8, "IJ 240°": 1.5, "IJ Exc 30°": 2.4}
    biodex_full_config = [
        {"label": "Q 60°", "g_rel": "Q G conc 60°/s (N/kg)", "d_rel": "Q Dt conc 60°/s (N/kg)", "g_raw": "Q G conc 60°/s", "d_raw": "Q Dt conc 60°/s"},
        {"label": "Q 240°", "g_rel": "Q G conc 240°/s (N/kg)", "d_rel": "Q Dt conc 240°/s (N/kg)", "g_raw": "Q G conc 240°/s", "d_raw": "Q Dt conc 240°/s"},
        {"label": "IJ 60°", "g_rel": "IJ G conc 60°/s (N/kg)", "d_rel": "IJ Dt conc 60°/s (N/kg)", "g_raw": "IJ G conc 60°/s", "d_raw": "IJ Dt conc 60°/s"},
        {"label": "IJ 240°", "g_rel": "IJ G conc 240°/s (N/kg)", "d_rel": "IJ Dt conc 240°/s (N/kg)", "g_raw": "IJ G conc 240°/s", "d_raw": "IJ Dt conc 240°/s"},
        {"label": "IJ Exc 30°", "g_rel": "IJ G Exc 30°/s (N/kg)", "d_rel": "IJ Dt exc 30°/s (N/kg)", "g_raw": "IJ G Exc 30°/s", "d_raw": "IJ Dt exc 30°/s"}
    ]
    rcats, r_l_rel, r_r_rel, r_norm, tbl_data = [], [], [], [], []
    poids_joueur = clean_numeric_value(row.get("Poids (kg)"))
    
    for item in biodex_full_config:
        lbl = item["label"]
        rcats.append(lbl)
        val_norm_rel = targets.get(lbl, 0)
        r_norm.append(val_norm_rel)
        
        col_g_rel = find_column(df_full, item["g_rel"]) or item["g_rel"]
        col_d_rel = find_column(df_full, item["d_rel"]) or item["d_rel"]
        v_g_rel = clean_numeric_value(row.get(col_g_rel))
        v_d_rel = clean_numeric_value(row.get(col_d_rel))
        r_l_rel.append(v_g_rel if v_g_rel is not None else 0)
        r_r_rel.append(v_d_rel if v_d_rel is not None else 0)
        
        col_g_raw = find_column(df_full, item["g_raw"]) or item["g_raw"]
        col_d_raw = find_column(df_full, item["d_raw"]) or item["d_raw"]
        v_g_raw = clean_numeric_value(row.get(col_g_raw))
        v_d_raw = clean_numeric_value(row.get(col_d_raw))

        s_lsi, c_lsi = "-", "#888"
        if v_g_raw is not None and v_d_raw is not None:
            mx = max(v_g_raw, v_d_raw)
            if mx > 0:
                lsi = ((v_d_raw - v_g_raw) / mx) * 100
                s_lsi = f"{lsi:.0f}%"
                c_lsi = "#D71920" if abs(lsi) > 10 else ("#F39C12" if abs(lsi) > 5 else "#27AE60")
        
        target_abs = f"{val_norm_rel * poids_joueur:.0f}" if poids_joueur and poids_joueur > 0 else "-"
        tbl_data.append({"label": lbl, "target": target_abs, "v_g": f"{v_g_raw:.0f}" if v_g_raw is not None else "-", "v_d": f"{v_d_raw:.0f}" if v_d_raw is not None else "-", "lsi": s_lsi, "c_lsi": c_lsi})
        
    biodex_b64 = create_biodex_radar_matplotlib(rcats, r_l_rel, r_r_rel, r_norm)
    
    h_rows = ""
    for item in tbl_data:
        h_rows += f"<tr style='border-bottom:1px solid #eee;'><td style='padding:4px; color:#555;'>{item['label']}</td><td style='text-align:center; color:#888; font-weight:bold;'>{item['target']}</td><td style='text-align:center; color:#111; font-weight:bold;'>{item['v_g']}</td><td style='text-align:center; color:#111; font-weight:bold;'>{item['v_d']}</td><td style='text-align:center; color:{item['c_lsi']}; font-weight:bold;'>{item['lsi']}</td></tr>"
    
    col_rm_g, col_rm_d = find_column(df_full, "Ratio Mixte (G)"), find_column(df_full, "Ratio Mixte (D)")
    val_rm_g = clean_numeric_value(row.get(col_rm_g)) if col_rm_g else None
    val_rm_d = clean_numeric_value(row.get(col_rm_d)) if col_rm_d else None
    
    def get_ratio_color(val):
        if val is None: return "#888"
        return "#D71920" if val < 0.8 else ("#F39C12" if val <= 1.0 else "#27AE60")
        
    s_rm_g = f"{val_rm_g:.2f}" if val_rm_g is not None else "-"
    s_rm_d = f"{val_rm_d:.2f}" if val_rm_d is not None else "-"
    h_rows += f"<tr style='border-top:2px solid #ccc; background-color:#f9f9f9;'><td style='padding:4px; font-weight:bold; color:#111;'>Ratio Mixte</td><td style='text-align:center;'>-</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_g)};'>{s_rm_g}</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_d)};'>{s_rm_d}</td><td style='text-align:center;'>-</td></tr>"
    
    biodex_html = f"""
    <div class="no-break" style="margin-bottom:16px;">
        <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid {SDR_RED}; padding-bottom:4px; margin-bottom:12px;">RADAR BIODEX (VALEURS RELATIVES)</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="width:50%; text-align:center;">
                <img src="data:image/png;base64,{biodex_b64}" style="width:100%; max-width:320px;">
            </div>
            <div style="width:48%;">
                <div style='text-align:center; font-size:9pt; font-weight:900; color:{SDR_RED}; margin-bottom:8px; text-transform:uppercase;'>Résultats Détaillés (Nm)</div>
                <table style='width:100%; border-collapse:collapse; font-size:7.5pt; font-family:sans-serif;'>
                    <tr style='background-color:#f0f0f0; color:#333; text-transform:uppercase; font-size:6.5pt;'>
                        <th style='padding:4px; text-align:left;'>Test</th>
                        <th style='padding:4px; text-align:center;'>Obj. (Nm)</th>
                        <th style='padding:4px; text-align:center;'>G (Nm)</th>
                        <th style='padding:4px; text-align:center;'>D (Nm)</th>
                        <th style='padding:4px; text-align:center;'>LSI</th>
                    </tr>
                    {h_rows}
                </table>
            </div>
        </div>
    </div>
    """

    kine_z_dict = {}
    for label in selected_metrics:
        if label in KINE_LABELS:
            col = find_column(df_full, label)
            use_rel = use_relative.get(label, False)
            val = get_value_for_metric(row, df_full, col, use_rel) if col else None
            z = calculate_zscore(df_ref, col, val, use_rel)
            if z is not None:
                kine_z_dict[label] = z
                
    avg_kine_z = sum(kine_z_dict.values()) / len(kine_z_dict) if kine_z_dict else None
    kine_comment_html = generate_kine_comment(kine_z_dict, avg_kine_z) if avg_kine_z is not None else ""

    zscore_html = ""
    if comp_zscores:
        zscore_html += f"""
        <div style="margin-bottom:20px;">
            <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:12px;">INDICES COMPOSITES (Z-SCORES)</div>
            <div style="display:flex; flex-wrap:wrap; gap:12px; justify-content:flex-start;">
        """
        for group, data in comp_zscores.items():
            # MODIFICATION: Limiter aux groupes kine pour éviter doublons en mode commun
            if group in GROUPES_KINE:
                zscore_html += get_zscore_gauge_html(group, data["score"], data["count"])
        zscore_html += "</div></div>"

    radar_b64 = create_radar_chart_kine(radar_labels, radar_values, radar_vals_d) if radar_labels else ""
    radar_html = f'''
    <div class="no-break" style="text-align:center; margin: 20px 0;">
        <img src="data:image/png;base64,{radar_b64}" style="width:100%; max-width:450px;">
        <div style="font-size:7pt; color:#888; margin-top:5px;">Radar Kiné : % par rapport à l'objectif (Cible = 100%, plage affichée 50%-150%). Seuils : <span style="color:#D71920;">Rouge &lt;80%</span>, <span style="color:#F39C12;">Orange 80-100%</span>, <span style="color:#27AE60;">Vert 100-120%</span>, <span style="color:#00E5FF;">Bleu &gt;120%</span>.</div>
    </div>
    ''' if radar_b64 else "<p style='font-size:8pt; color:#999; text-align:center;'>Aucune variable sélectionnée pour le radar.</p>"

    themes_html = ""
    for t in themes:
        themes_html += get_theme_card_html(t, is_report=True)
    if not themes_html: themes_html = "<p style='margin:0; font-size:9pt; color:#999;'>Aucune recommandation thématique définie.</p>"

    age_val = str(anthro.get('Age', '-')).strip()
    taille_val = str(anthro.get('Taille', '-')).strip()
    poids_val = str(anthro.get('Poids', '-')).strip()
    age_html = f"{age_val} <span style='font-size:7pt; color:#888; font-weight:normal;'>ans</span>" if age_val != "-" else "-"
    taille_html = f"{taille_val} <span style='font-size:7pt; color:#888; font-weight:normal;'>cm</span>" if taille_val != "-" else "-"
    poids_html = f"{poids_val} <span style='font-size:7pt; color:#888; font-weight:normal;'>kg</span>" if poids_val != "-" else "-"
    
    photo_img = f'<img src="data:image/png;base64,{photo_b64}" style="width:110px; height:110px; object-fit:cover; object-position:top center; display:block; border-radius:12px; border:2px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.08); flex-shrink:0;">' if photo_b64 else f'<div style="width:110px; height:110px; background:#f0f0f0; display:flex; align-items:center; justify-content:center; text-align:center; color:#aaa; font-weight:bold; font-size:32px; border-radius:12px; border:2px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.08); flex-shrink:0; line-height:110px;">{player_name[:1]}</div>'
    logo_img = f'<img src="data:image/{logo_ext};base64,{logo_b64}" style="width:75px; margin-bottom:5px;">' if logo_b64 else ''
    
    legend_html = f"""
    <div class="no-break" style="margin-top:15px; margin-bottom:15px; padding:12px; background:#f8f9fa; border:1px solid #e9ecef; border-radius:8px; font-size:8pt; color:#495057; box-shadow: 0 2px 4px rgba(0,0,0,0.02); width:100%; box-sizing:border-box;">
        <div style="display:flex; justify-content:space-around; align-items:flex-start;">
            <div style="flex:1;">
                <div style="font-weight:bold; color:#333; margin-bottom:6px; font-size:7.5pt; letter-spacing:0.5px;">🎯 STATUT OBJECTIF</div>
                <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{GREEN};"><div style="width:8px; height:8px; border-radius:50%; background:{GREEN};"></div> Acquis</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{ORANGE};"><div style="width:8px; height:8px; border-radius:50%; background:{ORANGE};"></div> Proche</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{SDR_RED};"><div style="width:8px; height:8px; border-radius:50%; background:{SDR_RED};"></div> Non Acquis</span>
                </div>
            </div>
            <div style="flex:2; border-left:1px dashed #ccc; padding-left:15px;">
                <div style="font-weight:bold; color:#333; margin-bottom:6px; font-size:7.5pt; letter-spacing:0.5px;">📊 RANG (Percentile vs Référence)</div>
                <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{BLUE_ELITE};"><div style="width:10px; height:4px; border-radius:2px; background:{BLUE_ELITE};"></div> Élite (≥ 95% / Z ≥ 1.65)</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{GREEN};"><div style="width:10px; height:4px; border-radius:2px; background:{GREEN};"></div> Bon (≥ 66%)</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{ORANGE};"><div style="width:10px; height:4px; border-radius:2px; background:{ORANGE};"></div> Moyen (≥ 33%)</span>
                    <span style="display:flex; align-items:center; gap:4px; font-weight:bold; color:{SDR_RED};"><div style="width:10px; height:4px; border-radius:2px; background:{SDR_RED};"></div> Flop (&lt; 33%)</span>
                </div>
            </div>
        </div>
    </div>
    """

    css = f"""
    <style>
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; background: #eee; margin:0; padding:0; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        .report-container {{ background: white; max-width: 210mm; margin: 10px auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); padding: 10mm 15mm 20mm 15mm; box-sizing: border-box; position: relative; }}
        .page-break {{ page-break-before: always; margin-top: 20px; }}
        .no-break {{ page-break-inside: avoid; break-inside: avoid; }}
        .footer-print {{ display: none; }}
        
        @media print {{
            @page {{ size: A4; margin: 12mm 15mm; }}
            body {{ background: white; margin: 0; padding: 0; }}
            .report-container {{ margin: 0; box-shadow: none; max-width: 100%; padding: 0; width: 100%; }}
            .page-break {{ margin-top: 0; padding-top: 0; }}
            .footer-print {{ display: flex !important; position: fixed; bottom: 0; left: 0; right: 0; justify-content: space-between; font-size: 7pt; color: #aaa; border-top: 1px solid #eee; padding: 5px 0 0 0; background: white; }}
        }}
    </style>
    """

    context_html = f"<div style='margin-top:10px; font-size:8.5pt; color:#666; overflow-wrap: break-word;'><b>Contexte du test :</b> {context_test}</div>" if context_test else ""

    header_html = f"""
        <div class="no-break" style="display:flex; justify-content:space-between; align-items:center; border-bottom: 3px solid {SDR_RED}; padding-bottom: 15px; margin-bottom: 15px;">
            <div style="display:flex; align-items:center; gap: 20px; flex-grow:1;">
                {photo_img}
                <div style="flex-grow:1; display:flex; flex-direction:column; justify-content:center;">
                    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:5px;">
                        <h1 style="margin:0; color:{SDR_RED}; font-size:26pt; font-weight:900; text-transform:uppercase; line-height:1; overflow-wrap: break-word;">
                            {player_name}
                        </h1>
                    </div>
                    <div style="font-size:11pt; font-weight:bold; color:#555; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">
                        {poste} &bull; {latéralité}
                    </div>
                    <div style="display:flex; gap:10px; width:100%;">
                        <div style="flex:1; background:#f8f9fa; border:1px solid #eee; padding:6px; border-radius:6px; text-align:center;">
                            <span style="color:#888; font-size:7pt; text-transform:uppercase; display:block;">Âge</span>
                            <span style="font-weight:900; font-size:11pt; color:{DARK};">{age_html}</span>
                        </div>
                        <div style="flex:1; background:#f8f9fa; border:1px solid #eee; padding:6px; border-radius:6px; text-align:center;">
                            <span style="color:#888; font-size:7pt; text-transform:uppercase; display:block;">Taille</span>
                            <span style="font-weight:900; font-size:11pt; color:{DARK};">{taille_html}</span>
                        </div>
                        <div style="flex:1; background:#f8f9fa; border:1px solid #eee; padding:6px; border-radius:6px; text-align:center;">
                            <span style="color:#888; font-size:7pt; text-transform:uppercase; display:block;">Poids</span>
                            <span style="font-weight:900; font-size:11pt; color:{DARK};">{poids_html}</span>
                        </div>
                    </div>
                    {context_html}
                </div>
            </div>
            <div style="text-align:right; border-left:2px solid #eee; padding-left:20px; margin-left:20px; min-width:100px;">
                {logo_img}
                <div style="font-weight:900; color:#333; font-size:8.5pt; text-transform:uppercase; line-height:1.3; margin-top:5px; overflow-wrap: break-word;">
                    Département<br><span style="color:{SDR_RED}">Performance</span>
                </div>
            </div>
        </div>
        <div class="no-break" style="font-size:8pt; color:#666; background:#eefaf3; border:1px solid {GREEN}; padding:6px 12px; border-radius:4px; display:inline-block; margin-bottom:15px; font-weight:bold; overflow-wrap: break-word;">
            Comparé à : {ref_group_label}
        </div>
    """

    dominant_txt = dominant.strip() if dominant else ""
    weak_txt = weak.strip() if weak else ""
    strat_salle_txt = strat_salle.strip() if strat_salle else ""

    strategy_html = f"""
        <div class="no-break" style="padding:10px 14px; margin-bottom:10px; border-radius:6px; border-left:6px solid #3498DB; background:#f0f7fd; word-wrap: break-word; overflow-wrap: break-word;">
            <div style="color:#3498DB; font-weight:bold; font-size:9pt; margin-bottom:4px;">STRATÉGIE DE PRISE EN CHARGE</div>
            <div style="font-size:8.5pt; color:#333; white-space: pre-wrap; margin:0; padding:0;">{strat_salle_txt}</div>
        </div>
    """

    # MODIFICATION: Gestion du mode "Commun" pour extraire uniquement la section Kiné sans la page de reco
    if is_commun:
        doc_html = f"""
<!-- MARQUEUR_DETAIL_START -->
        <div class="page-break"></div>
        <div class="report-section">
            <div class="no-break" style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 16px;">
                <h2 style="margin:0; color:{DARK}; font-size:14pt; text-transform:uppercase;">Détail des Métriques (Kiné)</h2>
                <div style="font-size:10pt; color:#888; font-weight:bold;">{player_name}</div>
            </div>
            {zscore_html}
            {radar_html}
            {asym_html}
            {biodex_html}
            {metrics_html}
        </div>
<!-- MARQUEUR_DETAIL_END -->
        """
    else:
        doc_html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">{css}</head><body>
    <div class="report-container">
        
        <div class="report-section">
            {header_html}
            {zscore_html}
            {radar_html}
            {legend_html}
        </div>
        
        <div class="page-break"></div>
        <div class="report-section">
            <div class="no-break" style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 16px;">
                <h2 style="margin:0; color:{DARK}; font-size:14pt; text-transform:uppercase;">Détail des Métriques</h2>
                <div style="font-size:10pt; color:#888; font-weight:bold;">{player_name}</div>
            </div>
            {asym_html}
            {biodex_html}
            {metrics_html}
        </div>

        <div class="page-break"></div>
        <div class="report-section">
            <div class="no-break" style="display:flex; align-items:center; gap: 20px; border-bottom: 3px solid {SDR_RED}; padding-bottom: 15px; margin-bottom: 20px;">
                {photo_img}
                <div>
                    <h1 style="margin:0; color:{SDR_RED}; font-size:24pt; text-transform:uppercase; line-height:1; overflow-wrap: break-word;">{player_name}</h1>
                    <div style="font-size:12pt; font-weight:bold; color:#555; text-transform:uppercase; margin-top:4px;">Bilan, Thématiques & Entretien</div>
                </div>
            </div>
            
            <div class="no-break" style="margin-bottom: 20px; margin-top: 10px;">
                <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:12px;">RECOMMANDATIONS THÉMATIQUES</div>
                <div style="display: flex; flex-wrap: wrap; gap: 15px;">{themes_html}</div>
            </div>

            <div class="no-break" style="margin-top:20px;">
                <div style="font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:4px; margin-bottom:12px;">SYNTHÈSE</div>
                <div class="no-break" style="padding:10px 14px; margin-bottom:10px; border-radius:6px; border-left:6px solid {GREEN}; background:#eefaf3; word-wrap: break-word; overflow-wrap: break-word;">
                    <div style="color:{GREEN}; font-weight:bold; font-size:9pt; margin-bottom:4px;">POINT(S) FORT(S)</div>
                    <div style="font-size:8.5pt; color:#333; white-space: pre-wrap; margin:0; padding:0;">{dominant_txt}</div>
                </div>
                <div class="no-break" style="padding:10px 14px; margin-bottom:10px; border-radius:6px; border-left:6px solid {SDR_RED}; background:#fef5f5; word-wrap: break-word; overflow-wrap: break-word;">
                    <div style="color:{SDR_RED}; font-weight:bold; font-size:9pt; margin-bottom:4px;">AXES D'AMÉLIORATION</div>
                    <div style="font-size:8.5pt; color:#333; white-space: pre-wrap; margin:0; padding:0;">{weak_txt}</div>
                </div>
                {strategy_html}
            </div>
            
            <div class="no-break" style="margin-top:20px; border:1px solid #ccc; border-radius:8px; padding:15px; background:#fafafa;">
                <div style="font-weight:bold; color:#555; font-size:9pt; margin-bottom:8px; text-transform:uppercase;">Conclusion de l'entretien</div>
                <div style="display:flex; justify-content:space-between; font-size:8.5pt; margin-bottom:8px;">
                    <div><b>Date de l'entretien :</b> {entretien_date if entretien_date else "...................."}</div>
                </div>
                <div style="font-size:8.5pt;"><b>Prochain RDV / Test :</b> {rdv_date if rdv_date else "........................................"}</div>
            </div>
        </div>
        
        <div class="footer-print">
            <span>Département Performance · Stade de Reims</span>
            <span>Document confidentiel — usage interne club</span>
        </div>
    </div>
    </body></html>
        """
    return doc_html

file_path = "Profilage 2026-2027.xlsx"

if not os.path.exists(file_path):
    st.error(f"Fichier introuvable : {file_path}")
    st.stop()

df = pd.read_excel(file_path)
df.columns = [str(c).strip() for c in df.columns]

if "Session" in df.columns:
    df["Session"] = df["Session"].astype(str)

col_session = "Session" if "Session" in df.columns else None
sessions_list = []
sel_session = None
df_prev_session = None

if col_session:
    sessions_list = sorted(df[col_session].dropna().unique().tolist())
    
    default_idx = len(sessions_list) - 1
    for i, s in enumerate(sessions_list):
        if "pré-saison" in str(s).lower() or "pre-saison" in str(s).lower():
            default_idx = i
            break
            
    sel_session = st.sidebar.selectbox("Session Analysée", sessions_list, index=default_idx)
    df_session = df[df[col_session] == sel_session]
else:
    df_session = df

teams = sorted(df_session["Equipe"].dropna().astype(str).unique().tolist())
if not teams:
    st.warning("Aucune équipe trouvée pour cette sélection.")
    st.stop()
default_team_idx = teams.index("PRO") if "PRO" in teams else 0
team_sel = st.sidebar.selectbox("Équipe", teams, index=default_team_idx)

df_team = df_session[df_session["Equipe"] == team_sel]
players = sorted(df_team["Joueur"].dropna().unique().tolist())

if not players:
    st.warning("Aucun joueur trouvé pour cette équipe.")
    st.stop()
p_sel = st.sidebar.selectbox("Joueur à profiler", players)
row = df_team[df_team["Joueur"] == p_sel].iloc[0]

if col_session and len(sessions_list) > 1:
    curr_idx = sessions_list.index(sel_session)
    if curr_idx > 0:
        prev_session_val = sessions_list[curr_idx - 1]
        df_prev_filter = df[(df["Joueur"] == p_sel) & (df[col_session] == prev_session_val)]
        if not df_prev_filter.empty:
            df_prev_session = df_prev_filter

poste = row.get(COL_MAPPING["Poste"], "-")
latéralité = row.get("Latéralité", "-")
p_equipe = row.get("Equipe", "-")
p_age = clean_numeric_value(row.get("Age"), "Age")

anthro = {"Age": int(p_age) if p_age is not None else "-", "Taille": row.get("Taille (cm)", "-"), "Poids": row.get("Poids (kg)", "-")}

key_suffix = f"{p_sel}_{sel_session}"

# MODIFICATION: Autoriser les paramètres kiné dans le menu latéral en mode Commun
if report_mode in ["Kiné / Prévention", "Commun (Complet)"]:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Contexte & Antécédents")
    antecedents_kine = st.sidebar.text_input("Antécédents médicaux (ex: ischio, pubalgie, cheville...)", key=f"ant_{key_suffix}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Latéralité (Correction)")
    lat_val = str(latéralité).strip().upper()
    default_frappe = "G" if lat_val == "G" else "D"
    default_appui = "G" if default_frappe == "D" else "D"
    jambe_frappe = st.sidebar.selectbox("Jambe Dominante (Frappe)", ["D", "G"], index=0 if default_frappe=="D" else 1, key=f"frappe_{key_suffix}")
    jambe_appui = st.sidebar.selectbox("Jambe d'Appui", ["G", "D"], index=0 if default_appui=="G" else 1, key=f"appui_{key_suffix}")
    leg_overrides = {"frappe": jambe_frappe, "appui": jambe_appui}
else:
    antecedents_kine = ""
    leg_overrides = None

st.sidebar.markdown("---")
st.sidebar.subheader("Groupe de Comparaison")

col_age = "Age" if "Age" in df.columns else None
min_age_file = int(df_session[col_age].min(skipna=True)) if col_age else 14
max_age_file = int(df_session[col_age].max(skipna=True)) if col_age else 35

age_range = st.sidebar.slider("Fenêtre d'âge", min_value=min_age_file, max_value=max_age_file, value=(min_age_file, max_age_file))

choix_niveau = st.sidebar.selectbox("Niveau hiérarchique", ["Club entier", "Équipe", "Poste large", "Position précise"], index=1)

def get_ref_dataframe(niveau, df_base, r, a_range):
    d = df_base.copy()
    lbl = ""
    if niveau == "Club entier":
        lbl = "Club"
    elif niveau == "Équipe":
        d = d[d["Equipe"] == r.get("Equipe")]
        lbl = f"Équipe {r.get('Equipe')}"
    elif niveau == "Poste large":
        d = d[d[COL_MAPPING["Poste"]] == r.get(COL_MAPPING["Poste"])]
        lbl = f"Poste {r.get(COL_MAPPING['Poste'])}"
    elif niveau == "Position précise":
        p = r.get("Position", r.get(COL_MAPPING["Poste"]))
        d = d[d["Position"] == p] if "Position" in d.columns else d[d[COL_MAPPING["Poste"]] == p]
        lbl = f"Position {p}"
    
    if col_age and (a_range[0] > min_age_file or a_range[1] < max_age_file):
        d = d[(d[col_age] >= a_range[0]) & (d[col_age] <= a_range[1])]
        lbl += f", {a_range[0]}-{a_range[1]} ans"
        
    return d, lbl

df_ref, ref_label = get_ref_dataframe(choix_niveau, df_session, row, age_range)
n_ref = len(df_ref)

if n_ref < 8:
    st.sidebar.warning(f"⚠️ Échantillon réduit (n={n_ref}). Percentile peu fiable.")
    forcer = st.sidebar.checkbox("Forcer le calcul quand même", value=False)
    
    if not forcer:
        niveaux_repli = ["Club entier", "Équipe", "Poste large", "Position précise"]
        idx_actuel = niveaux_repli.index(choix_niveau)
        repli_trouve = False
        for i in range(idx_actuel - 1, -1, -1):
            d_repli, l_repli = get_ref_dataframe(niveaux_repli[i], df_session, row, age_range)
            if len(d_repli) >= 8:
                df_ref = d_repli
                ref_label = l_repli
                n_ref = len(df_ref)
                st.sidebar.info(f"Repli automatique sur : {niveaux_repli[i]} (n={n_ref})")
                repli_trouve = True
                break
        if not repli_trouve:
            df_ref, ref_label = get_ref_dataframe("Club entier", df_session, row, (min_age_file, max_age_file))
            n_ref = len(df_ref)
            st.sidebar.info(f"Repli automatique total (n={n_ref})")

ref_group_label = f"{ref_label} (n={n_ref})"

st.sidebar.markdown("---")
st.sidebar.subheader("Variables & Évaluation")

player_metrics_key = f"selected_metrics_{key_suffix}"
saved_data_all = load_profiling_data()
saved_data_player = saved_data_all.get(key_suffix, {})

if player_metrics_key not in st.session_state:
    if "selected_metrics" in saved_data_player:
        st.session_state[player_metrics_key] = set(saved_data_player["selected_metrics"])
    else:
        auto_sel = set()
        for grp, lbls in GROUPES.items():
            if report_mode == "Kiné / Prévention" and "Biodex" in grp:
                continue
            for l in lbls:
                c = find_column(df_session, l)
                if c and pd.notna(row.get(c)):
                    auto_sel.add(l)
        st.session_state[player_metrics_key] = auto_sel

if "use_relative" not in st.session_state:
    st.session_state.use_relative = saved_data_player.get("use_relative", {})

staff_evals = {}

for group, labels in GROUPES.items():
    with st.sidebar.expander(group, expanded=False):
        for label in labels:
            col = find_column(df_session, label)
            has_data = col is not None
            checked = st.checkbox(label, value=(label in st.session_state[player_metrics_key]), key=f"chk_{label}_{key_suffix}", disabled=not has_data)
            if checked:
                st.session_state[player_metrics_key].add(label)
                
                unit = UNITS.get(label, "")
                can_be_rel = unit in ["N", "W", "Nm"] and "Poids (kg)" in df_session.columns
                if can_be_rel:
                    st.session_state.use_relative[label] = st.checkbox(f"→ Relatif ({unit}/kg)", value=st.session_state.use_relative.get(label, False), key=f"rel_{label}_{key_suffix}")
                
                st.markdown(f"**Statut pour {label}**")
                
                v_metric = get_value_for_metric(row, df_session, col, st.session_state.use_relative.get(label, False)) if col else None
                _, v_pct = calculate_percentile(df_ref, col, v_metric, st.session_state.use_relative.get(label, False)) if col and v_metric is not None else (None, None)
                statut_def, obj_def = auto_eval_metric(label, v_metric, v_pct, st.session_state.use_relative.get(label, False))
                    
                statut_opts = ["Acquis", "Proche", "Non Acquis"]
                saved_eval = saved_data_player.get("staff_evals", {}).get(label, {})
                saved_statut = saved_eval.get("statut", statut_def)
                idx_statut = statut_opts.index(saved_statut) if saved_statut in statut_opts else 0
                
                statut = st.radio("Acquis ?", statut_opts, horizontal=True, key=f"statut_{label}_{key_suffix}", index=idx_statut)
                
                obj_val = ""
                delai_val = ""
                if statut != "Acquis":
                    saved_obj = saved_eval.get("objectif", obj_def)
                    if report_mode == "Préparation Physique":
                        obj_val = st.text_input("Objectif", value=saved_obj, key=f"obj_{label}_{key_suffix}")
                    else:
                        c_obj, c_delai = st.columns(2)
                        with c_obj:
                            obj_val = st.text_input("Objectif", value=saved_obj, key=f"obj_{label}_{key_suffix}")
                        with c_delai:
                            delai_opts = ["", "1 semaine", "2 semaines", "3 semaines", "1 mois", "2 mois", "+ de 3 mois"]
                            saved_delai = saved_eval.get("delai", "")
                            delai_idx = delai_opts.index(saved_delai) if saved_delai in delai_opts else 0
                            delai_val = st.selectbox("Délai", delai_opts, index=delai_idx, key=f"delai_{label}_{key_suffix}")
                staff_evals[label] = {"statut": statut, "objectif": obj_val, "delai": delai_val}
                st.markdown("---")
            else:
                st.session_state[player_metrics_key].discard(label)

selected_metrics = st.session_state[player_metrics_key]

photo_b64_ui = img_to_b64(get_best_photo_path(p_sel))
img_html_ui = f'<img src="data:image/png;base64,{photo_b64_ui}" style="width: 120px; height: 120px; border-radius: 12px; border: 4px solid {SDR_RED}; object-fit: cover; object-position: top center; box-shadow: 0 4px 10px rgba(215,25,32,0.2); background: #fff;">' if photo_b64_ui else f'<div style="width: 120px; height: 120px; border-radius: 12px; border: 4px solid {SDR_RED}; display:flex; align-items:center; justify-content:center; text-align:center; background:#eee; font-size:36px; font-weight:bold; color:#aaa; box-shadow: 0 4px 10px rgba(215,25,32,0.2); line-height:120px;">{p_sel[:1]}</div>'

age_val = str(anthro.get("Age", "-")).strip()
taille_val = str(anthro.get("Taille", "-")).strip()
poids_val = str(anthro.get("Poids", "-")).strip()

age_html_ui = f"{age_val} <span style='font-size:14px; color:#888; font-weight:normal;'>ans</span>" if age_val != "-" else "-"
taille_html_ui = f"{taille_val} <span style='font-size:14px; color:#888; font-weight:normal;'>cm</span>" if taille_val != "-" else "-"
poids_html_ui = f"{poids_val} <span style='font-size:14px; color:#888; font-weight:normal;'>kg</span>" if poids_val != "-" else "-"

st.markdown(f"""
<div style="background: #ffffff; border-top: 4px solid {SDR_RED}; border-bottom: 4px solid {SDR_RED}; padding: 25px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 20px rgba(215,25,32,0.08); margin-bottom: 25px; overflow-wrap: break-word;">
    <div style="display: flex; align-items: center; gap: 25px;">
        {img_html_ui}
        <div style="display: flex; flex-direction: column;">
            <div style="font-size: 42px; font-weight: 900; color: {SDR_RED}; text-transform: uppercase; line-height: 1; margin-bottom: 6px;">{p_sel}</div>
            <div style="font-size: 16px; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 1px;">{poste} · {latéralité}</div>
            <div style="font-size: 12px; font-weight: 600; color: {GREEN}; margin-top: 8px;">Comparaison : {ref_group_label}</div>
        </div>
    </div>
    <div style="display: flex; gap: 40px; padding-right: 20px; border-left: 2px dashed #eee; padding-left: 40px;">
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <div style="font-size: 12px; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">Âge</div>
            <div style="font-size: 32px; font-weight: 900; color: {SDR_RED};">{age_html_ui}</div>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <div style="font-size: 12px; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">Taille</div>
            <div style="font-size: 32px; font-weight: 900; color: {SDR_RED};">{taille_html_ui}</div>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <div style="font-size: 12px; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">Poids</div>
            <div style="font-size: 32px; font-weight: 900; color: {SDR_RED};">{poids_html_ui}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

context_test = st.selectbox("Contexte du test", ["Pré-saison", "En saison", "Reprise", "Fin de saison"], key=f"contexte_{key_suffix}")

comp_zscores = {}
for group, labels in GROUPES.items():
    if group == "Ratio Mixte" and report_mode != "Kiné / Prévention" and report_mode != "Commun (Complet)": continue
    z_list = []
    for label in labels:
        if label in selected_metrics:
            col = find_column(df_session, label)
            use_rel = st.session_state.use_relative.get(label, False)
            val = get_value_for_metric(row, df_session, col, use_rel) if col else None
            z = calculate_zscore(df_ref, col, val, use_rel)
            if z is not None:
                z_list.append(z)
    if z_list:
        comp_zscores[group] = {"score": sum(z_list) / len(z_list), "count": len(z_list)}

c1, c2 = st.columns([1.5, 1])

with c1:
    st.markdown("**Aperçu des variables sélectionnées**")
    if not selected_metrics:
        st.caption("Sélectionne des variables dans la barre latérale pour construire le rapport.")
    
    sorted_groups_ui = list(GROUPES.items())
    if report_mode in ["Kiné / Prévention", "Commun (Complet)"] and antecedents_kine:
        prioritaires_ui = []
        ant_lower_ui = antecedents_kine.lower()
        for lbl in selected_metrics:
            is_prio = False
            lbl_lower = lbl.lower()
            if "ischio" in ant_lower_ui and ("ij" in lbl_lower or "ischio" in lbl_lower or "mixte" in lbl_lower): is_prio = True
            elif ("adducteur" in ant_lower_ui or "pubalgie" in ant_lower_ui) and ("add" in lbl_lower or "abd" in lbl_lower or "squeeze" in lbl_lower): is_prio = True
            elif "cheville" in ant_lower_ui and ("verseur" in lbl_lower): is_prio = True
            elif "quadri" in ant_lower_ui and ("q conc" in lbl_lower or "quadri" in lbl_lower): is_prio = True
            if is_prio: prioritaires_ui.append(lbl)
        if prioritaires_ui:
            sorted_groups_ui.insert(0, ("Priorité Antécédents", prioritaires_ui))

    for group, labels in sorted_groups_ui:
        if group == "Ratio Mixte" and report_mode not in ["Kiné / Prévention", "Commun (Complet)"]: continue
        
        group_cards_html = ""
        for label in labels:
            if label not in selected_metrics: continue
            
            if group != "Priorité Antécédents" and antecedents_kine and any(label in p_list for g, p_list in sorted_groups_ui if g == "Priorité Antécédents"):
                continue

            col = find_column(df_session, label)
            use_rel = st.session_state.use_relative.get(label, False)
            value = get_value_for_metric(row, df_session, col, use_rel) if col else None
            
            unit = UNITS.get(label, "")
            if use_rel and unit:
                unit = f"{unit}/kg"
                
            _, pct = calculate_percentile(df_ref, col, value, use_rel) if col and value is not None else (None, None)
            z_score = calculate_zscore(df_ref, col, value, use_rel) if col and value is not None else None
            
            prev_val = None
            if df_prev_session is not None and col in df_prev_session.columns:
                prev_val = get_value_for_metric(df_prev_session.iloc[0], df_session, col, use_rel)

            eval_data = staff_evals.get(label, None)
            group_cards_html += get_metric_card_html(label, col, value, unit, pct, z_score, eval_data, prev_val, use_rel, is_report=False, is_kine=(report_mode in ["Kiné / Prévention", "Commun (Complet)"] and label in KINE_LABELS))
            
        if group_cards_html:
            st.markdown(f"<div style='font-weight:900; color:{SDR_RED}; font-size:10pt; text-transform:uppercase; border-bottom:2px solid #eee; padding-bottom:6px; margin-bottom:10px; margin-top:15px;'>{group}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:8px;'>{group_cards_html}</div>", unsafe_allow_html=True)

with c2:
    st.markdown("**Variables pour le radar**")
    
    # MODIFICATION: Gestion de l'affichage des deux sections Radar en mode Commun
    radar_labels_prepa, radar_values_prepa = [], []
    radar_labels_kine, radar_values_kine, radar_vals_d_kine = [], [], []

    if report_mode in ["Préparation Physique", "Commun (Complet)"]:
        if report_mode == "Commun (Complet)": st.markdown("*(Radar Préparation Physique)*")
        radar_options_prepa = sorted([m for m in selected_metrics if m in GROUPES_PREPA.get("Force", []) or m in GROUPES_PREPA.get("Puissance", []) or m in GROUPES_PREPA.get("Saut", [])])
        default_radar_prepa = radar_options_prepa[:8]
        radar_selection_prepa = st.multiselect("Choix radar Prépa", radar_options_prepa, default=default_radar_prepa, label_visibility="collapsed", key=f"radar_sel_prepa_{key_suffix}")

        for label in radar_selection_prepa:
            col = find_column(df_session, label)
            use_rel = st.session_state.use_relative.get(label, False)
            value = get_value_for_metric(row, df_session, col, use_rel) if col else None
            
            _, pct = calculate_percentile(df_ref, col, value, use_rel) if col and value is not None else (None, None)
            if pct is not None:
                radar_labels_prepa.append(label.replace("(G)", "").replace("(D)", "").strip())
                radar_values_prepa.append(pct)

        if radar_labels_prepa:
            radar_b64_preview = create_radar_chart(radar_labels_prepa, radar_values_prepa)
            st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{radar_b64_preview}" style="width:100%; max-width:380px;"></div>', unsafe_allow_html=True)
        else:
            st.caption("Sélectionne au moins une variable numérique pour afficher le radar Prépa.")

    if report_mode in ["Kiné / Prévention", "Commun (Complet)"]:
        if report_mode == "Commun (Complet)": st.markdown("*(Radar Kiné / Prévention)*")
        biodex_bases = ["Q Conc 60°", "Q Conc 240°", "IJ Conc 60°", "IJ Conc 240°", "IJ Exc 30°"]
        base_kine_metrics = set()
        for m in selected_metrics:
            if "(G)" in m or "(D)" in m:
                base = m.replace("(G)", "").replace("(D)", "").strip()
                if base not in biodex_bases:
                    base_kine_metrics.add(base)
        radar_options_kine = sorted(list(base_kine_metrics))
        default_radar_kine = radar_options_kine[:8]
        radar_selection_kine = st.multiselect("Choix radar Kiné (bases G/D)", radar_options_kine, default=default_radar_kine, label_visibility="collapsed", key=f"radar_sel_kine_{key_suffix}")
        
        for base in radar_selection_kine[:8]:
            col_g = find_column(df_session, f"{base} (G)")
            col_d = find_column(df_session, f"{base} (D)")
            v_g = get_value_for_metric(row, df_session, col_g, st.session_state.use_relative.get(f"{base} (G)", False)) if col_g else None
            v_d = get_value_for_metric(row, df_session, col_d, st.session_state.use_relative.get(f"{base} (D)", False)) if col_d else None
            
            p_g = get_kine_radar_pct(f"{base} (G)", v_g, df_ref, col_g, st.session_state.use_relative.get(f"{base} (G)", False), row)
            p_d = get_kine_radar_pct(f"{base} (D)", v_d, df_ref, col_d, st.session_state.use_relative.get(f"{base} (D)", False), row)

            radar_labels_kine.append(base)
            radar_values_kine.append(p_g)
            radar_vals_d_kine.append(p_d)
            
        if radar_labels_kine:
            radar_b64_preview = create_radar_chart_kine(radar_labels_kine, radar_values_kine, radar_vals_d_kine)
            st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{radar_b64_preview}" style="width:100%; max-width:380px;"></div>', unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; font-size:12px; color:#888; margin-top:5px;'>Radar Kiné : % par rapport à l'objectif (Cible = 100%, plage affichée 50%-150%).<br>Seuils : <span style='color:#D71920;'>Rouge &lt;80%</span>, <span style='color:#F39C12;'>Orange 80-100%</span>, <span style='color:#27AE60;'>Vert 100-120%</span>, <span style='color:#00E5FF;'>Bleu &gt;120%</span>.</div>", unsafe_allow_html=True)
        else:
            st.caption("Sélectionne au moins une paire de variables numériques (G/D) pour afficher le radar Kiné.")
            
        st.markdown(f"<div style='margin-top:30px; margin-bottom:15px; font-size:18px; font-weight:900; color:{SDR_RED}; border-bottom:2px solid {SDR_RED}; padding-bottom:5px; text-transform:uppercase;'>RADAR BIODEX (VALEURS RELATIVES)</div>", unsafe_allow_html=True)
        targets = {
            "Q 60°": 3.1,
            "Q 240°": 2.2,
            "IJ 60°": 1.8,
            "IJ 240°": 1.5,
            "IJ Exc 30°": 2.4
        }
        
        biodex_full_config = [
            {"label": "Q 60°", "g_rel": "Q G conc 60°/s (N/kg)", "d_rel": "Q Dt conc 60°/s (N/kg)", "g_raw": "Q G conc 60°/s", "d_raw": "Q Dt conc 60°/s"},
            {"label": "Q 240°", "g_rel": "Q G conc 240°/s (N/kg)", "d_rel": "Q Dt conc 240°/s (N/kg)", "g_raw": "Q G conc 240°/s", "d_raw": "Q Dt conc 240°/s"},
            {"label": "IJ 60°", "g_rel": "IJ G conc 60°/s (N/kg)", "d_rel": "IJ Dt conc 60°/s (N/kg)", "g_raw": "IJ G conc 60°/s", "d_raw": "IJ Dt conc 60°/s"},
            {"label": "IJ 240°", "g_rel": "IJ G conc 240°/s (N/kg)", "d_rel": "IJ Dt conc 240°/s (N/kg)", "g_raw": "IJ G conc 240°/s", "d_raw": "IJ Dt conc 240°/s"},
            {"label": "IJ Exc 30°", "g_rel": "IJ G Exc 30°/s (N/kg)", "d_rel": "IJ Dt exc 30°/s (N/kg)", "g_raw": "IJ G Exc 30°/s", "d_raw": "IJ Dt exc 30°/s"}
        ]

        radar_cats, vals_l_rel, vals_r_rel, vals_norm, table_data = [], [], [], [], []
        poids_joueur = clean_numeric_value(row.get("Poids (kg)"))

        for item in biodex_full_config:
            lbl = item["label"]
            radar_cats.append(lbl)
            val_norm_rel = targets.get(lbl, 0)
            vals_norm.append(val_norm_rel)
            
            real_col_g_rel = find_column(df_session, item["g_rel"]) or item["g_rel"]
            real_col_d_rel = find_column(df_session, item["d_rel"]) or item["d_rel"]
            v_g_rel = clean_numeric_value(row.get(real_col_g_rel))
            v_d_rel = clean_numeric_value(row.get(real_col_d_rel))
            vals_l_rel.append(v_g_rel if v_g_rel is not None else 0)
            vals_r_rel.append(v_d_rel if v_d_rel is not None else 0)
            
            real_col_g_raw = find_column(df_session, item["g_raw"]) or item["g_raw"]
            real_col_d_raw = find_column(df_session, item["d_raw"]) or item["d_raw"]
            v_g_raw = clean_numeric_value(row.get(real_col_g_raw))
            v_d_raw = clean_numeric_value(row.get(real_col_d_raw))

            s_lsi, c_lsi = "-", "#888"
            if v_g_raw is not None and v_d_raw is not None:
                mx = max(v_g_raw, v_d_raw)
                if mx > 0:
                    lsi = ((v_d_raw - v_g_raw) / mx) * 100
                    s_lsi = f"{lsi:.0f}%"
                    c_lsi = "#D71920" if abs(lsi) > 10 else ("#F39C12" if abs(lsi) > 5 else "#27AE60")
            
            target_abs = f"{val_norm_rel * poids_joueur:.0f}" if poids_joueur and poids_joueur > 0 else "-"
            table_data.append({"label": lbl, "target": target_abs, "v_g": f"{v_g_raw:.0f}" if v_g_raw is not None else "-", "v_d": f"{v_d_raw:.0f}" if v_d_raw is not None else "-", "lsi": s_lsi, "c_lsi": c_lsi})

        col_radar, col_table = st.columns([1.2, 1]) 
        with col_radar:
            if not radar_cats:
                st.warning("Aucune donnée Biodex configurée trouvée.")
            else:
                import plotly.graph_objects as go
                max_data = max(max(vals_l_rel), max(vals_r_rel), max(vals_norm))
                limit_scale = max(4.0, max_data * 1.1)
                cats_closed = radar_cats + [radar_cats[0]]
                l_closed = vals_l_rel + [vals_l_rel[0]]
                r_closed = vals_r_rel + [vals_r_rel[0]]
                n_closed = vals_norm + [vals_norm[0]]
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=n_closed, theta=cats_closed, fill='toself', name='Objectif', mode='lines', line=dict(color='#2ECC71', dash='dash', width=2), fillcolor='rgba(46, 204, 113, 0.1)', hoverinfo='skip'))
                fig.add_trace(go.Scatterpolar(r=l_closed, theta=cats_closed, name='Gauche', mode='lines+markers', fill='toself', line=dict(color='#1ABC9C', width=3), marker=dict(size=8, color='#1ABC9C', symbol='circle'), fillcolor='rgba(26, 188, 156, 0.15)', hoveron='points', hovertemplate='<b>Gauche</b><br>%{theta}: <b>%{r:.2f}</b> N/kg<extra></extra>'))
                fig.add_trace(go.Scatterpolar(r=r_closed, theta=cats_closed, name='Droite', mode='lines+markers', fill='toself', line=dict(color='#9B59B6', width=3), marker=dict(size=8, color='#9B59B6', symbol='circle'), fillcolor='rgba(155, 89, 182, 0.15)', hoveron='points', hovertemplate='<b>Droite</b><br>%{theta}: <b>%{r:.2f}</b> N/kg<extra></extra>'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, limit_scale], showticklabels=True, tickfont=dict(color="#555", size=9), gridcolor="#eee", linecolor="#eee", layer="below traces"), angularaxis=dict(tickfont=dict(color="#111", size=12, weight="bold"), gridcolor="#eee", linecolor="#eee", layer="below traces"), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=20, b=20), showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(color="#111", size=12)), height=350, hovermode="closest")
                st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

        with col_table:
            st.markdown(f"<br><div style='text-align:center; font-size:15px; font-weight:900; color:{SDR_RED}; margin-bottom:10px; text-transform:uppercase;'>Résultats Détaillés (Nm)</div>", unsafe_allow_html=True)
            html_rows = ""
            for item in table_data:
                html_rows += f"<tr style='border-bottom:1px solid #eee;'><td style='padding:6px; color:#555;'>{item['label']}</td><td style='text-align:center; color:#888; font-weight:bold;'>{item['target']}</td><td style='text-align:center; color:#111; font-weight:bold;'>{item['v_g']}</td><td style='text-align:center; color:#111; font-weight:bold;'>{item['v_d']}</td><td style='text-align:center; color:{item['c_lsi']}; font-weight:bold;'>{item['lsi']}</td></tr>"
            col_rm_g, col_rm_d = find_column(df_session, "Ratio Mixte (G)") or "Ratio Mixte (G)", find_column(df_session, "Ratio Mixte (D)") or "Ratio Mixte (D)"
            val_rm_g, val_rm_d = clean_numeric_value(row.get(col_rm_g)), clean_numeric_value(row.get(col_rm_d))

            def get_ratio_color(val):
                if val is None: return "#888"
                return "#D71920" if val < 0.8 else ("#F39C12" if val <= 1.0 else "#27AE60")

            s_rm_g = f"{val_rm_g:.2f}" if val_rm_g is not None else "-"
            s_rm_d = f"{val_rm_d:.2f}" if val_rm_d is not None else "-"
            html_rows += f"<tr style='border-top:2px solid #ccc; background-color:#f9f9f9;'><td style='padding:6px; font-weight:bold; color:#111;'>Ratio Mixte</td><td style='text-align:center;'>-</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_g)};'>{s_rm_g}</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_d)};'>{s_rm_d}</td><td style='text-align:center;'>-</td></tr>"
            st.markdown(f"<table style='width:100%; border-collapse:collapse; font-size:12px; font-family:sans-serif;'><tr style='background-color:#f0f0f0; color:#333; text-transform:uppercase; font-size:10px;'><th style='padding:8px; text-align:left;'>Test</th><th style='padding:8px; text-align:center;'>Obj. (Nm)</th><th style='padding:8px; text-align:center;'>G (Nm)</th><th style='padding:8px; text-align:center;'>D (Nm)</th><th style='padding:8px; text-align:center;'>LSI</th></tr>{html_rows}</table>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px; color:#666; font-style:italic; margin-top:5px;'>* L'objectif brut (Nm) est calculé en multipliant la norme relative (N/kg) par le poids du joueur.</div>", unsafe_allow_html=True)

    legend_html_ui = f"""
    <div style="margin-top:15px; padding:10px; background:#f8f9fa; border:1px solid #e9ecef; border-radius:8px; font-size:12px; color:#495057;">
        <div style="font-weight:bold; color:#333; margin-bottom:8px;">📊 PAR RAPPORT AU GROUPE ({ref_group_label})</div>
        <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
            <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:{BLUE_ELITE};"><div style="width:12px; height:4px; border-radius:2px; background:{BLUE_ELITE};"></div> Élite (≥ 95% / Z ≥ 1.65)</span>
            <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:{GREEN};"><div style="width:12px; height:4px; border-radius:2px; background:{GREEN};"></div> Bon (≥ 66%)</span>
            <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:{ORANGE};"><div style="width:12px; height:4px; border-radius:2px; background:{ORANGE};"></div> Moyen (≥ 33%)</span>
            <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:{SDR_RED};"><div style="width:12px; height:4px; border-radius:2px; background:{SDR_RED};"></div> Flop (&lt; 33%)</span>
        </div>
    </div>
    """
    st.markdown(legend_html_ui, unsafe_allow_html=True)

st.markdown("---")
st.subheader("Recommandations Thématiques")

key_themes = f"themes_{key_suffix}"
saved_data_all = load_profiling_data()
saved_data_player = saved_data_all.get(key_suffix, {})

if key_themes not in st.session_state:
    if "themes" in saved_data_player:
        st.session_state[key_themes] = saved_data_player["themes"]
    else:
        auto = get_theme_suggestions_advanced(row, df_session)
        st.session_state[key_themes] = auto

ct1, ct2, ct3, ct4 = st.columns([2, 2, 2, 1])
with ct1:
    sel_etat = st.selectbox("État / Action", ETATS_ACTIONS)
with ct2:
    sel_qualite = st.selectbox("Qualité physique", QUALITES_PHYSIQUES)
with ct3:
    sel_zone = st.selectbox("Zone ciblée", ZONES_CIBLEES)
with ct4:
    st.write("")
    st.write("")
    if st.button("Ajouter", use_container_width=True):
        if len(st.session_state[key_themes]) < 3:
            st.session_state[key_themes].append({"id": str(uuid.uuid4()), "etat": sel_etat, "qualite": sel_qualite, "zone": sel_zone, "objectif": "", "freq": "1x/sem", "moment": "Pré séance"})
            st.rerun()
        else:
            st.warning("Max 3 recommandations pour faciliter l'entretien.")

if st.session_state[key_themes]:
    st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
    for i, t in enumerate(st.session_state[key_themes]):
        tid = t.get("id", str(i))
        cols_t = st.columns([2, 1.5, 1.5, 2, 1])
        with cols_t[0]:
            st.markdown(get_theme_card_html(t, is_report=False), unsafe_allow_html=True)
        with cols_t[1]:
            freq_opts = ["1x/sem", "2x/sem", "3x/sem", "4x/sem", "5x+/sem"]
            t["freq"] = st.selectbox("Fréquence", freq_opts, index=freq_opts.index(t.get("freq", "1x/sem")), key=f"freq_{tid}_{key_suffix}")
        with cols_t[2]:
            mom_opts = ["Pré séance", "Post séance", "Maison"]
            t["moment"] = st.selectbox("Moment", mom_opts, index=mom_opts.index(t.get("moment", "Pré séance")), key=f"mom_{tid}_{key_suffix}")
        with cols_t[3]:
            t["objectif"] = st.text_input("Objectif", value=t.get("objectif", ""), key=f"obj_th_{tid}_{key_suffix}")
        with cols_t[4]:
            st.write("")
            st.write("")
            if st.button("Retirer", key=f"del_{tid}_{key_suffix}"):
                st.session_state[key_themes].pop(i)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.caption("Aucune recommandation thématique. Utilise les menus ci-dessus pour en ajouter.")

st.markdown("---")
st.subheader("Entretien & Synthèse")

derniere_mod = saved_data_player.get("last_modified", "Jamais")
st.caption(f"Dernière modification : {derniere_mod}")

c_ent1, c_ent2 = st.columns(2)
with c_ent1:
    entretien_date = st.text_input("Date de l'entretien", value=saved_data_player.get("entretien_date", ""), key=f"ent_date_{key_suffix}")
with c_ent2:
    rdv_date = st.text_input("Prochain RDV / Test", value=saved_data_player.get("rdv_date", ""), key=f"rdv_date_{key_suffix}")

d1, d2 = st.columns(2)
with d1:
    dominant = st.text_area("Points forts", value=saved_data_player.get("dominant", ""), key=f"dominant_{key_suffix}", height=100)
    
    if report_mode in ["Préparation Physique", "Commun (Complet)"]:
        strat_salle = st.text_area("Stratégie Salle", value=saved_data_player.get("strat_salle", ""), key=f"strat_salle_{key_suffix}", height=100)
        strat_terrain = st.text_area("Stratégie Terrain", value=saved_data_player.get("strat_terrain", ""), key=f"strat_terrain_{key_suffix}", height=100)
    else:
        strat_salle = st.text_area("Stratégie de prise en charge", value=saved_data_player.get("strat_salle", ""), key=f"strat_salle_{key_suffix}", height=100)
        strat_terrain = ""
with d2:
    weak = st.text_area("Axes d'amélioration", value=saved_data_player.get("weak", ""), key=f"weak_{key_suffix}", height=100)

if st.button("💾 Sauvegarder Profilage"):
    saved_data_all[key_suffix] = {
        "entretien_date": entretien_date,
        "rdv_date": rdv_date,
        "dominant": dominant,
        "weak": weak,
        "strat_salle": strat_salle,
        "strat_terrain": strat_terrain,
        "themes": st.session_state[key_themes],
        "selected_metrics": list(st.session_state[player_metrics_key]),
        "use_relative": st.session_state.use_relative,
        "staff_evals": staff_evals,
        "last_modified": datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    }
    
    with st.spinner("Sauvegarde en cours sur GitHub..."):
        success = save_profiling_data(saved_data_all, key_suffix)
        if success:
            st.success("Sauvegardé et synchronisé sur GitHub avec succès !")
            st.rerun()

st.markdown("---")

st.info("💡 **Pour une impression parfaite :** Lors de l'impression (Ctrl+P / Cmd+P), pensez à **décocher 'En-têtes et pieds de page'** dans les options de votre navigateur pour retirer les URL en haut et en bas de page.")

# MODIFICATION: Gestion de l'assemblage HTML au moment de générer le rapport
if st.button("Générer le rapport HTML", type="primary"):
    photo_b64 = img_to_b64(get_best_photo_path(p_sel))
    logo_b64, logo_ext = get_logo_b64()
    
    if report_mode == "Préparation Physique":
        html_report = build_prepa_report(
            p_sel, row, df_ref, df, poste, latéralité, anthro,
            selected_metrics, st.session_state.use_relative,
            radar_labels_prepa, radar_values_prepa,
            st.session_state[key_themes], dominant, weak, strat_salle, strat_terrain,
            photo_b64, logo_b64, logo_ext, staff_evals, 
            sel_session, df_prev_session, rdv_date, entretien_date, context_test,
            ref_group_label, comp_zscores
        )
    elif report_mode == "Kiné / Prévention":
        html_report = build_kine_report(
            p_sel, row, df_ref, df, poste, latéralité, anthro,
            selected_metrics, st.session_state.use_relative,
            radar_labels_kine, radar_values_kine,
            st.session_state[key_themes], dominant, weak, strat_salle, strat_terrain,
            photo_b64, logo_b64, logo_ext, staff_evals, 
            sel_session, df_prev_session, rdv_date, entretien_date, context_test,
            ref_group_label, comp_zscores, antecedents_kine, leg_overrides, radar_vals_d_kine
        )
    else:
        # Création des deux morceaux avec l'argument is_commun=True pour arrêter/scinder correctement
        html_prepa = build_prepa_report(
            p_sel, row, df_ref, df, poste, latéralité, anthro,
            selected_metrics, st.session_state.use_relative,
            radar_labels_prepa, radar_values_prepa,
            st.session_state[key_themes], dominant, weak, strat_salle, strat_terrain,
            photo_b64, logo_b64, logo_ext, staff_evals, 
            sel_session, df_prev_session, rdv_date, entretien_date, context_test,
            ref_group_label, comp_zscores, is_commun=True
        )
        html_kine = build_kine_report(
            p_sel, row, df_ref, df, poste, latéralité, anthro,
            selected_metrics, st.session_state.use_relative,
            radar_labels_kine, radar_values_kine,
            st.session_state[key_themes], dominant, weak, strat_salle, strat_terrain,
            photo_b64, logo_b64, logo_ext, staff_evals, 
            sel_session, df_prev_session, rdv_date, entretien_date, context_test,
            ref_group_label, comp_zscores, antecedents_kine, leg_overrides, radar_vals_d_kine, is_commun=True
        )
        
        # Concaténation fine des parties via les marqueurs HTML pour générer un rapport combiné page par page unique
        parts_prepa = html_prepa.split("<!-- MARQUEUR_RECO -->")
        parts_kine = html_kine.split("<!-- MARQUEUR_DETAIL_START -->")[1].split("<!-- MARQUEUR_DETAIL_END -->")[0]
        html_report = parts_prepa[0] + parts_kine + "<!-- MARQUEUR_RECO -->" + parts_prepa[1]
        
    b64 = base64.b64encode(html_report.encode('utf-8')).decode('utf-8')
    st.success("Rapport généré.")
    st.markdown(
        f'<a href="data:text/html;base64,{b64}" download="Profilage_{p_sel}.html">'
        f'<button style="background:{SDR_RED}; color:white; padding:10px 18px; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">TÉLÉCHARGER LE RAPPORT</button></a>',
        unsafe_allow_html=True
    )
    with st.expander("Aperçu du rapport"):
        st.components.v1.html(html_report, height=900, scrolling=True)

# streamlit run app.py