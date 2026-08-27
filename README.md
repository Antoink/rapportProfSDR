# Rapport de Profilage — Stade de Reims (version modulaire)

Refonte de l'application Streamlit de restitution du profilage joueurs.
Fonctionnalités et rendu visuel identiques à l'ancienne version : l'objectif
de cette passe était la **fiabilité** et la **maintenabilité**, pas de tout
réinventer.

## 1. Ce qui a changé

### Architecture : 1 fichier de 2115 lignes → 11 modules
```
config.py            constantes (couleurs, mapping colonnes, normes, unités, groupes)
data_loader.py        chargement + nettoyage numérique du fichier Excel
stats_engine.py       percentile, z-score, évaluation auto vs normes
charts.py              radars matplotlib + courbes d'évolution (PNG base64)
html_components.py    briques HTML communes aux 2 rapports (cartes, légende, CSS)
suggestions.py         suggestion automatique de 3 thématiques de travail
report_prepa.py        rapport "Préparation Physique"
report_kine.py         rapport "Kiné / Prévention"
persistence.py         sauvegarde/chargement des commentaires (GitHub JSON)
pdf_export.py           conversion HTML -> PDF (WeasyPrint)
app.py                  orchestration Streamlit (UI uniquement)
```
Chaque module a une seule responsabilité et peut être testé isolément
(`smoke_test.py` en donne un exemple, sans dépendance à Streamlit — utile
si tu veux réutiliser `data_loader`/`stats_engine` dans un notebook pour ta
thèse).

### Bugs corrigés

1. **Fichier introuvable (bloquant)** — l'app cherchait en dur
   `"Profilage 2026-2027.xlsx"` (espace) alors que le fichier réel est
   `"Profilage_2026-2027.xlsx"` (underscore). `data_loader.locate_excel_file()`
   détecte maintenant automatiquement le `.xlsx` du dossier, donc un
   renommage d'une saison à l'autre ne casse plus l'app.

2. **`load_profiling_data()` appelée à chaque interaction** — chaque case
   cochée dans la sidebar déclenchait un appel à l'API GitHub. Mis en cache
   (`st.cache_data(ttl=60)`), invalidé explicitement juste après une
   sauvegarde réussie.

3. **Conflit d'écriture GitHub non géré** — si deux membres du staff
   sauvegardent en même temps, l'écriture échouait silencieusement (sha
   périmé). `persistence.save_profiling_data()` retente une fois.

4. **Code mort** — `json.dump_s` (n'existe pas) supprimé.

5. **Bug de robustesse du nettoyage numérique, trouvé ET corrigé pendant
   les tests de cette refonte** : la fonction `clean_numeric_value`
   extrayait un nombre par recherche regex dans n'importe quelle chaîne, y
   compris du texte parasite. Sur ton fichier actuel, une cellule de
   `Q G conc 240°/s (N/kg)` contient par erreur le nom de la colonne recopié
   — l'ancienne logique y aurait extrait "240" et faussé la moyenne du
   groupe de référence pour tout le monde comparé sur cette variable.
   Corrigé : une chaîne n'est acceptée comme nombre que si elle y ressemble
   globalement (nombre + unité courte), sinon elle est traitée comme
   manquante. **Vérifié par comparaison exhaustive colonne par colonne**
   entre l'ancien et le nouveau calcul sur ton fichier réel (0 écart
   restant après correction — voir `smoke_test.py`).
   *Note méthodologique* : sur ce fichier précis, les décimales utilisent
   déjà le point (pas la virgule) donc le risque "virgule française perdue"
   ne s'est pas manifesté aujourd'hui — mais la fonction reste robuste si
   une future saisie manuelle utilise la virgule.

6. **Duplication CSS/HTML entre les deux rapports** — carte métrique,
   légende, CSS d'impression étaient copiés-collés avec de petits écarts
   entre `build_prepa_report` et `build_kine_report`. Désormais dans
   `html_components.py`, une seule source, donc une seule correction à
   faire si le staff demande un changement visuel.

### Nouveauté : export PDF réel
En plus du HTML existant (conservé tel quel, aucun changement de mise en
page ni de risque de régression visuelle), un vrai bouton **Télécharger le
PDF** est disponible, basé sur WeasyPrint. Il réutilise exactement le même
HTML/CSS que la version imprimable — donc le rendu PDF est identique à ce
que donnait déjà "Imprimer" depuis le navigateur.

- Testé sur ce fichier réel : rapports Prépa (3 pages) et Kiné (5 pages)
  générés et inspectés visuellement, mise en page conforme.
- **Déploiement Streamlit Cloud** : WeasyPrint a besoin de bibliothèques
  système absentes par défaut → fichier `packages.txt` fourni à la racine,
  à ne pas oublier lors du déploiement. Sans lui, l'app détecte
  l'indisponibilité et propose automatiquement le HTML seul (pas de plantage).

### Nouveauté : génération en lot (`batch_engine.py`)
Un panneau "🗂️ Génération en lot" en bas de l'app permet de produire les
rapports de plusieurs joueurs en une fois :
- sélection d'une ou plusieurs équipes (PRO, Elite, U19...) + ajout
  ponctuel de joueurs individuels d'une autre équipe (ex : un espoir
  surclassé) ;
- les KPI cochées dans la sidebar sont utilisées pour tous les joueurs du
  lot, mais **une métrique qu'un joueur n'a pas testée est automatiquement
  retirée de SON rapport** (pas de carte à tiret) — ce comportement
  s'applique aussi bien en génération individuelle qu'en lot, y compris
  pour les blocs Ratio Mixte et Biodex ;
- le texte d'entretien / thèmes / évaluations de chaque joueur proviennent
  de ses réglages déjà sauvegardés (GitHub JSON) — rien n'est halluciné à
  la place du staff si rien n'a été saisi ;
- sortie en `.zip` (un PDF ou HTML par joueur), avec barre de progression
  et rapport d'erreurs par joueur si un cas particulier échoue (n'annule
  pas tout le lot).
- Testé sur données réelles (8 joueurs, un lot mixte équipe complète + 1
  joueur ajouté individuellement) — voir `smoke_test_batch.py`.

### Nouveauté : radar ISAK (composition corporelle)
Les 8 sites du protocole ISAK (`Isak_triceps`, `Isak_sousscapulaire`,
`Isak_biceps`, `Isak_crete`, `Isak_supraspinale`, `Isak_abdominal`,
`Isak_cuisse`, `Isak_jambe`) sont désormais traités comme n'importe quel
autre groupe de métriques kiné : ils apparaissent dans la sidebar
("Composition Corporelle (ISAK)"), donnent chacun une carte avec
percentile/z-score vs groupe de référence, ET un radar dédié (échelle fixe
0-15mm, cohérente avec la plage observée sur ton fichier) s'affiche dès que
3 sites ou plus sont sélectionnés et disponibles pour le joueur — avec la
somme des 8 plis si tous sont renseignés. Aucune norme club n'étant définie
pour ces valeurs, elles restent purement descriptives (pas de statut
Acquis/Non Acquis).

### Nouveauté : suivi & historique
- **Reprendre la session précédente** : bouton qui recopie texte
  d'entretien, thèmes et métriques sélectionnées de la session N-1 vers la
  session courante (à ajuster avant de sauvegarder).
- **Historique des sauvegardes** : les 20 dernières versions de chaque
  profil sont conservées (horodatées) avec un bouton "Restaurer".
- **Aperçu PDF inline** en plus de l'aperçu HTML, avant même de télécharger.

### Recommandations thématiques : passées en 100% manuel
L'auto-suggestion silencieuse a été retirée : une heuristique (seuil
d'asymétrie, percentile bas...) n'est pas assez fiable pour être présentée
comme une recommandation validée dans un rapport transmis au joueur. Les
pistes automatiques restent consultables à la demande via un expander
"💡 Voir des pistes indicatives", mais rien n'est pré-rempli.

### Nouveauté : radar Sprint 1080 (15m)
Les 4 nouvelles métriques (Temps 15m, Temps 5m, Vitesse Max 15m, Amax) issues
du test 1080 bénéficient désormais d'un mini-radar dédié (percentile 0-100,
même logique que le radar principal), affiché automatiquement dans le
rapport dès que 3 des 4 métriques sont disponibles pour le joueur — sans
action manuelle du staff. Visible aussi dans l'aperçu interactif.

### Correctif : sens des indicateurs ISAK
Les 8 sites du protocole ISAK n'étaient pas traités comme "plus bas = mieux"
(un pli cutané plus épais était compté comme une meilleure performance dans
les percentiles/z-scores). Corrigé dans `data_loader.py` (mot-clé "isak"
ajouté à la liste des métriques inversées). Vérifié sur données réelles :
un joueur avec un pli triceps légèrement au-dessus de la moyenne du groupe
obtient maintenant un percentile sous les 50% (au lieu d'au-dessus avant
correctif).

### Correctif : "NAN" affiché à la place d'un tiret
Bug trouvé en testant un joueur sans latéralité renseignée (`IBRAHIM Hafiz`) :
le rapport affichait littéralement "AT · NAN" au lieu de "AT · -". Cause :
`row.get(clé, défaut)` ne renvoie le défaut que si la CLÉ est absente, pas si
la cellule est vide (NaN). Nouvelle fonction `safe_get()` dans
`data_loader.py`, utilisée pour poste/latéralité/taille/poids dans `app.py`
et `batch_engine.py`.

### Nouveauté : Planning Type Hebdomadaire (Match Day)
Nouveau module `planning.py` + section dédiée dans l'app ("📅 Planning Type
Hebdomadaire"). Permet de saisir manuellement, pour le joueur sélectionné,
un planning organisé autour du jour de match (MD-2 → MD+3, Matin /
Après-midi), avec des catégories d'activité (Entraînement, Renforcement,
Soins, Protocole Récup, Prévention, Vidéo/Analyse, Nutrition, Repos) + un
champ de détail libre par créneau. Génère un visuel A4 paysage aux couleurs
du club (logo `logo_sdr.png` inclus dans ce zip), exportable en HTML et PDF,
sauvegardé séparément du profilage (`training_planning.json` sur GitHub, cf.
`persistence.py` — mêmes mécanismes de cache/retry que le profilage).
*Aucun calcul automatique : c'est un outil de saisie/visualisation, le
contenu est décidé entièrement par le staff.* Le thème visuel est une
première version — à affiner selon tes prochaines indications (fond, etc.).

**Bug corrigé pendant le développement de cette fonctionnalité** :
`display:inline-flex` n'est pas fiable avec WeasyPrint (le moteur de rendu
PDF) — les pastilles de catégorie s'étiraient sur toute la largeur au lieu
de rester compactes. Remplacé par `display:inline-block` partout dans
`planning.py` (vérifié : aucun autre fichier du projet n'utilisait
`inline-flex`, donc ce bug était strictement localisé à ce nouveau module).

### Ce qui n'a PAS changé (choix produit)
- Persistance des commentaires/thèmes : toujours GitHub JSON (pas de
  migration PostgreSQL pour l'instant, comme demandé).
- Rendu visuel des rapports : identique pixel pour pixel à l'ancienne
  version pour tout ce qui existait déjà (mêmes couleurs, cartes, radars,
  mise en page A4).
- Variables spécifiques par poste (gardien vs joueur de champ) : mis de
  côté pour l'instant (aucune variable n'est réellement propre à un seul
  poste dans ce fichier).

## Installer les dépendances système de WeasyPrint manuellement

**Sur Streamlit Community Cloud** : `packages.txt` doit être à la racine du
repo GitHub (même niveau que `app.py`). Après l'avoir poussé, redémarre
l'app manuellement (menu ⋮ → *Reboot app*) — un simple re-run ne suffit pas,
Streamlit Cloud ne relit les paquets système qu'au redémarrage complet.

**En local (Debian/Ubuntu)** :
```bash
sudo apt-get update && sudo apt-get install -y \
  libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
pip install -r requirements.txt
```

**En local (macOS, via Homebrew)** :
```bash
brew install pango cairo gdk-pixbuf libffi
pip install -r requirements.txt
```

**En local (Windows)** : WeasyPrint sur Windows nécessite l'installation de
GTK3 (le moyen le plus simple est le [MSYS2 GTK3 runtime](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)).
C'est plus contraignant que Linux/Mac — si ton usage est surtout en local
sous Windows, le plus simple reste de garder le HTML (déjà fonctionnel sans
rien installer) et de réserver le PDF au déploiement Streamlit Cloud.

Dans tous les cas, `is_pdf_export_available()` (dans `pdf_export.py`)
détecte automatiquement si WeasyPrint est utilisable et bascule l'app sur
HTML seul si ce n'est pas le cas — aucun risque de plantage.



## 2. Utiliser le projet

```bash
pip install -r requirements.txt
streamlit run app.py
```
Place ton fichier `.xlsx` de profilage dans le même dossier que `app.py`
(le nom exact n'a plus d'importance, cf. bug #1 corrigé).

Pour valider le pipeline de données sans lancer Streamlit :
```bash
python smoke_test.py
```

## 3. Repères méthodologiques (pour ton comité de pilotage / tes articles)

- **Percentile / z-score** : calculés sur la distribution réelle du groupe
  de référence sélectionné dans l'app (club / équipe / poste / position).
  Ce sont des indicateurs *relatifs* — leur fiabilité dépend de la taille
  de cet échantillon. En dessous de `N_REF_MIN = 8` (config.py), l'app
  avertit et propose un repli automatique vers un groupe plus large.
- **Normes (NORMES_ABSOLUES / NORMES_RELATIVES)** : ce sont des repères
  opérationnels fixés par le staff, pas des seuils calibrés
  statistiquement sur ta base. Le statut "Acquis / Proche / Non Acquis" est
  un repère pédagogique pour le terrain, à distinguer du z-score qui, lui,
  reflète la position réelle dans la distribution du groupe.
- Avec de petits effectifs (fréquent ici par poste), privilégie la taille
  d'effet (z-score) à un jugement binaire sur un seuil de percentile.

## 4. Pistes pour la suite (non traitées dans cette passe, sur demande)
- Migration de la persistance vers PostgreSQL (cohérent avec ta thèse et
  ton suivi longitudinal U15→Pro) plutôt que le JSON GitHub actuel.
- Extraction de `data_loader.py` / `stats_engine.py` vers un module partagé
  entre cette app Streamlit et tes pipelines Python de thèse (clustering
  K-means, ACP, profils Force-Vitesse), pour éviter de dupliquer la logique
  de nettoyage/normalisation entre les deux usages.

## 5. Correctifs suite à l'audit qualité (mise en page, calculs, PDF)

**Layout Sprint 1080 aligné sur le style Biodex** : radar à gauche (50%),
KPI empilés verticalement à droite (48%), pleine largeur de page — au lieu
d'un radar centré au-dessus des cartes.

**Chevauchement "POIDS" / "DÉPARTEMENT PERFORMANCE" dans l'en-tête** :
bug de largeur flexible mal calculée par WeasyPrint sur une structure flex
imbriquée. Corrigé en donnant une largeur fixe non compressible au bloc
logo (`flex-shrink:0`) plutôt qu'un simple `min-width`.

**Artefact visuel (point coloré isolé) sur les pages avec radar + légende** :
isolé et corrigé — c'étaient les emojis (icônes) utilisés dans le HTML des
rapports. WeasyPrint n'a pas de police emoji couleur installée par défaut,
ce qui produit des glyphes de repli mal positionnés. Retirés de tout le
HTML qui part en PDF (`html_components.py`) ; conservés dans les libellés
Streamlit de l'interface (`app.py`), qui s'affichent dans le navigateur et
ne sont pas concernés par cette limitation.

**Texte d'objectif dynamique trop long pour les cartes compactes** : "(moy.
groupe)" débordait et se chevauchait avec le reste de l'en-tête sur les
cartes à 3 colonnes du rapport kiné. Raccourci en "(grp)".

**Le PDF recalculé deux fois à chaque interaction** : le bouton de
téléchargement PDF et l'onglet d'aperçu PDF appelaient chacun
`html_to_pdf_bytes()` séparément, et ce à CHAQUE rerun Streamlit (pas
seulement au clic) puisque Streamlit réexécute tout le script à chaque
interaction. Sur un rapport volumineux, WeasyPrint peut prendre plusieurs
secondes — ce doublon pouvait donner une impression de lenteur ou
d'échec. Corrigé : le PDF n'est recalculé que si le contenu HTML du
rapport a changé (mis en cache en `st.session_state`), pour le rapport de
profilage ET pour le planning hebdomadaire.

**Vérification des calculs** : percentile, z-score (métrique normale et
inversée), LSI Biodex, somme des plis ISAK et moyennes dynamiques du
Sprint 1080 recalculés à la main (pandas indépendant du code de l'app) sur
plusieurs joueurs réels — tous les résultats correspondent exactement à ce
qu'affichent les rapports.

**Audit des sauts de page** : rapports Prépa seul, Kiné seul et Commun
inspectés page par page (cas normal et cas le plus chargé — un joueur
avec toutes les métriques disponibles, rapport de 6 pages) : aucune carte
coupée, aucun chevauchement de texte.
