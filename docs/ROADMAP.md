# Roadmap : explorateur de chansons des Beatles

Deux étapes :

- **v2 (en cours, 21/10/2026)** : passer du comptage de mots à une analyse thématique interprétable, et fiabiliser
  les crédits (auteurs, voix, instruments) avec des sources citées.
- **v1 (terminée)** : construction de l'explorateur Streamlit, en annexe en bas de ce fichier.

Légende : ✅ vérifié (dans le repo ou sur la source citée) · 🔶 connu, à revérifier · 💡 recommandation.

---

# v2 : analyse thématique et crédits

## A. État des lieux (audit du 21/10/2026)

### Ce qui existe ✅

| Fonction | Fichiers | Constat |
|---|---|---|
| Corpus et sections | `corpus.py`, `text/sections.py`, `text/segment.py` | balises Genius normalisées ; sans balises, sections déduites des strophes qui reviennent |
| Métriques lexicales | `text/metrics.py`, `text/repetition.py` | MATTR, hapax, répétition, empreinte 48×48 |
| Mots distinctifs | `text/keyness.py` | log-odds de Monroe et al. (prior de Dirichlet), déjà mieux que des fréquences brutes |
| Mots compagnons | `text/words.py:companions` | contraste chansons avec / sans le mot : le contexte est la chanson entière, pas le voisinage du mot |
| Humeur et thèmes | `text/mood.py` | VADER sur le sac de mots + 9 listes de mots faites à la main |
| Similarité | `text/similarity.py` (TF-IDF), `text/semantic.py` (MiniLM-L6, local via `scripts/embed_songs.py`) | seuls 5 voisins et scores sont exportés |
| Évolution | `text/trends.py`, `stories.py` | rho de Spearman année × taux, 4 périodes, récits recalculés depuis les données |
| Voix | `attribution.py` | balise de section > `lead_vocal` > Neutral ; le README précise que ce n'est pas le crédit d'écriture |
| Comparaison | `scripts/compare_artists.py`, `analysis/artists/` | 8 catalogues, même pipeline |

**Contrainte structurante** : le mode public (`data/public/beatles_bow.parquet`) ne contient que des sacs de mots.
Toute analyse contextuelle (phrases, négation, voisinage, embeddings) tourne en local et s'exporte sous forme de
**variables dérivées** sans texte, comme `semantic.parquet`.

### Qualité des données ✅

- 272 chansons, 213 compositions, environ 209 analysables (≥ 30 mots) : petit corpus.
- **159 des 213 compositions sont créditées « Lennon–McCartney »** sans distinction. `songwriters` est une chaîne brute
  jamais analysée (affichage dans `render/song_widgets.py`, `is_original`).
- Graphies hétérogènes : `Lennon–McCartney` / `Lennon; McCartney` (titres d'archives), `Starkey` / `Starr`,
  `Jerry Leiber\; \; Mike Stoller`, médleys `Lennon; McCartney /; Lennon; McCartney; Harrison; Starkey`.
- `lead_vocal` : 22 graphies (`McCartney; (with Lennon,; Harrison,; and Starr)`), `–` (3), `Sound Collage`,
  `Tony Sheridan`. Les chœurs entre parenthèses sont jetés.
- `year` : année de sortie pour les titres publiés à l'époque, mais année de session ou de démo pour les archives
  (*Free as a Bird* 1977, *Real Love* 1979, *Get Back*, *Bootleg 1963*). Le README parlait à tort d'« année de
  première sortie ». C'est l'année utile pour l'évolution de l'écriture, mais il faut la nommer et la signaler.
- `release` : 56 valeurs mêlant album et mentions de face A/B.
- Aucun niveau « enregistrement » : `lead_vocal` est porté par la chanson alors qu'il dépend de la version.
- `beatles.parquet` ne peut pas être reconstruit depuis le repo (`build_beatles.py` écrit un CSV).
- Le parquet public ne se lit pas avec un pyarrow ancien (lu correctement avec la version épinglée 24).

### Problèmes méthodologiques

1. Thèmes = listes de mots sans contexte ni validation (`away` → voyage, `man` → monde, `real` → esprit).
2. VADER sur sac de mots : pas de négation ni d'ironie (« don't cry » compte comme triste).
3. Chanteur pris implicitement pour auteur dans `analysis/beatles/distinctive_words_by_singer.csv` et
   `singer_summary.csv` (libellés honnêtes, lecture tentante). **Corrigé le 21/10/2026** : renommés `*_lead_voice*`,
   comparaison par crédit officiel ajoutée (Harrison contre Lennon–McCartney), `analysis/beatles/README.md`.
4. `trends.steady_movers` teste des centaines de mots à p < 0,05 sans correction ; les taux poolés pèsent plus
   lourd pour les chansons longues.
5. Aucun jeu annoté de référence pour valider un thème ou une émotion.

## B. Comparaison des approches

| Approche | Question | Pertinence (~210 chansons) | Interprétable | Dépendances | Coût | Verdict |
|---|---|---|---|---|---|---|
| Concordance et collocations en fenêtre (±5 mots, log-odds) | Dans quel sens « love », « girl », « mine » sont-ils employés ? | excellente, sans entraînement | très forte | aucune | faible | ✅ retenir |
| Codebook thématique multi-label annoté à la main, assisté par embeddings | De quoi parle chaque chanson, plusieurs thèmes à la fois ? | idéale : 210 chansons s'annotent en quelques jours | très forte | MiniLM (présent) | moyen puis faible | ✅ cœur de la v2 |
| Embeddings (strophes, chansons) | Quelles chansons sont proches malgré un vocabulaire différent ? | bonne (pré-entraîné) | moyenne : montrer les strophes qui rapprochent | sentence-transformers (local) | faible | ✅ étendre |
| NMF sur TF-IDF | Quels mots reviennent ensemble ? | correcte, plus stable que LDA sur textes courts | bonne | scikit-learn (présent) | faible | 🔶 exploratoire, pour proposer des thèmes |
| LDA | idem | faible : textes courts, répétitifs, instable | moyenne | sklearn / gensim | faible | ❌ écarter |
| BERTopic | idem, par embeddings | médiocre sur 210 documents, acceptable sur ~1 800 strophes ; instable (UMAP, HDBSCAN) | moyenne | torch, umap, hdbscan | moyen à élevé | ❌ phase 3 au plus, une fois |
| Émotion par ligne (VADER phrase, gère la négation) | Quelle émotion, où, avec quel contraste ? | bonne | bonne | vaderSentiment (présent) | faible | ✅ retenir |
| Classifieur d'émotions transformer (type GoEmotions) | joie, tristesse, colère… | moyenne : entraîné sur Reddit | faible | torch | moyen | 🔶 optionnel, validé contre l'annotation |
| Sens littéral / implicite (ironie) | *Run for Your Life*, *Happiness Is a Warm Gun* | aucun modèle fiable | n/a | n/a | annotation | ✅ champ manuel du codebook |
| Analyse narrative (je / tu / nous, personnages, impératifs, questions, temps) | Qui parle à qui ? | très bonne, règles simples | très forte | regex ou spaCy `en_core_web_sm` | faible à moyen | ✅ retenir |
| Évolution temporelle avec intervalles | Les thèmes changent-ils ? | bonne si par chanson | forte | scipy (présent) | faible | ✅ retenir, tests corrigés |

**Combinaison retenue** 💡 : concordance contextuelle + codebook annoté (embeddings et NMF comme assistants) +
émotion par ligne + indicateurs narratifs + tendances avec intervalles et correction des tests multiples. Avec
210 chansons, l'annotation humaine est faisable et sert de référence ; les modèles proposent et mesurent l'accord,
ils ne décident pas.

## C. Sources externes

### Vérifié le 21/10/2026 ✅

- **MusicBrainz** ([API](https://musicbrainz.org/doc/MusicBrainz_API) ;
  [limite](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting) : 1 requête/s, User-Agent descriptif). Données
  cœur, *Relationships* comprises, en CC0 ([Data License](https://musicbrainz.org/doc/About/Data_License),
  [Database](https://musicbrainz.org/doc/MusicBrainz_Database)) ; tags et annotations en CC BY-NC-SA.
  - La work *In My Life* a deux relations writer (Lennon, McCartney).
  - Sur *Abbey Road* (1969, ES), *Come Together* a 30 relations (instruments par membre, ingénieurs, producteur
    George Martin), *Something* 26 (dont orgue Hammond, Billy Preston).
  - Les enregistrements de remasters ou compilations n'ont **aucune** relation : cibler l'enregistrement d'origine.
  - Les relations ne citent pas leur source : fiabilité moyenne.
- **Wikidata** : P676 « lyrics by » et P86 « composer » sont distinctes (paroles / musique). Couverture Beatles non
  vérifiée.
- **Stylométrie** : Glickman et al., *Data in the Life: Authorship Attribution in Lennon-McCartney Songs*, Harvard
  Data Science Review, n° 1 (page en 403, résumé via la
  [Harvard Gazette](https://news.harvard.edu/gazette/story/2018/09/harvard-statistician-examines-beatles-mystery) et
  [Smithsonian](https://www.smithsonianmag.com/smart-news/statistics-offer-answer-decades-long-dispute-over-authorship-beatles-hit-180969804/)) :
  ~70 chansons, traits **musicaux** ; *In My Life* nettement Lennon, pont proche de 50/50. Inférence statistique, à
  stocker comme interprétation.

### À explorer 🔶

| Rang | Source | Apport | Accès |
|---|---|---|---|
| 1 primaire | pochettes et étiquettes ; entretiens : Lennon (*Playboy* 1980, D. Sheff, *All We Are Saying*), McCartney (B. Miles, *Many Years From Now*, 1997 ; *The Lyrics*, 2021) | crédit officiel, témoignages contradictoires | manuel, page citée |
| 2 référence | M. Lewisohn, *The Complete Beatles Recording Sessions* ; I. MacDonald, *Revolution in the Head* ; W. Everett, *The Beatles as Musicians* ; Guesdon & Margotin, *Tous les Beatles* | sessions, personnel, analyses d'attribution | manuel, page citée |
| 3 bases | MusicBrainz (CC0, API), Wikidata (CC0, SPARQL), Discogs (API, crédits par édition) | instruments et voix par enregistrement, identifiants stables | automatisable |
| 4 secondaire | sections « Personnel » de Wikipédia (CC BY-SA), The Beatles Bible, crédits Genius | pratique, exactitude variable | Wikipédia oui ; Beatles Bible sans API, droits à vérifier |

**Règles d'enrichissement** 💡

- Chaque donnée est une affirmation (claim) liée à une source, avec un niveau de confiance (`high`, `medium`, `low`).
- Jamais de fusion : deux sources en désaccord donnent deux lignes, signalées par une vue `conflicts`.
- Trois natures distinctes : `official` (crédit), `documented` (contribution attestée), `interpretation` (analyse).
- Sans preuve : `unknown`. Aucune attribution forcée.
- Collecte automatique : `retrieved_at` et identifiant MusicBrainz / Wikidata.

## D. Architecture cible

### Schéma (`data/credits/*.csv`, sans paroles, versionnés)

```
work(work_id, title, is_original, year_written?, mbid_work, wikidata_qid)
recording(recording_id, work_id, label, release, year_recorded, year_released, is_canonical, mbid_recording)
person(person_id, name, is_member)
source(source_id, type[primary|reference|database|secondary], citation, url, accessed)
work_credit(work_id, person_id, role[credited_writer|lyrics|music|middle_eight…], kind[official|documented|interpretation],
            share?, source_id, confidence[high|medium|low], note)
performance_credit(recording_id, person_id, role[lead_vocal|backing_vocal|instrument|producer|engineer|arranger],
                   detail, source_id, confidence, note)
```

Une propriété de la chanson (auteurs) reste distincte d'une propriété d'un enregistrement (voix, instruments).
Exemples (valeurs du repo, de MusicBrainz au 21/10/2026, ou attributions à sourcer précisément) :

```
work_credit: in_my_life, lennon,    credited_writer, official,       src=pochette_rubber_soul, high
work_credit: in_my_life, mccartney, credited_writer, official,       src=pochette_rubber_soul, high
work_credit: in_my_life, lennon,    lyrics,          documented,     src=sheff_1980 (page à vérifier), medium
work_credit: in_my_life, mccartney, music,           documented,     src=miles_1997 (page à vérifier), medium   ← conflit
work_credit: in_my_life, lennon,    music,           interpretation, src=glickman_hdsr, low, note="stylométrie, pont ~50/50"
performance_credit: come_together_1969, harrison, instrument, "electric guitar", src=musicbrainz, medium, accessed=2026-10-21
performance_credit: something_1969,     preston_b, instrument, "Hammond organ",   src=musicbrainz, medium, accessed=2026-10-21
```

**Migration** : `songwriters` et `lead_vocal` restent dans les parquets. Le module `beatles_viz/credits.py` en dérive
des colonnes (phase 1), puis lira les tables (phase 2) pour ajouter `primary_writer` (ou `undetermined`) et
`writer_confidence`. `attribution.py` ne change pas. Un test vérifie que chaque `work_id` correspond à un titre.

### Analyses rendues possibles (formats, pas résultats)

- Carte thèmes × album (part de chansons portant chaque thème, effectif affiché).
- Paires « proches en sens, éloignées en mots » : cosinus MiniLM élevé, TF-IDF faible, avec les strophes en cause.
- Tableau **auteur documenté × interprète** : les chansons écrites par l'un et chantées par l'autre testent le biais
  d'interprète (effectifs très faibles).
- Graphe membres → instruments par enregistrement, de *Please Please Me* à *Abbey Road*.

**Niveaux de preuve à afficher** : descriptif (comptages) ; exploratoire (NMF, voisins, tendances non corrigées) ;
à valider (toute affirmation « Lennon écrit plus sur X » : auteurs documentés, bootstrap, Benjamini-Hochberg, et
confusion période × auteur, Harrison et Starr écrivant surtout tard).

## E. Plan d'action

### Phase 1 : simple, à forte valeur ajoutée

**Statut** : faite le 21/10/2026 (non commitée à cette date). 208 tests passent en local ; 204 passent et 4 sont ignorés en mode public.

| Tâche | Fichiers | Résultat |
|---|---|---|
| Parser les crédits : `songwriters` → `writers`, `other_writers`, `writer_credit`, `medley` ; `lead_vocal` → `lead_singers`, `backing_singers`, `other_singers`, `vocal_known` | `beatles_viz/credits.py`, `corpus.py`, `tests/test_credits.py` | ✅ colonnes calculées en mode local et public ; colonnes d'origine intactes ; les voix principales coïncident avec `attribution.lead_members` sur toutes les chaînes réelles |
| Nature de `year` : `is_archival`, `year_basis` (`release` / `recording`) ; README corrigé | `credits.py`, `corpus.py`, `README.md` | ✅ 56 titres d'archives (Anthology, BBC, Get Back, Bootleg 1963, démos 2018…) |
| Album séparé de la mention de face : `release_note` | `credits.py`, `corpus.py` | ✅ |
| Couverture du parsing dans l'audit | `scripts/audit_dataset.py`, `analysis/audit/credits.csv`, `summary.csv` | ✅ 82 chaînes, 0 non résolue, 4 chansons à voix inconnue (`–`, `Sound Collage`) |
| Collocations en fenêtre ±5 mots, exportées en paires non ordonnées de mots pleins | `text/context.py`, `data/export.py`, `data/loader.py`, `app/word_page.py`, `viz/word_charts.py`, `tests/test_context.py` | ✅ section « What stands right next to it? » sur la page Word ; parquet public 239 → 381 Ko, colonnes existantes identiques |
| Humeur par ligne (`valence_ctx`, `mood_lines`), `valence` conservée | `text/mood.py`, `corpus.py`, `data/export.py`, `app/mood_page.py`, `viz/mood_charts.py` | ✅ nuage « Two readings of the mood » + chansons où l'écart est le plus grand ; corrélation 0,87 entre les deux lectures |
| Tendances : q-values (Benjamini-Hochberg), moyenne des taux par chanson (`change_song`), intervalle bootstrap 95 % | `text/trends.py`, `viz/trend_charts.py`, `app/trends_page.py` | ✅ sur 129 mots testés, 2 tiennent après correction (« love », « just ») ; ils sont toujours affichés (astérisque) |

**Constats et décisions**

- Aucun des mots « qui bougent » montrés jusqu'ici, hors « love » et « just », ne résiste à la correction : la page
  les présente désormais comme des pistes. « just » a un intervalle qui croise zéro entre la première et la dernière
  période alors que sa corrélation sur toutes les années est significative : les deux mesures ne disent pas la même
  chose, la légende l'explique.
- `valence` (mots isolés) reste la mesure utilisée par Stories, la carte de partage, Compare et Other artists.
  Basculer vers `valence_ctx` est une décision à prendre en phase 2, après comparaison sur l'annotation manuelle.
- Les paires de mots sont stockées sans ordre ni mots grammaticaux : elles ne permettent pas de reconstituer les
  paroles. Les mots vides de scikit-learn (dont « mine ») n'ont donc pas de voisinage.
- Le parquet public a été régénéré (`scripts/export_public.py`) ; à recommiter avec le code.

- **Dépendances** : aucune nouvelle.
- **Critères de réussite** : 100 % des chaînes `songwriters` et `lead_vocal` correspondent à un ensemble de membres
  ou à `unknown` ; tests existants verts ; CI publique inchangée (le parquet public garde ses colonnes et en gagne).
- **Risques** : moins de « mots qui bougent » après correction (attendu : ceux qui restent sont plus solides) ; le
  parquet public doit être régénéré en local (`scripts/export_public.py`).

### Phase 2 : enrichissement des données et analyses de fond

**Statut** : outillage fait le 21/10/2026 ; reste l'annotation des thèmes (travail humain) et la saisie des
contributions documentées depuis les livres.

| Tâche | Fichiers | Résultat |
|---|---|---|
| Collecte MusicBrainz (édition originale, puis recherche par titre ; cache local, 1 req/s, relances sur 503) | `scripts/fetch_credits.py`, `data/credits/mb_*.csv` | ✅ 266 des 272 chansons associées à un enregistrement, 263 avec des crédits d'interprètes (249 avant la correction du 21/10/2026 : les 45 tours sont désormais rattachés à leur sortie d'origine, plus à une réédition sans crédits) ; 6 sans enregistrement trouvé (jams de *Get Back*, *Suzy Parker*, *Save the Last Dance for Me*), listées dans `mb_missing.csv` |
| Tables de crédits sourcées (schéma D) et vue des désaccords | `scripts/build_credits.py`, `beatles_viz/credits.py`, `data/credits/*.csv`, `data/credits/README.md`, `analysis/credits/lead_vocal_conflicts.csv` | ✅ 1 107 crédits d'œuvre, 3 488 crédits d'enregistrement, 377 personnes. 27 désaccords sur la voix principale entre la liste officielle et MusicBrainz : surtout de granularité (MusicBrainz crédite la partie chantée par McCartney dans *A Day in the Life* ; la liste nomme deux voix principales sur *Love Me Do*). Conservés tous les deux, rien n'est tranché |
| Saisie manuelle des contributions (sources de rang 1 et 2) | `data/credits/manual_sources.csv`, `manual_claims.csv` | 🔶 gabarit et règles prêts ; une seule affirmation saisie (*In My Life*, stylométrie, `interpretation`, confiance faible). Le reste demande les livres : **à faire à la main** |
| Section « Who wrote it, who sings and plays? » sur la page Song | `render/views.py` | ✅ crédit officiel, affirmations non officielles avec leur source, interprètes et instruments |
| Codebook de 14 thèmes (définition, inclure, exclure) | `data/themes/codebook.csv` | ✅ CSV plutôt que YAML : aucune dépendance. « Nature et saisons » et « Nourriture et boisson » ajoutés le 21/10/2026 après l'annotation modèle |
| Page « Annotate » (locale) : paroles, codebook, thèmes multiples, thème principal, sens implicite, note ; suggestions du modèle masquées tant que la chanson n'est pas annotée | `app/annotate_page.py`, `beatles_viz/themes.py`, `data/themes/annotations.csv` | ✅ outil prêt ; **0 chanson annotée** |
| Suggestions du modèle : similarité MiniLM strophes × descriptions des thèmes ; NMF 12 sujets | `scripts/suggest_themes.py`, `data/themes/suggestions.csv`, `nmf_topics.csv`, `nmf_songs.csv` | ✅ ; à l'œil, souvent à côté (*Within You Without You* n'est pas classée « spiritualité », *Lucy in the Sky* pas « rêve ») : confirme que le modèle ne peut qu'aider |
| Accord inter-annotateurs et annotateur × modèle (kappa de Cohen par thème) | `scripts/theme_agreement.py`, `analysis/themes/agreement.csv` | ✅ script prêt, à lancer après annotation |
| Thèmes annotés par période sur la page Mood | `app/mood_page.py`, `viz/mood_charts.py` | ✅ s'affiche dès qu'une annotation existe |
| Indicateurs narratifs : 3e personne, passé, futur, personnages nommés (sac de mots) ; questions, ordres (lignes, exportés) | `text/narrative.py`, `corpus.py`, `data/export.py` | ✅ graphique « How it tells » (page Song), section « Do the songs tell differently? » (Trends) |

**Décisions**

- Indicateurs narratifs par listes de mots et règles de ligne plutôt que spaCy : transparents, sans dépendance,
  suffisants pour comparer des chansons. Limites affichées : pas de grammaire, questions dépendantes de la
  ponctuation de la transcription.
- Les thèmes du modèle ne sont jamais affichés comme résultat dans l'app : seulement dans la page Annotate, après la
  décision de l'annotateur.
- `valence` reste la mesure d'humeur principale tant que l'annotation n'a pas permis de comparer les deux lectures.

**Prochaines étapes (humaines)**

1. Annoter les ~209 compositions (page Annotate), idéalement à deux sur un échantillon de 40 chansons pour mesurer
   l'accord (objectif : kappa ≥ 0,6 par thème ; sinon préciser le codebook).
2. Lancer `python scripts/theme_agreement.py`, puis remplacer les thèmes par listes de mots.
3. Saisir dans `manual_claims.csv` les attributions documentées (Lewisohn, MacDonald, Everett ; entretiens Sheff et
   Miles), page citée, une ligne par source, conflits conservés.

### Phase 3 : exploratoire

**Statut** : faite le 21/10/2026, sauf ce qui dépend de l'annotation des thèmes.

| Tâche | Fichiers | Résultat |
|---|---|---|
| Niveau de preuve affiché sous chaque analyse (descriptif, exploratoire, à valider) | `render/components.py:evidence`, pages Trends, Mood, Credits, Other artists | ✅ |
| Page Credits : instruments par membre et par période (familles), musiciens extérieurs, crédit officiel × voix principale × période, désaccords entre sources, contributions documentées | `app/credits_page.py`, `viz/credit_charts.py`, `credits.py` | ✅ 240 chansons avec instrumentistes (218 avant la correction des 45 tours) ; ex. l'harmonica de Lennon en 1962-63 puis les claviers en 1966-67 ; George Martin (36 chansons) et Billy Preston (10) en tête des extérieurs |
| Sujets de strophes : le cœur de BERTopic (embeddings MiniLM, k-means, mots par c-TF-IDF) sans umap ni hdbscan ; k par silhouette ; stabilité par ARI entre 10 graines | `scripts/stanza_topics.py`, `data/themes/stanza_topics*.csv`, `analysis/themes/stanza_topics_quality.csv`, page Mood | ✅ 1 144 strophes distinctes, k = 18. **Silhouette 0,04, stabilité 0,29** : les strophes ne forment pas de groupes nets, et une autre graine donne des groupes assez différents. Quelques groupes lisibles (versions allemandes, amour / besoin, soleil, argent), d'autres réduits aux mots d'une ou deux chansons. Affiché comme exploratoire, pas comme des thèmes |
| Indicateurs narratifs et humeur par ligne sur les 8 catalogues, avec intervalles bootstrap | `scripts/compare_narrative.py`, `analysis/artists/narrative.csv`, page Other artists | ✅ ex. Cohen narre le plus au passé, les Beatles et McCartney sont les plus tournés vers le futur et les plus positifs ; personnages exclus (la liste de noms est celle des Beatles) |
| Classifieur d'émotions transformer | | ⏸ reporté : il ne peut être évalué que contre l'annotation manuelle, qui n'existe pas encore ; l'ajouter sans évaluation contredirait la règle de la v2 |
| Thèmes du codebook appliqués aux 8 catalogues | | ⏸ reporté : dépend aussi de l'annotation (un modèle validé sur les Beatles pourrait alors être appliqué aux autres, avec contrôle sur un échantillon) |

**Annotation modèle (21/10/2026)** : les 209 compositions annotées par Claude (Opus 5.5) avec le codebook, annotateur
`claude-opus-5.5 (model)` dans `data/themes/annotations.csv`, à partir des paroles seules ; 1,95 thème par chanson,
30 chansons marquées « sens implicite ». Ce n'est **pas** la référence humaine : c'est un second codeur. Accord avec les
suggestions MiniLM (top 2) : kappa moyen **0,28** (accord faible), de 0,10 (société) à 0,51 (musique et danse). MiniLM
surestime « identité », « nostalgie », « solitude » et « chagrin », sous-estime « société », « spiritualité », « rêve »
et « désir » : il lit le vocabulaire affectif, pas le propos. Lacunes du codebook relevées : la nature et les saisons,
la nourriture, ajoutées depuis (8 chansons recodées ; kappa moyen inchangé à 0,28). Prochaine mesure, la seule qui valide : humain × Claude, dès qu'une annotation humaine existe.

**Leçon** : le résultat le plus net de la phase 3 est négatif et utile. Les méthodes non supervisées (NMF en phase 2,
groupes de strophes ici) ne trouvent pas de structure thématique stable dans un corpus de cette taille : elles
confirment le choix d'un codebook annoté à la main comme référence.

**Wikipédia comme seconde source de crédits (21/10/2026)**

| Tâche | Fichiers | Résultat |
|---|---|---|
| Sections « Personnel » des pages d'albums : rôles limités à des chansons nommées seulement (le reste vaut pour tout l'album et n'est pas comparable chanson par chanson) | `beatles_viz/wiki.py`, `scripts/fetch_wikipedia_credits.py`, `data/credits/wp_*.csv` | ✅ 19 albums sur 27 ont une section ; accord avec MusicBrainz de 81 à 100 % selon la partie |
| Sections « Personnel » des pages de chansons, avec la révision lue et les ouvrages cités (Lewisohn, MacDonald, Everett…) | idem | ✅ 233 articles avec section ; 3 462 lignes ; source `wikipedia_song_page`, confiance moyenne |
| Qui a écrit quoi : phrases des articles lues par le modèle, une ligne par affirmation, citation et révision gardées | `scripts/wikipedia_authorship.py`, `data/credits/wikipedia_claims.csv` | ✅ 403 affirmations sur 177 chansons (234 moyennes, 169 faibles : sans citation ou contredites) ; 16 chansons où les récits divergent. **À vérifier dans les livres cités** |
| Recoupement Wikipédia × MusicBrainz, personne par personne et partie par partie | `credits.py:compare_sources`, `analysis/credits/source_agreement.csv`, `source_disagreements.csv`, page Credits | ✅ 222 chansons comparées, **79 % d'accord** ; guitare 90 %, basse 91 %, voix principale 87 %, chœurs 63 %, cordes 62 % |

Les désaccords sont surtout de définition : deux chanteurs qui se partagent la voix sont deux voix principales pour
MusicBrainz, une voix et une harmonie pour beaucoup d'articles ; MusicBrainz nomme chaque musicien d'orchestre,
Wikipédia écrit souvent « non crédité ». Quelques-uns sont de fond (McCartney absent de *She Said She Said* selon
MacDonald et Everett, crédité à la basse par MusicBrainz). Rien n'est fusionné : chaque source garde sa ligne.

**Reste à faire (dans l'ordre)** : annoter (page Annotate) → `scripts/theme_agreement.py` → remplacer les thèmes par
listes de mots sur la page Mood → évaluer un classifieur d'émotions et les suggestions du modèle contre l'annotation →
étendre aux autres catalogues. En parallèle : saisir les contributions documentées (`data/credits/manual_claims.csv`).

---

# Annexe : roadmap v1 (terminée)


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

**Statut (20/10/2026)** : fait. `pyproject.toml` installe le paquet (`pip install -e ".[dev]"`), les versions sont celles de Streamlit Cloud, `scripts/beatles_lib.py` a disparu au profit de `beatles_viz` seul. Le point d'entrée reste `app/beatles_app.py`.

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
