# Presentations and documents

Decks and reports carry the same tokens as the app, so a chart or number looks the same on screen, on a slide and on paper.

## Presentations

- 16:9 at 1920×1080. Layouts: Title (navy), Section divider (Diploma), Headline + chart, Big number; see SlideLayouts.
- Type: `slide-title`, `slide-heading`, `slide-body`, `slide-stat`, `slide-caption`. Nothing below 20px; body never below 24px.
- Headlines state the takeaway as a sentence. One idea per slide, at most three bullets.
- Every data slide has a source line bottom-left and a folio bottom-right.
- Charts use the same `chart-*` order as the dashboard; export charts from the app rather than redrawing them.
- Title and closing slides carry the official GT logo from the Logos group: `GTLogo_GoldWhite.svg` or `GTLogo_White.svg` on navy, `GTLogo_RGB.svg` on white or Diploma. Start from GT's PowerPoint template (2022 rev) when one is required.

## Documents

- US Letter, 1-inch margins. Title block, numbered sans headings, IBM Plex Serif body at 11pt; see DocumentLayout.
- Lead with a Summary; put any decision needed in a Diploma callout with the gold rule.
- Tables and figures get numbered captions with source and date. Sample or provisional figures say so.
- Always navy ink on white, whatever theme the app is in.

## Applying the system in Office and Google tools

| Setting | Value |
| --- | --- |
| Theme dark 1 / light 1 | `gt-navy` #051E39 / `gt-white` #FFFFFF |
| Theme dark 2 / light 2 | `navy-11` #003D69 / `gt-diploma` #F9F6E5 |
| Accents 1–6 | `chart-1` to `chart-6` (day values) |
| Hyperlink | `navy-9` #004C97 |
| Heading font | Barlow SemiBold (fallback: DIN 2014, then Roboto) |
| Body font | IBM Plex Sans (slides), IBM Plex Serif (documents) |
