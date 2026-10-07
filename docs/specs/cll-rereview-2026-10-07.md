# CLL Initiative Dashboard: Re-review after the 11 fixes

7 October 2026 · http://127.0.0.1:8000 · as **Bill**, plus **Kevin** for the admin
views. The session was switched back to Bill afterwards. Read-only: the reviewer
opened the Update form and the New initiative form, but submitted neither.

**Viewport.** The first few minutes ran at 758 px wide because the Chrome side
panel was open. The window then widened to **1518 × 921 CSS px**. Every screenshot
and layout claim below comes from 1518 px. The capture tool takes the visible
viewport only, so long pages were covered by several shots rather than one
full-page image.

**Which 11 fixes.** Taken to be findings #1–#11 from the 6 October report.

---

## 1. Verdicts on the 11 fixes

| # | Fix | Verdict | Evidence |
|---|---|---|---|
| 1 | Search + Enter opened a raw fragment | **PASS** | Enter opens the highlighted result ("MI-001" goes to `/team-initiatives/MI-001`). `/search?q=pathways` is a fully styled results page. A one-match query redirects straight through. |
| 2 | Outcome-card placeholders | **PARTIAL** | `updated [date]` is gone. Every card read *`[no owner named] — to be named by Oct 12`*; the square-bracketed italic still read as an unfilled template variable. |
| 3 | Literal `&minus;` | **PASS** | Trade-off lines render a real "−", no overlap; 0 literal entities in the DOM. |
| 4 | Build memo in the Dean's view | **PASS** (residual) | Scope, data-requirements and trade-offs sit in a collapsed `<details>`; closed by default. Residual: "About these figures" stays visible with workbook file names — defensible provenance. |
| 5 | MI-021–029 targets shifted | **PASS** | Each target now matches its own subject. The list, the team page and the MI-021 detail page all agree. The table's row order was still non-numeric here — see N8. |
| 6 | Status vocabulary | **PARTIAL** | A "Milestone states:" key now sits under the header; it lists the five words but defines none, so "CONFIRM" is still unexplained. Target status "source" is still undefined. "Needs update" vs "Need review" still differ. |
| 7 | One name per priority | **PARTIAL** | The new pattern appears on the priority h1, Outcomes, the drawer and MI pages. Short names remained in the Initiatives table, `/checks`, search results and the priority breadcrumb. The fix also introduced a doubled code on MI pages (N3). |
| 8 | Overview shows health | **PARTIAL** | A strip read "22 initiatives tracked: 16 on track · 3 at risk · 1 off track" — those add up to 20; the 2 "Not started" were missing (N4). |
| 9 | Search index and keyboard | **PASS** (functional), a11y gap | MI-001 and the "faculty" MIs are found; arrows move a highlight; Enter follows it. A11y gap: no combobox roles. |
| 10 | Wayfinding | **PASS** | Breadcrumb gutter aligned; MI parent is Team Initiatives; `/teams` returns 200; `aria-current` correct; breadcrumbs added on goal/priority/team/MI pages. |
| 11 | Drawer restyle | **PARTIAL** | The Update button and Feeds badge are styled. But the form behind Update was entirely unstyled (N1). |

**Score: 5 PASS, 5 PARTIAL, 0 FAIL.**

### Bonus: earlier findings now fixed

Milestone counts reconcile; priority-code contrast passes; the Outcomes track is
`#9C9480` (3.02:1); `/checks` uses "covered" chips; the logo has a text
alternative; the goal eyebrow reads "Goal G1"; spelling is US; the shortcut hint
reads "Ctrl/⌘ K".

---

## 2. New or regressed issues

| ID | Severity | Issue | Where |
|---|---|---|---|
| **N1** | **High** | The Update form was entirely browser-default: slider, select, textarea, buttons. The only weekly write path, and the most visibly unfinished surface. |
| **N2** | **High (admin)** | The New initiative form's labels sat beside the wrong fields ("Code [input] Name" wrapped). Default controls. |
| **N3** | Medium | Doubled priority code: "P03 P03 Integrated Portfolio & Pathways". |
| **N4** | Medium | The Overview status strip omitted "Not started", so it did not total the 22 it claimed. |
| **N5** | Medium | Two links ran together in the user menu ("New initiative Switch user"). |
| **N6** | Low | Search rows wrapped awkwardly; the kind label was the raw slug "MAJOR-INITIATIVE". |
| **N7** | Low | The Who-are-you cards look like a system font; the nav marks "Overview" current on `/whoami` and `/search`. |
| **N8** | Low (check) | The MI table was not in ID order — the rows whose targets had been shifted. Source-register order, or an incomplete fix. |

---

## 3. Corrections to the 6 October report

- **Table wrapping was not caused by the viewport.** At 1518 px the MI table still
  wrapped because `main` was capped at **max-width 960 px**, leaving ~560 px of a
  wide screen empty. The effect was real; the "894 px viewport" explanation was
  wrong.
- **Status badges** do not wrap at 1518 px; the pass-1 "At / risk" wrap was a
  narrow-window effect.

---

## 4. Overall read: brand and modernity

**Brand: clearly Georgia Tech.** The app bar is the best thing in the product:
navy, the gold rule, the official logo, Barlow, and a gold current-section
underline. Gold eyebrows, cream filter bands and Plex body text carry it into the
content.

**Modernity: a polished internal tool, not yet a 2026 product.**

- **Layout.** A single 960 px column on a wide screen looks like a document, not a
  dashboard. Nearly half the canvas is blank, and the densest tables are squeezed.
- **Data display.** Health is still mostly text and counts; the status strip was
  the only portfolio-level visual, and it did not total.
- **Finish.** The read-only surfaces are restyled; the **write surfaces** (Update
  form, New initiative form, Who-are-you cards) were still browser defaults — the
  most "prototype" signal left.

**Net.** The Dean-facing read paths are close to demo-ready once N3, N4 and the
bracketed owner line are fixed. The contributor and admin write paths were not
ready yet.

---

## 5. Screenshots

Folder `cll-rereview-screens/`, all at 1518 × 921 (visible viewport only).

| File | Shows |
|---|---|
| 01-app-bar-closeup.png | Logo, gold rule, nav (as Kevin, with Checks) |
| 02-overview-bill.jpg | Overview with the new status strip |
| 03-outcomes-top.jpg | Outcomes cards, milestone-state key, owner line |
| 04-outcomes-memo-collapsed.jpg | Memo collapsed |
| 05a-outcomes-memo-open.jpg / 05b-outcomes-memo-tradeoffs.jpg | Memo open; trade-offs with real "−" |
| 06a-initiative-drawer.jpg / 06b-drawer-update-form.jpg | Restyled drawer; unstyled Update form |
| 07-search-palette-results.jpg | Palette with "faculty" results, second row highlighted |
| 08-team-initiatives-list.jpg | MI table at desktop width (wrapping from the 960 px cap) |
| 09-mi-001-detail.jpg | Breadcrumb fix; doubled "P03 P03" |
| 10-team-learning-experiences.jpg | Breadcrumb aligned; Teams link |
| 11a / 11b / 11c | Kevin: admin nav; New initiative form; /checks |
| 12-priority-p01.jpg | Canonical h1; short-name breadcrumb |
| 13-initiatives-table.jpg | Short priority names; bare % progress |

**Not covered:** dark mode, a real screen reader, and widths below 1024 px after
the window widened.
