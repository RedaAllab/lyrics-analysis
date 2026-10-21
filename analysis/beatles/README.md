# Les Beatles : tables et figures

Produites par `scripts/analyse_beatles.py` à partir des compositions originales analysables (209 chansons d'au moins
30 mots, mêmes règles que l'app). Elles ne contiennent que des chiffres, des titres et des mots isolés.

| Fichiers | Ce qu'ils disent | Niveau de preuve |
|---|---|---|
| `global_summary.csv`, `top_words_content.csv`, `fig1`, `fig2` | vocabulaire du corpus | descriptif |
| `year_summary.csv`, `phase_summary.csv`, `fig3` | longueur, richesse, répétition par année et période | descriptif |
| `distinctive_words_by_phase.csv`, `fig4`, `word_trends_per_1000_tokens.csv`, `fig5` | mots propres à chaque période | exploratoire |
| `lead_voice_summary.csv`, `distinctive_words_by_lead_voice.csv`, `fig6`, `fig7` | les chansons que chaque membre **chante** | descriptif pour les chiffres ; **à ne pas lire comme l'écriture** |
| `credit_summary.csv`, `distinctive_words_by_credit.csv`, `fig8` | Harrison contre Lennon–McCartney, selon le **crédit officiel** | exploratoire |
| `song_metrics.csv` | une ligne par chanson : voix principale, crédit, mesures | descriptif |

Précautions :

- **Voix principale ≠ auteur.** 169 des 209 compositions sont créditées « Lennon–McCartney », quel que soit celui qui
  a écrit. Une chanson chantée par Lennon n'est pas une chanson de Lennon. Ces tables s'appelaient `*_singer*` jusqu'au
  21/10/2026 ; elles ont été renommées pour que leur titre dise ce qu'elles mesurent.
- **Le crédit officiel est la seule comparaison d'auteurs possible aujourd'hui**, et seulement Harrison (25 chansons)
  contre la paire Lennon–McCartney. Séparer Lennon et McCartney demande les attributions documentées
  (`data/credits/manual_claims.csv`).
- **Mots distinctifs** (log-odds de Monroe et al.) : la colonne `songs_using` dit combien de chansons du groupe
  emploient le mot. Un mot répété dans une seule chanson peut sembler typique : chez Harrison, « sun » et « comes »
  viennent presque tous de *Here Comes the Sun*, et 28 des 41 « long » de *Blue Jay Way*.
