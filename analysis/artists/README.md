# Beatles, Rolling Stones, Bob Dylan : comparaison des paroles

Analyse hors ligne (l'application Streamlit n'est pas modifiée). Les trois catalogues passent par le même
pipeline que l'app (`beatles_viz.corpus.build_corpus` : sections, MATTR, répétition, humeur VADER), compositions
originales seulement, chansons d'au moins 30 mots. Les fichiers ici ne contiennent que des chiffres, des titres
et des mots isolés : aucune parole n'est citée.

## Données

| | Beatles | Rolling Stones | Bob Dylan |
|---|---|---|---|
| Liste officielle (Wikipédia) | *List of songs recorded by the Beatles* | *List of songs recorded by the Rolling Stones* (445 titres) | *List of songs written by Bob Dylan* (560 titres) |
| Lignes Genius de l'artiste | 751 | 829 | 850 |
| Chansons retenues | 272 | 387 (dont 9 via une version Live/Demo) | 403 (dont 19 via une version Live/Demo) |
| Compositions analysées | 209 | 293 | 403 |

- L'année est celle de la première sortie donnée par la liste Wikipédia, comme pour les Beatles. L'année du
  dataset Genius n'est pas fiable (pour les Beatles elle ne tombe juste que dans 78 % des cas : compilations,
  rééditions).
- Une ligne par titre officiel : le titre studio quand Genius l'a, sinon une version Live/Demo/Take, en gardant
  les paroles les plus longues (≥ 20 mots).
- « Original » : les Stones écrits par un membre (Jagger, Richards, Nanker Phelge…) ; la liste de Dylan ne
  contient que ses chansons ; les Beatles reprennent la colonne `is_original` du fichier de l'app.
- Les noms propres (mots écrits avec une majuscule en milieu de ligne dans ≥ 90 % des cas) sont exclus des mots
  distinctifs, comme la liste `NAMES` des Beatles.

Reproduire (les paroles restent dans `data/`, ignoré par git) :

```bash
curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_recorded_by_the_Rolling_Stones&action=render" -o stones.html
curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_written_by_Bob_Dylan&action=render" -o dylan.html
python scripts/build_artist.py "The Rolling Stones" stones.html raw/genius
python scripts/build_artist.py "Bob Dylan" dylan.html raw/genius
python scripts/compare_artists.py data/beatles/beatles.parquet data/rolling_stones/rolling_stones.parquet data/bob_dylan/bob_dylan.parquet
```

## Résultats (médianes par chanson)

| | Beatles | Rolling Stones | Bob Dylan |
|---|---|---|---|
| Mots par chanson | 183 | 236 | 258 |
| Richesse du vocabulaire (MATTR-50) | 0,64 | 0,64 | **0,77** |
| Répétition (paires de mots identiques) | **0,030** | 0,026 | 0,015 |
| Lignes répétées (part des mots) | **33 %** | 20 % | 9 % |
| Chansons avec un refrain | 64 % | 70 % | **32 %** |
| Humeur (valence VADER, −1 à 1) | **+0,22** | +0,02 | +0,04 |
| « I / me / my » (part des mots) | 9,4 % | 7,0 % | 6,9 % |

Tests de Mann-Whitney dans `pairwise_tests.csv` ; toutes les différences du tableau sont nettes (p < 0,01)
sauf : MATTR Beatles vs Stones (p = 0,42), part du refrain Beatles vs Stones (p = 0,29) et humeur Stones vs Dylan
(p = 0,73).

1. **Dylan a le vocabulaire le plus riche, et de loin.** Sur une fenêtre glissante de 50 mots, 77 % des mots
   sont différents chez lui, contre 64 % chez les Beatles et les Stones, qui sont à égalité. Le MATTR ne dépend
   pas de la longueur : ce n'est pas un effet des chansons plus longues. Ses chansons sont aussi les plus
   longues et les moins répétitives : seulement un tiers ont un refrain, le reste est strophique (couplets qui
   se suivent, avec au plus un vers-refrain en fin de couplet, que Genius ne marque pas comme refrain).
2. **Les Beatles sont les plus concis et les plus répétitifs** : chansons courtes, un tiers des mots dans des
   lignes répétées, refrains fréquents. Les Stones sont entre les deux : aussi riches que les Beatles par fenêtre
   de 50 mots, mais plus longs et un peu moins répétitifs.
3. **L'humeur sépare les Beatles des deux autres.** Valence médiane +0,22 contre ~0 pour les Stones et Dylan ;
   les Beatles emploient plus de mots positifs (4,1 % contre 3,2-3,4 %) et presque deux fois moins de mots
   négatifs (1,7 % contre 2,9-3,1 %). VADER compte des mots sans contexte (« don't cry » compte comme triste) :
   c'est une tendance de vocabulaire, pas une lecture fine.
4. **Mots distinctifs** (`distinctive_words.csv`, chacun contre les deux autres, mot présent dans ≥ 5 chansons) :
   - Beatles : *love, know, girl, lonely, good, better, yes, feeling, need, home* : la chanson d'amour et le
     dialogue « je / tu » (ce sont aussi eux qui disent le plus *I* et *you*).
   - Rolling Stones : *yeah, baby, oh, hey, hot, got, dancing, cold, drink, rock, tough, strange* : interjections,
     corps, danse et alcool, le registre du rhythm and blues.
   - Bob Dylan : *turn, wind, road, men, walking, town, land, river, water, cross, death* : paysages, voyage,
     images bibliques, et la langue parlée (*ya, ain't, says, went*), narration au passé.
   - Les scores de Dylan (z ≤ 7) sont bien plus bas que ceux des Beatles et des Stones (jusqu'à 22-27) : aucun mot
     ne domine son catalogue, autre signe d'un vocabulaire étalé.
5. **Proximité des catalogues** (`similarity_between_artists.csv`, cosinus TF-IDF moyen entre chansons) : chaque
   artiste ressemble d'abord à lui-même ; les Stones sont à mi-chemin, Beatles et Dylan sont les plus éloignés.
   Les écarts sont faibles (0,030 à 0,037) : les trois parlent la même langue pop des années 60.

## Évolution : les neuf premières années de carrière

Fenêtre choisie : **les neuf premières années de chaque carrière, à partir du premier disque** (Beatles
1962-1970, Stones 1963-1971, Dylan 1962-1970), découpées en trois étapes de trois ans. Pourquoi : neuf ans, c'est
toute la carrière des Beatles, donc la seule fenêtre où l'on compare les trois au même « âge » ; elle tombe en
plus sur la même décennie pour les trois (même contexte musical, mêmes influences croisées). Comparer la carrière
entière mélangerait les Beatles des années 60 avec le Dylan ou les Stones des années 2000 (voir `decades.csv`
pour ce contexte).

| Étape | Beatles (MATTR / mots / valence) | Stones | Dylan |
|---|---|---|---|
| Années 1-3 | 0,64 / 177 / +0,24 (54 chansons) | 0,62 / 153 / +0,07 (21) | 0,77 / 286 / +0,00 (34) |
| Années 4-6 | 0,67 / 200 / +0,20 (71) | 0,68 / 191 / +0,09 (58) | 0,80 / 258 / +0,03 (45) |
| Années 7-9 | 0,61 / 166 / +0,20 (81) | 0,66 / 206 / +0,02 (18) | 0,74 / 160 / +0,23 (23) |

- **Beatles et Stones suivent la même courbe** : le vocabulaire s'enrichit jusqu'au milieu de la décennie
  (1965-67 : *Rubber Soul*, *Revolver* ; *Aftermath*, *Between the Buttons*) puis redescend un peu ; les Stones
  allongent leurs chansons quand les Beatles reviennent à des formats courts.
- **Dylan fait le chemin inverse** : il commence long, dense et sombre (chansons protestataires et talking blues),
  culmine vers 1965-66 (*Highway 61*, *Blonde on Blonde*), puis raccourcit et s'éclaircit nettement à partir de
  1967-69 (*John Wesley Harding*, *Nashville Skyline* : valence +0,23, comme les Beatles).
- Les Beatles restent les plus positifs sur toute la période.

## Limites

- Les débuts des Stones contiennent surtout des reprises : seulement 21 compositions dans leurs trois premières
  années (et aucune en 1963), d'où une première étape fragile. Les points creux de `fig3` ont moins de 5 chansons.
- Couverture : 87 % des titres officiels des Stones et 72 % de ceux de Dylan sont dans Genius (la liste de Dylan
  inclut des Basement Tapes et des titres rares, souvent absents).
- Quelques titres des Stones n'ont existé que sur des sorties d'archives tardives : leur année est celle de cette
  sortie (hors de la fenêtre de neuf ans, donc sans effet sur la partie « évolution »).
- Le vocabulaire total (`summary.csv`) dépend de la taille du corpus (Dylan a deux fois plus de mots que les
  Beatles) : pour comparer la richesse, se fier au MATTR.
- Refrains : marqués par Genius, ou détectés automatiquement quand les paroles n'ont pas d'en-têtes (3 à 5 % des
  chansons).

## Fichiers

- `summary.csv` : profil global ; `song_metrics.csv` : une ligne par chanson (titre, année, mesures).
- `pairwise_tests.csv` : tests de Mann-Whitney deux à deux.
- `distinctive_words.csv` : 20 mots par artiste (z de Monroe, occurrences, nombre de chansons).
- `similarity_between_artists.csv` : similarité moyenne entre catalogues.
- `career_stages.csv`, `career_years.csv`, `decades.csv` : évolution.
- `fig1_profile.png` (distributions), `fig2_distinctive_words.png`, `fig3_first_nine_years.png`,
  `fig4_pronouns_choruses.png`.
