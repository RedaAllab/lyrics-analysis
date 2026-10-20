# Les Beatles et les autres : comparaison des paroles

Analyse hors ligne, affichée aussi dans l'app (page « Other artists »). Huit catalogues passent par le même
pipeline que l'app (`beatles_viz.corpus.build_corpus` : sections, MATTR, répétition, humeur VADER), compositions
originales seulement, chansons d'au moins 30 mots :

- **groupes des années 60** : les Beatles, les Rolling Stones ;
- **les Beatles après les Beatles** : Paul McCartney (Wings compris), John Lennon ;
- **auteurs-compositeurs** : Bob Dylan, Leonard Cohen, Joni Mitchell, Paul Simon.

Les fichiers ici ne contiennent que des chiffres, des titres et des mots isolés : aucune parole n'est citée.

## Données

| Artiste | Liste officielle | Titres officiels | Chansons retenues | Compositions analysées |
|---|---|---|---|---|
| The Beatles | *List of songs recorded by the Beatles* | | 272 | 209 |
| The Rolling Stones | *List of songs recorded by the Rolling Stones* | 445 | 387 | 293 |
| Bob Dylan | *List of songs written by Bob Dylan* | 560 | 403 | 403 |
| Paul McCartney | *List of songs recorded by Paul McCartney* | 590 | 445 | 382 |
| John Lennon | *List of songs recorded by John Lennon* | 157 | 115 | 95 |
| Leonard Cohen | pistes de 15 albums studio | 143 | 139 | 133 |
| Joni Mitchell | pistes de 17 albums studio | 177 | 170 | 162 |
| Paul Simon | pistes de 13 albums studio | 144 | 132 | 132 |

- L'année est celle de la première sortie (liste Wikipédia, ou album pour Cohen, Mitchell et Simon, qui n'ont pas
  de liste de chansons sur Wikipédia : `scripts/album_song_list.py` lit les pistes de leurs albums studio, sans
  les titres bonus des rééditions ni les albums de reprises ou de réenregistrements). L'année du dataset Genius
  n'est pas fiable (pour les Beatles elle ne tombe juste que dans 78 % des cas).
- Une ligne par titre officiel : le titre studio quand Genius l'a, sinon une version Live/Demo/Take, en gardant
  les paroles les plus longues (≥ 20 mots). Pour McCartney, Genius range les Wings sous un autre nom
  (« Paul McCartney & Wings ») : les deux sont réunis.
- « Original » : écrit ou coécrit par l'artiste (pour les Stones : Jagger, Richards, Nanker Phelge… ; pour Lennon :
  avec Yoko Ono) ; les Beatles reprennent la colonne `is_original` du fichier de l'app.
- Les noms propres (majuscule en milieu de ligne dans ≥ 90 % des cas) sont exclus des mots distinctifs.

Reproduire (les paroles restent dans `data/`, ignoré par git) :

```bash
curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_recorded_by_the_Rolling_Stones&action=render" -o stones.html
curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_written_by_Bob_Dylan&action=render" -o dylan.html
curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_recorded_by_Paul_McCartney&action=render" -o mccartney.html
curl -sL "https://en.wikipedia.org/w/index.php?title=List_of_songs_recorded_by_John_Lennon&action=render" -o lennon.html
python scripts/album_song_list.py "Leonard Cohen" cohen.html
python scripts/album_song_list.py "Joni Mitchell" mitchell.html
python scripts/album_song_list.py "Paul Simon" simon.html
python scripts/build_artist.py "The Rolling Stones" stones.html raw/genius
python scripts/build_artist.py "Bob Dylan" dylan.html raw/genius
python scripts/build_artist.py "Paul McCartney" mccartney.html raw/genius --alias "Paul McCartney & Wings"
python scripts/build_artist.py "John Lennon" lennon.html raw/genius
python scripts/build_artist.py "Leonard Cohen" cohen.html raw/genius
python scripts/build_artist.py "Joni Mitchell" mitchell.html raw/genius
python scripts/build_artist.py "Paul Simon" simon.html raw/genius
python scripts/compare_artists.py data/beatles/beatles.parquet data/rolling_stones/rolling_stones.parquet \
  data/bob_dylan/bob_dylan.parquet data/paul_mccartney/paul_mccartney.parquet data/john_lennon/john_lennon.parquet \
  data/leonard_cohen/leonard_cohen.parquet data/joni_mitchell/joni_mitchell.parquet data/paul_simon/paul_simon.parquet
```

## Résultats (médianes par chanson)

| | Beatles | Stones | McCartney | Lennon | Dylan | Cohen | Mitchell | Simon |
|---|---|---|---|---|---|---|---|---|
| Mots par chanson | 183 | 236 | 206 | 185 | 258 | 240 | 232 | 225 |
| Richesse du vocabulaire (MATTR-50) | 0,64 | 0,64 | 0,65 | 0,65 | **0,77** | 0,72 | 0,76 | 0,74 |
| Lignes répétées (part des mots) | **33 %** | 20 % | **33 %** | 24 % | 9 % | 21 % | 10 % | 14 % |
| Chansons avec un refrain | 64 % | 70 % | 77 % | 68 % | **32 %** | 65 % | 79 % | 72 % |
| Humeur (valence VADER, −1 à 1) | +0,22 | +0,02 | **+0,25** | +0,09 | +0,04 | +0,10 | +0,15 | +0,10 |
| « I / me / my » (part des mots) | **9,4 %** | 7,0 % | 6,3 % | 4,2 % | 6,9 % | 7,7 % | 4,1 % | 6,0 % |

Tests de Mann-Whitney deux à deux dans `pairwise_tests.csv`.

1. **Deux familles de vocabulaire.** D'un côté les Beatles, les Stones, McCartney et Lennon, tous à 0,64-0,65 de
   MATTR (aucune différence significative entre eux, p > 0,3) ; de l'autre les quatre auteurs-compositeurs, de
   0,72 (Cohen) à 0,77 (Dylan). Le MATTR ne dépend pas de la longueur des chansons : chez les auteurs-compositeurs,
   chaque fenêtre de 50 mots contient 4 à 6 mots différents de plus.
2. **McCartney prolonge les Beatles, Lennon s'en éloigne.** McCartney garde exactement la répétition des Beatles
   (33 % de lignes répétées, p = 0,81) et leur humeur (+0,25, p = 0,14), avec encore plus de refrains (77 %). Lennon
   répète moins (24 %), est nettement plus sombre (+0,09, p = 0,006 contre les Beatles) et parle beaucoup moins à
   la première personne (4,2 % de « I / me / my » contre 9,4 %).
3. **Ce que les Beatles disent de plus que les autres** : *know, girl, love, lonely, yes* et le « je / tu » (ce
   sont eux qui disent le plus *I* et *you*). Les solos se partagent cet héritage : McCartney garde *love, joy,
   tonight, lonely* ; Lennon passe au collectif et au politique : *people, power, peace, war, free, world, human*.
4. **Les auteurs-compositeurs ont chacun leur monde** : Dylan la route et le vent (*road, wind, walking, west*) et
   la langue parlée (*ain't, ya*) ; Cohen le corps et le sacré (*lover, body, beauty, broken, naked, holy,
   longing*) ; Mitchell les images (*blue, black, green, angel, wings, paper, garden, window*) ; Simon le ciel et le
   doute (*maybe, skies, summer, stars, prayers, bones*).
5. **L'humeur** : McCartney et les Beatles sont les plus positifs (+0,22 à +0,25, et ~1,6 % de mots négatifs contre
   ~3 % pour tous les autres). Les Stones et Dylan sont les plus neutres ; Lennon, Cohen, Simon et Mitchell sont
   entre les deux. VADER compte des mots sans contexte : c'est une tendance de vocabulaire, pas une lecture fine.
6. **Proximité des catalogues** (`similarity_between_artists.csv`, cosinus TF-IDF moyen entre chansons) :
   McCartney et Lennon ressemblent plus aux Beatles qu'à n'importe qui d'autre ; Cohen, Mitchell et Simon sont
   chacun plus proches de Dylan que des Beatles. Les écarts restent faibles (0,022 à 0,038).

## Évolution : les neuf premières années de carrière

Fenêtre : **les neuf ans qui suivent le premier disque**, car c'est toute la carrière des Beatles (1962-1970) ;
c'est la seule façon de comparer tout le monde au même « âge ». Débuts retenus : Beatles 1962, Stones 1963,
Dylan 1962, Cohen 1967, Mitchell 1968, Lennon 1969, McCartney 1970, et Paul Simon 1972 (premier album solo après
Simon & Garfunkel ; le *Songbook* de 1965, chansons qu'il a ensuite réenregistrées avec Garfunkel, tombe avant).
Tableaux : `career_stages.csv` (trois étapes de trois ans), `career_years.csv` (année par année).

| MATTR par étape | Années 1-3 | Années 4-6 | Années 7-9 |
|---|---|---|---|
| Beatles | 0,64 | 0,67 | 0,61 |
| Rolling Stones | 0,62 | 0,68 | 0,66 |
| Paul McCartney | 0,55 | 0,59 | **0,69** |
| John Lennon | 0,56 | 0,65 | (1 chanson) |
| Bob Dylan | 0,77 | 0,80 | 0,74 |
| Leonard Cohen | 0,77 | 0,76 | 0,70 |
| Joni Mitchell | 0,76 | 0,77 | **0,79** |
| Paul Simon | 0,68 | 0,70 | 0,74 |

- **Les deux ex-Beatles démarrent très bas** (0,55-0,56, en dessous des Beatles à leurs débuts) puis s'enrichissent :
  McCartney gagne 0,14 en neuf ans et finit au-dessus des Beatles de la fin.
- **Mitchell et Simon s'enrichissent avec le temps, Dylan et Cohen culminent tôt** : Dylan au milieu des années 60,
  Cohen dès ses premiers disques.
- Beatles et Stones suivent la même courbe : sommet au milieu de la décennie, léger repli ensuite.

## Limites

- Lennon n'a que 95 compositions analysées, et une seule dans ses années 7-9 (1975-77, sa retraite) ; les débuts
  des Stones sont surtout des reprises (21 compositions en trois ans). Les points creux de `fig3` ont moins de 5
  chansons.
- Couverture : 72 % (Dylan) à 97 % (Cohen) des titres officiels sont dans Genius. Pour Paul Simon, l'album
  *Stranger to Stranger* (2016) n'a pas de liste de pistes lisible et *Seven Psalms* (2023) n'est pas dans Genius.
- Refrains : marqués par Genius, ou détectés automatiquement quand les paroles n'ont pas d'en-têtes. C'est le cas
  de 44 % des chansons de Cohen (3 à 18 % pour les autres) : sa part de refrains est la moins fiable.
- Le vocabulaire total (`summary.csv`) dépend de la taille du corpus : pour comparer la richesse, se fier au MATTR.
- Deux restes du découpage en mots sont exclus des mots distinctifs : *caf* (« café » coupé à l'accent) et *em*.

## Fichiers

- `summary.csv` : profil global ; `song_metrics.csv` : une ligne par chanson (titre, année, mesures).
- `pairwise_tests.csv` : tests de Mann-Whitney deux à deux.
- `distinctive_words.csv` : 20 mots par artiste (z de Monroe contre tous les autres, occurrences, nombre de chansons).
- `similarity_between_artists.csv` : similarité moyenne entre catalogues.
- `career_stages.csv`, `career_years.csv`, `decades.csv` : évolution.
- `fig1_profile.png` (distributions), `fig2_distinctive_words.png`, `fig3_first_nine_years.png`,
  `fig4_pronouns_choruses.png`.
