# Pistes produit : Lyrics Explorer

Réflexion du 19/10/2026, à partir de l'app actuelle (Home, Song avec Lire/Analyser, Compare, Corpus) et d'une recherche de projets proches.

## Cadrage

**Deux usages à servir**
- **Toi, en local** : « quand une chanson me trotte dans la tête, je veux comprendre comment elle est construite et ce qui la rend unique ».
- **Un visiteur de l'app publique** (statistiques seulement, sans paroles) : « je veux apprendre quelque chose de surprenant sur les Beatles en 2 minutes ».

**Constat** : l'app est solide pour le premier usage (une chanson, deux chansons). Elle est faible pour le second : rien ne raconte une histoire, et les découvertes restent à faire soi-même. Elle ne crée pas non plus de raison de revenir.

**Hypothèse la plus risquée** : que le visiteur public vienne pour explorer librement. Les projets qui marchent dans ce domaine (data stories, « scrollytelling ») guident le lecteur au lieu de lui donner des filtres. À tester en premier, à faible coût : une histoire guidée de 4 écrans, et voir si on la parcourt jusqu'au bout.

## Ce que j'ai trouvé (même stack ou même sujet)

| Projet | Ce qu'on peut reprendre |
|---|---|
| [SongSim de Colin Morris, présenté sur R-bloggers](https://www.r-bloggers.com/2019/03/decode-lyrics-in-pop-music-visualise-prose-with-the-songsim-algorithm/) et [sa discussion sur r/dataisbeautiful](https://www.reddit.com/r/dataisbeautiful/comments/5zkqr6/patterns_in_song_lyrics_visualized_using/) | La matrice de répétition comme « empreinte » d'une chanson, reconnaissable d'un coup d'œil, et un score de répétition comparable entre chansons |
| [MusicPlot (article)](https://wlouie1.github.io/MusicPlot/musicplot_paper.pdf) | Une matrice d'auto-similarité interactive, avec un panneau de réglages et un lien entre la matrice et le texte |
| [Corpus WASABI, segmentation par matrice d'auto-similarité (arXiv)](https://arxiv.org/html/1912.02477v2) | Détecter automatiquement couplets et refrains quand les balises manquent (21 chansons chez nous) |
| [Lyrics Analysis & Music Recommendation (Streamlit)](https://github.com/NotShrirang/Lyrics-Analysis-and-Music-Recommendation-with-Pair-Similarities) | Des recommandations de chansons proches par similarité TF-IDF des paroles. Ça marche avec nos comptes de mots, donc aussi en public |
| [Dashboard Billboard Top 100 (sujet GitHub « lyrics-analysis »)](https://112.cachefly.net/topics/lyrics-analysis) | Le sentiment par artiste et par période, un axe qu'on a mis de côté |
| [best-of-streamlit](https://github.com/jrieke/best-of-streamlit), [galerie Streamlit](https://streamlit.io/gallery) | Des modèles de mise en page multipage et d'accueil |
| [streamlit-extras](https://github.com/arnaudmiribel/streamlit-extras) | Des briques prêtes : cartes stylisées, conteneurs stylables, stockage navigateur (pour des favoris) |
| [st_yled studio](https://discuss.streamlit.io/t/st-yled-studio-explore-and-configure-your-streamlit-theme-and-style-components/119932) et [les nouveautés Streamlit fin 2025](https://levelup.gitconnected.com/my-top-5-new-streamlit-features-from-the-q4-2025-releases-647c78fc49c6) | Un thème réutilisable dans un fichier TOML, et le style de composants sans CSS fragile |

## Fonctionnalités proposées

Impact et effort sont estimés à vue : I = impact, E = effort, sur une échelle de 1 à 3.

### Maintenant (fort impact, effort faible)
1. **« Chansons proches »** (I3, E1). Sur la page Song, les 5 chansons au vocabulaire le plus proche (similarité cosinus des comptes de mots, pondérée TF-IDF). Ça crée une navigation de proche en proche, et ça marche aussi dans l'app publique.
2. **Page « Mot »** (I3, E2). On tape un mot et on voit sa biographie :
   - son usage par année ;
   - qui le chante ;
   - les chansons où il pèse le plus ;
   - les mots qui l'accompagnent.
   Les mots caractéristiques ailleurs dans l'app deviennent des liens vers cette page.
3. **Score de répétition + empreinte SongSim** (I2, E1). Un score par chanson, classé dans le corpus, et une miniature de la matrice affichée sur les fiches de l'accueil et dans Compare.

### Ensuite
4. **Vue par album** (I3, E2). Une page par sortie :
   - la richesse lexicale de chaque piste ;
   - une mini-frise de structure par piste ;
   - les mots propres à l'album.
   Une ligne de temps des albums complète la page Corpus.
5. **Profils de voix** (I2, E2). Lennon, McCartney, Harrison et Starr chacun sur une fiche : radar des métriques, mots caractéristiques, évolution dans le temps. Le face-à-face Lennon / McCartney attirera les visiteurs.
6. **Histoires guidées** (I3, E2). 3 ou 4 constats racontés en quelques écrans, chacun avec son graphique. Par exemple :
   - « love » s'efface après 1965 ;
   - les paroles se densifient en 1964-65 ;
   - le « je » recule en 1966-67.
   C'est la meilleure porte d'entrée pour un visiteur.
7. **Détection automatique des sections** (I2, E2). Pour les chansons sans balises : repérer les blocs qui se répètent dans la matrice et en déduire couplets et refrains.

### Plus tard
8. **Jeu « Qui chante ? »** (I2, E1). On montre les mots caractéristiques d'une chanson (jamais ses paroles) et on devine la voix. C'est une raison de revenir.
9. **Carte partageable** (I2, E2). Une image de l'empreinte d'une chanson (structure, score, voix) à télécharger.
10. **Sentiment et thèmes** (I2, E2), mis de côté depuis le début du projet.
11. **Notes et favoris personnels** (I1, E1), en local seulement.
12. **Écoute** (I2, E3). Des liens vers les versions officielles (lecteurs intégrés des plateformes), sans héberger d'audio. Il faut faire correspondre chaque titre à son identifiant sur la plateforme.

## Suivi (20/10/2026)

| # | Fonctionnalité | Statut |
|---|---|---|
| 1-3 | Chansons proches, page Mot, score de répétition et empreinte | Fait |
| 4 | Vue par album | Fait : page Albums (frise des sorties, structure de chaque piste, pistes comparées, mots de l'album, empreintes) |
| 5 | Profils de voix | Fait : page Voices, deux voix face à face (Lennon / McCartney par défaut) |
| 6 | Histoires guidées | Fait : page Stories, 4 constats dont le texte est calculé à partir des données |
| 7 | Détection des sections | Fait pour 16 des 21 chansons sans balises ; parmi les compositions originales, 3 restent en un seul bloc parce qu'aucune strophe n'y revient (Bad to Me, I'm in Love, Madman). Mesurée sur les chansons balisées : 70 % des lignes bien classées (62 % en classant tout en couplet), F1 de 0,65 sur les refrains |
| 8 | Jeu « Qui chante ? » | Fait : page Who sings?, 6 mots caractéristiques d'une chanson (jamais ses paroles, mots du titre exclus) et 4 voix à deviner, score de la session |
| 9 | Carte partageable | Fait : image 1200 x 630 à télécharger, dessinée dans le style « session sheet » |
| 10 | Sentiment et thèmes | Fait : page Mood et section de la fiche chanson. Valence des mots (lexique VADER, MIT), 9 thèmes en listes de mots. Sans contexte : la négation et l'ironie échappent au score |
| 11 | Notes et favoris personnels | Fait, en local : favori, note sur 5, notes, journal d'écoute, page My songs |
| 12 | Écoute | Fait sous forme de liens de recherche vers 4 plateformes (pas d'identifiants de pistes, pas de lecteur intégré) |
| Design | Pastilles de voix, gabarit Plotly unique, mobile (métriques 2 x 2, titres qui passent à la ligne, légendes sous les graphiques) | Fait |
| Design | Thème « session sheet » : thème Streamlit clair, gabarit Plotly commun, polices hébergées, carte de partage assortie, test qui garde thème et palette alignés | Fait (voir `DESIGN_REVIEW.md`) |

## Design

- **Empreinte de chanson** : en tête de la page Song, une bande avec la mini-frise de structure, la couleur de la voix et le score de répétition. C'est l'élément visuel signature de l'app.
- **Fiches de l'accueil** : ajouter la miniature de la matrice. Les fiches deviennent visuelles et toutes différentes, comme des pochettes.
- **Filtres de voix** : remplacer la liste déroulante par des pastilles cliquables aux couleurs des voix (`st.pills`). C'est plus visible et plus direct.
- **Gabarit Plotly unique** : police, couleurs et marges définies une seule fois, appliquées à tous les graphiques.
- **Mobile** :
  - métriques en grille 2 x 2 ;
  - matrice de répétition par section ;
  - frise de structure en hauteur.
- **États vides et chargements** : un texte qui dit ce qui arrive (« Analysing 211 songs… ») plutôt qu'un spinner nu.
- **Thème clair optionnel** : la version de Streamlit en ligne (1.66) le permet mieux que la version locale (1.45).

## Prérequis techniques

- **Versions alignées (fait)** : passer en local à la version de Streamlit utilisée en ligne (1.66) et fixer les versions dans `requirements.txt`. On développe aujourd'hui sur la 1.45 et on déploie sur la 1.66, ce qui bloque l'usage des nouveautés (thèmes réutilisables, `st.pills`, etc.).
- **Calculs de similarité** (TF-IDF, voisins) : les faire une fois et les mettre en cache, avec les comptes de mots publics, pour que les nouvelles fonctions marchent aussi dans l'app déployée.

## Mis de côté
- **Pochettes d'albums** : ce sont des images protégées, donc remplacées par des tuiles abstraites colorées.
- **Génération de paroles « à la manière de »** : hors sujet, et risquée pour les droits.
