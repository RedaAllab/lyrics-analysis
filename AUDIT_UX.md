# Audit UX : Beatles lyrics explorer

Relevé du 19/10/2026 sur l'app locale : accueil et ses 5 onglets, page Song, page Read. Testé en largeur bureau (1280 px) et mobile (375 px), en thème sombre. La page Read n'a été inspectée que par sa structure et ses styles.

## Cadrage

Deux usages, deux publics :
- **Toi, en local** : « quand je pense à une chanson, je veux voir ce qui la rend particulière et la relire avec sa structure ».
- **Un visiteur de l'app publique** : « je veux comprendre en deux minutes comment l'écriture des Beatles a évolué ».

**Diagnostic principal** : l'app est organisée par type d'analyse (onglets, puis pages) et non par parcours. La chanson, qui est l'entrée naturelle, est isolée. Rien ne mène de l'accueil vers une chanson, et la même chanson est éclatée sur deux pages (Song et Read).

## Constats

### A. Navigation et architecture
1. **Noms de pages** : la navigation affiche « beatles app » (le nom du fichier), « Song » et « Read ». L'interface est en anglais alors que tu travailles en français.
2. **Trois modèles de filtres différents** :
   - l'accueil propose un bouton radio pour le corpus, un curseur d'années et « Lead singer » (avec la valeur « Other ») ;
   - Song et Read proposent un interrupteur, « Lead voice » (avec « Neutral ») et un sélecteur de chanson.
   Le vocabulaire change (singer / voice, Other / Neutral) et les filtres ne suivent pas d'une page à l'autre.
3. **Aucun chemin du corpus vers une chanson** : on ne peut cliquer ni sur le tableau Songs, ni sur les points du nuage, ni sur les mots caractéristiques.
4. **Song et Read sont deux pages pour une même chanson**, reliées seulement par un lien texte, et dans un seul sens.

### B. Lisibilité des données
5. **Jargon** : MATTR-50, z-score, `in_group`, « Used once », `repeat_ratio`.
6. **Tableaux bruts** : on voit les noms de colonnes du code (`release_core`, `tokens`, `types`, `mattr`, `repeat_ratio`) et des décimales non arrondies (0.631).
7. **Flèches de variation trompeuses** sur la page Song : « −59 vs median » s'affiche en rouge avec une flèche vers le bas. Une chanson courte n'est pas « moins bonne ».
8. **Double titre** : chaque graphique a une question en petit gris au-dessus, puis un titre. C'est redondant, et la question est peu contrastée.
9. **Couleurs incohérentes** : la page Song utilise les couleurs des voix, mais l'accueil utilise les couleurs par défaut de Plotly (la boîte à moustaches par chanteur est toute bleue).
10. **Boîte à moustaches écrasée** (onglet Lead singers) : une chanson d'environ 1 200 mots écrase l'échelle, et toutes les autres boîtes se tassent en bas.
11. **Carte des répétitions illisible** : pas d'axes ni de repères de sections. Sur mobile (337 px), on ne peut rien y lire.
12. **Étiquettes de sections** du graphique de densité : elles se chevauchent encore sur les largeurs étroites.
13. **Mots caractéristiques** : présentés comme 4 tableaux de chiffres. Un graphique en barres ou des étiquettes de taille variable se liraient d'un coup d'œil.

### C. Page Read
14. **Animations en continu** : 8 animations tournent sans fin pendant la lecture (par exemple la pulsation de Harrison sur chaque section). C'est distrayant et contraire au critère WCAG 2.2.2 (pouvoir mettre en pause un mouvement qui dure plus de 5 secondes).
15. **En-têtes de section trop petits** (12 px, majuscules, opacité 0,75), et **aucune légende** qui explique quel effet correspond à quelle voix.
16. **Paramètres techniques exposés** : les réglages des effets affichent les noms internes (`rare_max_songs`, `chorus_scale`, `line_height`).
17. **Le texte commence tard** : en bureau, il démarre à environ 430 px du haut, sous le choix d'ordre de navigation, les boutons, l'en-tête et les métriques. Les boutons précédent et suivant n'existent qu'en haut.

### D. Mobile
18. **Bon point** : pas de défilement horizontal.
19. **Métriques empilées** : les 4 métriques occupent tout le premier écran, et la page Song fait environ 3 400 px de haut.
20. **Barre d'outils Plotly** : elle est toujours visible et chevauche les titres des graphiques.

### E. Identité visuelle
21. **Pas d'identité** : c'est le thème Streamlit par défaut. Le titre « The Beatles - lyrics vocabulary » utilise un tiret simple. Les seuls éléments de caractère sont dans la page Read (les effets par voix).

## Pistes, par priorité

### Gains rapides (moins d'une heure chacun)
- **Noms et langue** : renommer les pages (« Corpus », « Chanson », « Lecture ») avec `st.navigation` et des icônes, et choisir une seule langue.
- **Tableaux** : noms de colonnes lisibles et formats arrondis (`st.column_config`).
- **Métriques** : flèches neutres (`delta_color="off"`) et infobulles (`help=`) qui expliquent MATTR, z-score et « mots uniques ».
- **Titres** : un seul titre par graphique, formulé comme la question.
- **Graphiques** :
  - masquer la barre d'outils Plotly ;
  - partager un gabarit Plotly avec les couleurs des voix sur toutes les pages ;
  - passer la boîte à moustaches en échelle logarithmique, ou plafonner les valeurs extrêmes en les signalant.

### Chantiers moyens
- **Filtres** : un seul composant, avec le même vocabulaire (« voix »), dont l'état est conservé dans `st.session_state` d'une page à l'autre.
- **Chemin vers les chansons** : tableau Songs cliquable (colonne de liens vers la chanson), mots caractéristiques reliés aux chansons qui les contiennent.
- **Page Read, lisibilité** : légende des voix en haut (pastilles colorées), en-têtes de section plus grands, réglages avec des libellés humains.
- **Page Read, animations** : elles se jouent une fois à l'apparition de la section, ou au survol. Un « mode calme » est actif par défaut.
- **Carte des répétitions** : bandes de sections sur les axes, et version par section sur mobile.

### Paris plus ambitieux
- **Page chanson unique (mon choix)** : fusionner Song et Read en une seule page avec deux vues, « Lire » et « Analyser ». C'est la même chanson, le même contexte et les mêmes filtres.
- **Accueil orienté chanson** : une recherche de titre mise en avant, une sélection de chansons à découvrir, puis la vue corpus.
- **Comparaison de deux chansons** côte à côte (par exemple une de Lennon et une de McCartney de la même année).
- **Identité visuelle** : thème Streamlit personnalisé (`.streamlit/config.toml`), une couleur d'accent, une police de titre avec du caractère, la palette des voix comme fil conducteur.

## Hypothèse à vérifier en premier

La fusion Song + Read et l'accueil orienté chanson supposent que **l'usage principal est l'exploration chanson par chanson**, plutôt que les tendances du corpus. C'est l'hypothèse la plus risquée. Le test le moins coûteux : noter pendant une semaine par quelle page tu entres et où tu restes.

## Mis de côté pour l'instant
- Mode sombre propre aux cartes de la page Read : les cartes claires ressortent bien sur le fond sombre.
- Animations plus riches (synchronisées avec l'audio) : hors de portée sans source audio.
