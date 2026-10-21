# Session-sheet theme: visual review

Checked on 2026-10-21, every page at 800 px wide, home / song / voices at 375 px. Console: only
`/<page>/_stcore/health` and `host-config` 404s, a dev-server artefact on sub-page URLs, not the theme.

## Works
- Light theme, Space Grotesk titles, mono kickers, square cards and buttons on all pages.
- Charts share one look (ink axes, light horizontal rules, palette colours); heatmaps use the shared sequential scale.
- Verse cards: white background, ink text, left border in the voice colour (fonts and animations kept).
- Mobile: banner, search row, metrics two by two and stacked buttons hold up.

## To improve
1. **Truncated metric labels and deltas** (Song, Albums, Word, Voices, Corpus): "LEXICAL RICHN…", "DISTINCT WO…",
   "+358 vs m…", "90 of …", "McCa…". Shrink the label size or allow wrapping in `[data-testid="stMetricLabel"]`,
   and let the delta pill wrap.
2. **Truncated buttons at 800 px** on the Song page: "Add to f…", "← Previ…".
3. **Voices, "over time" chart**: two legends (Plotly's and Streamlit's "voice"), the second cut off. Hide one.
4. **Voices radar** is small and its labels crowd the plot; give it more height.
5. **Segmented control** (Artists, "Show") selects with a grey fill while tabs select with solid ink: pick one.
6. **Box plot on Artists** uses pastel box fills from Streamlit's categorical colours; set the fills explicitly.
7. **Corpus tabs** are small and underlined rather than the solid-ink tabs used elsewhere; check the selected state.
8. **Info box** on My songs keeps Streamlit's blue tint; restyle with `--lx-rule` border and card background.
9. **Mobile header**: the sidebar logo shrinks to the icon plus a `»` toggle; fine, but the title block starts low.
10. **Listen player** (synced sections bar): unplayed segments at 55 % opacity read grey on paper; raise contrast.
11. **Fonts**: IBM Plex and Space Grotesk load from Google Fonts at runtime; a slow connection shows a fallback flash.
