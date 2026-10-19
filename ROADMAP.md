# Roadmap : explorateur de chansons des Beatles (Streamlit)

## Hypothèses

Constats d'un audit rapide de `data/beatles/beatles.parquet`, à confirmer en phase 0 :

- **Source** : `data/beatles/beatles.parquet`, 272 chansons dont 213 compositions du groupe. Colonnes : `artist`, `title`, `year`, `release_core`, `songwriters`, `lead_vocal`, `is_original`, `genius_title`, `n_tokens`, `n_types`, `lyrics_raw`, `lyrics_clean`.
- **Sections** : elles sont balisées Genius dans `lyrics_raw` (`[Verse 1]`, `[Chorus]`, `[Bridge]`, etc.). 252 chansons sur 272 ont des balises. Les libellés ne sont pas homogènes (`Guitar solo` et `Guitar Solo`, `x`, `?`).
- **Chanteur par section** : 375 balises sur 1 817 nomment le chanteur (`[Verse 2: Paul McCartney]`). Elles servent à attribuer une section quand elles existent.
- **Attribution « auteur »** : 159 compositions sont créditées « Lennon–McCartney » sans distinction. **L'effet visuel suit donc la voix principale, pas le crédit d'écriture** :
  1. le chanteur nommé dans la balise de section, s'il existe ;
  2. sinon `lead_vocal` de la chanson ;
  3. sinon un effet neutre.
  Une chanson ou une section à plusieurs voix reçoit l'effet « voix partagées ».
- **Auteurs disponibles** : Lennon, McCartney, Harrison, Starr (8 chansons en voix principale, peu de données), et « Partagé ». Les reprises sont exclues par défaut et activables.
- **Paroles et droits** : les paroles sont protégées et restent locales. Le mode « chanson entière » ne s'active que si le fichier local avec paroles est présent. L'app déployée (qui lit `data/public/beatles_bow.parquet`) le masque. Les tests n'utilisent que des paroles synthétiques.
- **Code existant** : `scripts/beatles_lib.py` (tokenisation, MATTR, filtres) et `app/beatles_app.py`. Ils sont migrés dans le nouveau paquet, pas réécrits.

## Architecture cible

```
beatles_viz/
  config.py            chemins, constantes (phases, fenêtres, seuils)
  data/loader.py       lecture parquet, choix source locale/publique
  text/tokenize.py     tokenisation, mots vides, syllabes, noms propres
  text/sections.py     découpage en sections, normalisation des libellés, chanteur par section
  text/metrics.py      métriques lexicales par chanson et par section
  attribution.py       règle voix -> auteur (section, chanson)
  effects/base.py      interface Effect + registre
  effects/lennon.py, mccartney.py, harrison.py, starr.py, shared.py, neutral.py
  viz/song_charts.py   figures Plotly par chanson (aucun appel Streamlit)
  render/song_view.py  rendu HTML d'une chanson (sections + effet)
  render/components.py composants Streamlit réutilisables (sélecteur, panneau métriques)
app/
  Home.py              vue corpus (app actuelle)
  pages/1_Chanson.py   visualisations par chanson
  pages/2_Lecture.py   mode chanson entière
tests/
```

Une seule règle de dépendance : `data` → `text` → `attribution` / `metrics` → `viz` / `effects` → `render` → `app`. Aucun module en amont n'importe Streamlit.

---

## Phase 0 : audit du dataset

**Objectifs**
- Documenter le format, les colonnes, l'encodage (22 chansons contiennent des caractères non ASCII : guillemets typographiques, accents, allemand) et les valeurs manquantes (`lead_vocal` = `–` pour 2 chansons).
- Inventorier les libellés de section et les chanteurs nommés, puis construire les tables de normalisation.
- Lister les chansons sans balises (20), les co-écritures, et les voix partagées dans `lead_vocal` et dans les balises.

**Fichiers** : `scripts/audit_dataset.py` (sortie : `analysis/audit/*.csv`), `beatles_viz/config.py` (tables de normalisation).

**Dépendances** : pandas, pyarrow.

**Critères de validation**
- Chaque libellé de section brut correspond à une catégorie normalisée : `intro`, `verse`, `pre_chorus`, `chorus`, `bridge`, `instrumental`, `outro`, `other`.
- Chaque chaîne de chanteur correspond à un ensemble de membres.
- Un rapport donne la couverture par auteur (nombre de chansons et de sections).

**Risques** : balises absentes ou fantaisistes (`x`, `?`) ; noms écrits de plusieurs façons (« Paul McCartney (& John Lennon and George Harrison) »). Les cas non résolus vont dans `other` ou « Partagé », sans deviner.

## Phase 1 : modèle de données et extraction

**Objectifs** : une chanson devient une structure `Song` → `Section` → lignes → tokens. Les métriques sont calculées par chanson et par section.

**Interfaces**
```python
load_songs(source="auto", originals_only=True)   # -> DataFrame, colonne lyrics si locale
has_lyrics()                                      # True si le fichier local existe
split_sections(lyrics_raw)                        # -> [Section(kind, label, number, singers, lines)]
normalize_label(raw_label)                        # "Guitar solo" -> "instrumental"
parse_singers(raw)                                # "Paul McCartney & John Lennon" -> {"McCartney", "Lennon"}
tokenize(text)
song_metrics(song)        # tokens, types, mattr, repeat_ratio, hapax, pronoms
section_metrics(section)  # tokens, types, répétition interne
resolve_voice(section, song)                      # -> "Lennon" | ... | "Shared" | "Neutral"
```

**Fichiers** : `data/loader.py`, `text/tokenize.py`, `text/sections.py`, `text/metrics.py`, `attribution.py`.

**Dépendances** : phase 0 (tables de normalisation). Reprise de `tokenize`, `mattr` et des filtres de `scripts/beatles_lib.py`.

**Critères de validation**
- Concaténer les sections redonne `lyrics_clean`, aux espaces près.
- Les métriques par chanson sont égales à celles de `analysis/beatles/song_metrics.csv` sur les 211 chansons.
- `resolve_voice` applique l'ordre balise, puis `lead_vocal`, puis neutre.

**Risques** : refrains notés une seule fois avec `x2` ou `(x3)` (à détecter et étendre ou signaler, sans réécrire les paroles) ; MATTR non défini sous 50 mots par section (afficher « n/a »).

## Phase 2 : visualisations par chanson

Chaque graphique répond à une question différente.

| # | Visualisation | Question | Donnée |
|---|---|---|---|
| 1 | Frise de structure : sections en blocs proportionnels au nombre de mots, colorées par type | Comment la chanson est-elle construite ? | sections |
| 2 | Matrice d'auto-similarité des lignes | Où sont les répétitions et les retours de motifs ? | lignes |
| 3 | Richesse lexicale glissante (MATTR sur fenêtre mobile) le long de la chanson | Où le texte est-il dense ou répétitif ? | tokens ordonnés |
| 4 | Mots spécifiques de la chanson face au corpus (log-odds, top 10) | Quel vocabulaire la distingue ? | comptes chanson / corpus |
| 5 | Position dans le corpus : nuage longueur × richesse, chanson mise en évidence, filtrable par période | Est-elle typique de son époque ? | métriques corpus |
| 6 | Répartition des voix par section (barre empilée), seulement si des balises nomment les chanteurs | Qui chante quoi ? | `resolve_voice` |
| 7 | Profil des pronoms (je / tu / nous) comparé à la moyenne de la période | De quel point de vue la chanson parle-t-elle ? | tokens |

Pas de nuage de mots : il ferait doublon avec le graphique 4 et resterait moins précis.

**Interfaces** : une fonction par figure dans `viz/song_charts.py`, qui renvoie un objet Plotly, par exemple `structure_timeline(song)`, `self_similarity(song)`, `rolling_richness(song, window=30)`, `keyness(song, corpus)`, `corpus_position(song, corpus, period=None)`, `voice_split(song)`, `pronoun_profile(song, corpus)`.

**Fichiers** : `viz/song_charts.py`, `render/components.py`, `app/pages/1_Chanson.py`.

**Dépendances** : phase 1. Plotly.

**Critères de validation**
- Chaque fonction s'exécute sur toutes les chansons du corpus sans exception.
- Les graphiques 1 à 3 restent informatifs sur une chanson sans balises (une seule section « chanson »).
- Le graphique 6 est masqué, avec un message, quand aucune balise ne nomme de chanteur.

**Risques** : la matrice 2 devient illisible au-delà d'environ 80 lignes (agréger par section) ; les comptes du graphique 4 sont faibles sur les chansons courtes (seuil minimal d'occurrences).

## Phase 3 : système d'effets par auteur

**Objectifs** : chaque voix a un effet visuel reconnaissable, appliqué au rendu de la phase 4. Les effets sont des modules interchangeables et désactivables.

**Interface**
```python
class Effect:
    name = ""
    defaults = {}                      # paramètres configurables
    def css(self, params): ...         # styles et @keyframes, préfixés par la classe de l'effet
    def wrap_section(self, html, section, params, ctx): ...
    def wrap_line(self, line, params, ctx): ...   # ctx : membres, fréquences du corpus, rang de la ligne

register(effect)                       # décorateur ou appel explicite
get_effect(voice)                      # voix inconnue -> Neutral
```

Contraintes communes :
- CSS pur, injecté une seule fois, sans JavaScript (rendu via `st.html`).
- Toutes les animations sont coupées sous `prefers-reduced-motion` et avec un interrupteur « effets » global.
- Contraste conforme WCAG AA en thème clair et sombre.
- L'effet modifie la présentation, jamais le texte.

**Récapitulatif des effets**

| Auteur (voix) | Effet visuel | Justification | Paramètres configurables |
|---|---|---|---|
| John Lennon | Police à chasse fixe type machine à écrire, palette froide à fort contraste, léger flou ondulant sur les mots rares de la chanson | Jeux de mots, introspection et textes psychédéliques (« I Am the Walrus », « Strawberry Fields Forever ») : on met en avant le mot et l'étrangeté | palette, intensité de l'ondulation (0-1), seuil de rareté des mots soulignés |
| Paul McCartney | Serif lisible, palette chaude, apparition fluide ligne par ligne, refrains légèrement agrandis | Écriture mélodique et narrative, souvent centrée sur des personnages : on suit le fil et le refrain | palette, vitesse d'apparition, facteur d'agrandissement du refrain |
| George Harrison | Grand interlignage, palette safran et indigo, pulsation lente de l'opacité des sections | Spiritualité et influence de la musique indienne (« Within You Without You ») : la pulsation évoque un bourdon, l'espace évoque la méditation | palette, période de pulsation (s), interlignage |
| Ringo Starr | Police arrondie, couleurs primaires, léger rebond rythmique en début de ligne | Chansons chantées ou écrites sur un ton ludique (« Yellow Submarine », « Octopus's Garden », « Don't Pass Me By ») | palette, amplitude du rebond, tempo |
| Voix partagées | Bordure bicolore aux couleurs des voix présentes, sans animation | Plusieurs chanteurs : on montre la combinaison sans privilégier une voix | couleurs héritées des effets concernés, épaisseur de bordure |
| Neutre | Typographie de base de l'app, aucune animation | Voix inconnue ou chanson instrumentale | aucun |

**Fichiers** : `effects/base.py`, un fichier par effet, `effects/__init__.py` (registre).

**Dépendances** : `attribution.py` (phase 1). Aucune dépendance à Streamlit.

**Critères de validation**
- Un test de contrat vérifie que tout effet enregistré produit un CSS non vide préfixé par sa classe, ne modifie pas le texte, et accepte ses `defaults`.
- Ajouter un effet ne demande qu'un nouveau fichier et son enregistrement.
- Désactiver les effets donne le même rendu que l'effet neutre.

**Risques** : peu de chansons pour Starr (8) ; perception subjective des effets (les paramètres sont réglables dans l'app) ; conflits de CSS avec le thème Streamlit (préfixer toutes les classes).

## Phase 4 : mode chanson entière

**Objectifs** : affichage complet et lisible d'une chanson, organisé par sections, avec l'effet de la voix de chaque section.

**Fonctionnalités**
- Sélection d'une chanson par recherche de titre, filtres (album, année, voix, compositions ou reprises) et lien direct par paramètre d'URL (`?song=...`).
- Navigation précédente / suivante dans l'ordre chronologique, ou dans l'ordre d'un album.
- Sections affichées avec un titre normalisé (« Couplet 2 », « Refrain », « Pont »). Les répétitions notées `x2` sont signalées, sans recopie.
- Panneau latéral : année, album, auteurs crédités, voix, métriques de la phase 1, lien vers les visualisations de la phase 2.
- Réglages : effets activés ou non, paramètres de l'effet courant, taille de police.

**Interfaces**
```python
render_song(song, effects_on=True, params=None)   # -> HTML
song_selector(corpus, key)                        # composant Streamlit -> titre choisi
neighbors(corpus, title, order="chronological")   # -> (précédent, suivant)
```

**Fichiers** : `render/song_view.py`, `render/components.py`, `app/pages/2_Lecture.py`.

**Dépendances** : phases 1 et 3. Fichier local avec paroles (`has_lyrics()`).

**Critères de validation**
- Les 272 chansons s'affichent sans erreur, y compris les 20 sans balises (une seule section).
- La navigation conserve les filtres actifs.
- Sans le fichier local, la page affiche un message et aucun texte de paroles.

**Risques** : paroles Genius non relues (signaler la source en pied de page) ; rendu HTML lent sur les longues chansons (mise en cache par titre) ; diffusion involontaire des paroles (la page reste désactivée hors local, et `data/beatles/` reste ignoré par git).

## Phase 5 : tests, packaging et lancement local

**Objectifs** : tests automatisés, installation reproductible, lancement en une commande.

**Tests (`tests/`)**
- `test_sections.py` : découpage, normalisation des libellés, chanteurs, sur des paroles synthétiques.
- `test_metrics.py` : valeurs connues sur de petits textes (MATTR, répétitions).
- `test_attribution.py` : ordre de priorité balise, puis chanson, puis neutre.
- `test_effects.py` : contrat commun à tous les effets enregistrés.
- `test_charts.py` : chaque figure se construit sans erreur sur un mini-corpus synthétique.
- `test_app.py` : `streamlit.testing.v1.AppTest` sur chaque page, avec et sans fichier de paroles.

**Packaging** : `pyproject.toml` (paquet `beatles_viz`, dépendances, `pytest` en dépendance de développement) ; mise à jour de `requirements.txt` pour Streamlit Cloud ; `README.md` (installation, lancement, ce qui est local et ce qui est publié) ; `.claude/launch.json` pointant sur `app/Home.py`.

**Lancement local**
```bash
pip install -e .
streamlit run app/Home.py
```

**Critères de validation**
- `pytest` passe dans un environnement vierge.
- L'app démarre en local avec paroles (toutes les pages) et sans paroles (page Lecture masquée).
- Le déploiement Streamlit Cloud n'inclut aucune parole.

**Risques** : différences de versions entre local et Streamlit Cloud (fixer des bornes minimales testées) ; tests qui dépendent du fichier local (les isoler derrière un marqueur `pytest`).

## Ordre et jalons

| Jalon | Contenu | Livrable |
|---|---|---|
| J0 | Phase 0 | rapport d'audit, tables de normalisation |
| J1 | Phase 1 | paquet `beatles_viz` (données, texte, attribution), tests unitaires |
| J2 | Phases 2 et 3 en parallèle | page Chanson ; registre d'effets |
| J3 | Phase 4 | page Lecture |
| J4 | Phase 5 | tests d'app, packaging, README |
