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

## To improve
1. **Box plot on Artists** uses pastel box fills from Streamlit's categorical colours; set the fills explicitly.
2. **Corpus tabs** are small and underlined rather than the solid-ink tabs used elsewhere; check the selected state.
3. **Info box** on My songs keeps Streamlit's blue tint; restyle with `--lx-rule` border and card background.
4. **Mobile header**: the sidebar logo shrinks to the icon plus a `»` toggle; fine, but the title block starts low.
5. **Listen player** (synced sections bar): unplayed segments at 55 % opacity read grey on paper; raise contrast.
6. **Fonts**: IBM Plex and Space Grotesk load from Google Fonts at runtime; a slow connection shows a fallback flash.
