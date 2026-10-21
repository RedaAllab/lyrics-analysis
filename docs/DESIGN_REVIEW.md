# Session-sheet theme: visual review

Checked on 2026-10-21, every page at 800 px wide, home / song / voices at 375 px. Console: only
`/<page>/_stcore/health` and `host-config` 404s, a dev-server artefact on sub-page URLs, not the theme.

## Works
- Light theme, Space Grotesk titles, mono kickers, square cards and buttons on all pages.
- Charts share one look (ink axes, light horizontal rules, palette colours); heatmaps use the shared sequential scale.
- Verse cards: white background, ink text, left border in the voice colour (fonts and animations kept).
- Mobile: banner, search row, metrics two by two and stacked buttons hold up.

## Fixed
1. Truncated metric labels, values and deltas now wrap (`identity.py`).
2. Truncated buttons on Song: wrapping enabled, Previous/Next and favourite/stars/listen columns widened.
3. Voices: this was a misreading (radar and line chart each have one legend); the redundant "voice" legend title is removed.
4. Voices radar: taller, with larger margins.
5. Segmented controls now select in solid ink, like the tabs.

6. Artists and Corpus box plots: solid fills in the group colour, ink outline and median (`viz.theme.solid_boxes`).
7. Tabs (Corpus and others): the old `data-baseweb` selectors matched nothing in this Streamlit version; they now target
   `data-testid="stTab"`, selected tab in solid ink.
8. Notices (`st.info`, `st.warning`): card background, ink frame, thick left edge, no tint.
9. Phone: top padding of the page reduced so the title starts higher.
10. Listen player: unplayed sections at 80 % opacity, the current one outlined by an ink bar.

## To improve
1. **Fonts**: IBM Plex and Space Grotesk load from Google Fonts at runtime, so a slow connection shows a fallback flash.
   `st.html` strips `<link rel="preconnect">`, so the only real fix is to self-host the font files
   (`enableStaticServing` plus `[[theme.fontFaces]]` in `config.toml`), which needs the woff2 files added to the repository.
