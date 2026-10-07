# CLL Initiative Dashboard: Analysis (Hive restyle)

Reviewed 6 October 2026, signed in as **Bill (Dean)**, at http://127.0.0.1:8000. Read-only. I couldn't enlarge the browser window, so the whole review used an **894 × 601 px viewport**. Some of the wrapping and overflow findings will be milder on a wide monitor.

Each finding is marked **[verified]** if I measured it, clicked it, or read it from the DOM, or **[inferred]** if it's a visual judgment.

---

## 1. Summary

This is a strategy-portfolio dashboard for the Dean's weekly leadership meeting. The Hive restyle has noticeably raised its quality. The app bar now reads as Georgia Tech: navy, a gold rule, the official logo and Barlow headings. Several issues from the last review are fixed: the People names now show, the "21 Need review" tile works, the Outcomes progress bars match their numbers, and the drawer now handles keyboard focus correctly. **Overall: promising, but not yet ready to show the Dean.**

**The single biggest issue is the Outcomes page, which is the Dean's own view.** It still shows `Owner: [no owner named] · updated [date]` on all six cards. It prints a literal `&minus;` over its own text. And below the cards it carries an internal planning memo (scope, a 19-row data-requirements table, trade-offs).

**A close second:** pressing Enter in search opens an unstyled raw HTML page.

---

## 2. What works well

- **App bar and brand** (all pages). Navy bar, 2.7 px gold rule (`#B39051`), the GT gold-and-white logo at 90 × 32 px with no distortion, white nav links at 16.8:1 contrast, and a gold underline on the current section. It reads unmistakably as Georgia Tech, not as generic SaaS. [verified]
- **Focus rings adapt to the background** (all pages). Gold on the navy bar, navy on white content, both 2 px. Keyboard users can always see where they are. [verified]
- **"21 Need review" tile** (`/`). It now opens `/team-initiatives?target=needs_review`, which shows exactly 21 rows. The KPI and the list agree. [verified]
- **Initiative drawer** (`/initiatives`). It's a real modal dialog. Focus moves to Close when it opens, Escape closes it, and focus returns to the row you came from. This is textbook behaviour. [verified]
- **Table filters** (`/initiatives`). "At risk" gives "3 of 22 initiatives · filtered" and a "Clear filters" link. Every select has a proper `<label>`. [verified]
- **Outcomes progress bars** (`/outcomes`). The fill now matches the milestone fraction (1/4 = 24.9 %, 2/4 = 49.8 %). [verified]
- **Status badges** (`/initiatives`, `/people`). The word is always present, and every badge passes AA: On track 4.75:1, At risk 4.77:1, Off track 4.79:1, Not started 6.0:1. [verified]
- **Priority page structure** (`/priorities/Identity`). Measure, Target, Cadence and Owner is exactly the right frame for a priority. [verified]
- **Goal cascade** (`/goals/1`). Progress bars with a visible track, plus working group-by. This is the most useful drill-down in the app. [verified]
- **Fonts.** Barlow 600, IBM Plex Sans 400/500/600 and IBM Plex Serif 400 all load, and none fail. [verified]

---

## 3. Findings, ranked by impact

| # | Severity | Finding | Page | What I saw | Why it matters |
|---|---|---|---|---|---|
| 1 | **Critical** | Search + Enter opens a raw, unstyled page | any (⌘K / Ctrl-K) | Typing "Elizabeth" and pressing Enter goes to `/search?q=Elizabeth`: Times New Roman, no header, one bullet reading "person Elizabeth". It's the htmx fragment served as a whole page. [verified] | Enter is the most natural thing to press. In a live meeting it looks like the app crashed. |
| 2 | **Critical** | Placeholder text on every outcome card | `/outcomes` | All six cards end with `Owner: [no owner named] · updated [date]`. [verified] | This is the Dean's own view. Template variables on screen undermine trust in everything else on the page. |
| 3 | **Critical** | Literal `&minus;` printed over the text | `/outcomes`, Trade-offs | The two minus lines show "&minus;" overprinted on "Does not match…" and "Needs about 25…", which makes both unreadable. [verified] | A visible encoding bug on the headline page. |
| 4 | **Critical** | Internal planning memo inside the Dean's view | `/outcomes`, below the cards | "Scope and scale of this choice", "REALISTIC BY OCT 16? Yes if scoped down", a 19-row data-requirements table (A-01…A-19, with whole rows coloured teal, pink or gold), trade-offs, and file names (`Oct16_Wireframe_Data_Lists.xlsx`). [verified] | It reads as the build team's decision memo, not as a dashboard. A presenter would have to explain or scroll past it. |
| 5 | **High** | Targets appear shifted against their titles | `/teams/1`, `/team-initiatives` | MI-021 is "Develop approval/governance process…" but its target is "Approve the faculty governance charter…" (MI-022's subject). MI-023's target is about "one approval process" (MI-021's subject). MI-024's is "Fill 100 % of authorized faculty searches" (MI-025's). MI-027's is enrollment targets (MI-028's). The pattern runs across MI-021 to MI-028. [verified text; cause unknown] | If the register was mis-sorted on import, every target in this block is wrong. **I can't tell if this is an app bug or the source spreadsheet.** Check it against the source. |
| 6 | **High** | Three or more status vocabularies | `/team-initiatives`, `/outcomes`, `/initiatives` | Target status can be "source" (undefined) or "needs review". Milestones show MET, IN PROGRESS, NOT STARTED, **DUE DEC** and **CONFIRM**. The page's own spec (row A-13) says Met/In progress/Not started/**Missed**, and row A-05 says "On track, At risk, **Behind**" where the app says "Off track". The Initiatives filter says "Needs **update** only" while the Overview says "Need **review**". [verified] | Readers can't tell which states are good, bad or pending. "source" and "CONFIRM" will draw a question. |
| 7 | **High** | One priority, several names | `/`, `/priorities/*`, `/initiatives`, search, MI pages | P01 is "One Shared Identity" on the Overview and Outcomes, "Identity (2027)" on its own page (no P01 code), and "Identity" in tables. P03 is "Integrated Portfolio & Pathways" and also "Pathways". Searching "Integrated" returns "P03 Pathways". [verified] | People can't tell they're on the same thing. Leadership vocabulary needs one canonical label. |
| 8 | **High** | The Overview answers "how is it organised", not "how is it going" | `/` | The headline is "How the College's work is organised". Goal and priority cards show only counts ("10 initiatives · 18 Team Initiatives"), with no status mix, bar or colour. The only health signal on the page is the "21 Need review" tile. [verified] | In the first five seconds, Bill can't see whether anything is in trouble. |
| 9 | **High** | Search misses Team Initiatives, and arrow keys do nothing | ⌘K | "MI-001" returns "Nothing matches". "pathways" finds an initiative and a priority, but not MI-001 "Portfolio & pathways". Down-arrow leaves focus in the input with no highlighted result. Clicking a result does navigate correctly. [verified] | 29 Team Initiatives are the core objects and they can't be found. A palette you can't drive by keyboard misses the point of ⌘K. |
| 10 | **High** | Wayfinding is wrong or missing | `/teams/1`, `/team-initiatives/MI-001`, `/goals/1`, `/checks` | The breadcrumb sits at x = 0, touching the window edge, outside the page gutter. On MI-001 it reads "Overview › Priorities › MI-001" (the wrong parent). On teams it reads "Overview › Teams › …", but "Teams" isn't a link, carries `aria-current="page"`, and `/teams` returns **404**. The top nav highlights "Initiatives" on goal, priority, team and MI pages, and "Overview" on `/checks`. Only some pages have breadcrumbs. [verified] | People lose their place, and the wrong item is marked as the current page for screen readers. |
| 11 | **High** | The drawer isn't fully restyled | `/initiatives` drawer | The "Update" button is the browser default (Arial, grey, 2 px outset border). The Feeds line runs together: "D-C Dean C (sample): Consulting arm launch Bill At risk 15%", with the status as loose gold text rather than a badge. [verified] | It's the one surface that still looks unfinished, and the primary action looks like a placeholder. |
| 12 | Medium | Outcome milestone counts don't add up | `/outcomes` | P01 says "1 of 4" but lists 3. P02 says "2 of 5" and lists 3. P05 says "**2** of 4 reached" but shows only **1** MET among the 3 listed. [verified] | Readers will count, and the numbers won't reconcile on the card. |
| 13 | Medium | Low-contrast priority codes | `/` | The P03 code text is 3.34:1, P05 3.59:1 and P06 3.25:1 at 12 px (AA needs 4.5:1). P01, P02 and P04 pass. [verified] | It fails WCAG 1.4.3, and these are the labels people use to talk about priorities. |
| 14 | Medium | Progress track barely visible | `/outcomes` | The unfilled track is `#D8D4C8` on white, 1.48:1 (WCAG 1.4.11 needs 3:1). [verified] | A low-progress bar reads as "a short line", not "a small share of the whole". |
| 15 | Medium | Progress is drawn three different ways | `/initiatives`, `/people/2`, `/checks` | The Initiatives table shows bare "10 %" with no bar. On `/people/2` the track width varies by row (262 px vs 272 px), so the same % draws at different lengths. On `/checks` every bar is full width whether the count is 2 or 10. [verified] | Bars can't be compared across rows, and the `/checks` bars look like quantities when they're really a yes/no. |
| 16 | Medium | Badges and IDs wrap mid-word | `/initiatives`, `/team-initiatives`, `/teams/1` | "At / risk", "Not / started", "ELIZ- / 1", "MI- / 001". The MI table is 869 px in an 839 px box, so the Feeds column is cut off and you have to scroll sideways to see it. [verified at 894 px] | The table looks broken at laptop-split widths. A `white-space: nowrap` on badges and IDs is a one-line fix. |
| 17 | Medium | Priority colours are categorical, not a scale | `/` | Navy, plum, gold, blue, orange, cyan, each shown as a dot (`aria-hidden`) and a coloured top border. P03 gold and P05 orange are close to the At risk amber, and there's no legend. [verified colours; the semantic clash is inferred] | It reads as six unrelated colours, and the warm ones suggest "warning". |
| 18 | Medium | Logo has no text alternative | all pages | The GT logo is a CSS `::before` background image, so assistive tech announces only "Initiative Dashboard" and never "Georgia Tech". [verified] | Screen-reader users miss the institutional identity. |
| 19 | Medium | Mixed type voice | `/`, `/checks` | Page and section headings use Barlow. Card titles, stat numbers, subtitles and the `/checks` headings use IBM Plex Serif, and the priority card titles are underlined. Plex Serif is requested at weight 500 but only 400 loads. [verified] | Three families plus heavy underlines make the cards feel busier than the restyled chrome around them. |
| 20 | Medium | A measure with no current reading | `/priorities/Identity` | The Measure says "% of reviewed public-facing assets aligned…", but no current value, target gap or trend is shown. [verified] | The frame asks "where are we?" and the page doesn't answer. |
| 21 | Low | Dangling separator in the eyebrow | `/goals/1` | The eyebrow reads "GOAL ·" with nothing after the dot (the "G1" code is missing). [verified] | Small, but visible. |
| 22 | Low | Mixed spelling | `/` | "How the College's work is **organised**" vs "**Organizational** layer". [verified] | GT house style is US English. |
| 23 | Low | Mac-only shortcut hint | header | The button says "⌘K" for everyone. Ctrl-K does work on Windows. [verified] | Most GT Windows users won't know to try Ctrl-K. |
| 24 | Low | Filter controls feel dated | `/initiatives` | The filters need an Apply click. The checkbox sits above its label. The Apply button has an odd notched corner. [verified] | Small friction on the most-used table. |
| 25 | Low | Redundant grouping output | `/goals/1`, `/team-initiatives?group=team` | Grouped by owner, each row repeats the owner's name under itself. Grouped by team, the Team column repeats the group header. The "D-1" group header is tiny grey mono text. [verified] | Noise, and an unexplained code. |
| 26 | Low | `/checks` is hidden and says too little | `/checks` | It's reachable only by URL (Bill can see it). It reports "all passing" while Outcomes shows placeholders and the MI targets look shifted (#5). [verified] | A green light that doesn't cover the parts most likely to be wrong. |
| 27 | Low | Thin user menu | header ("Bill") | It opens to blank space and a single "Switch user" link, with no name or role shown. [verified] | Minor, but it looks unfinished. |

---

## 4. Per-lens detail

### 4.1 Visual design and brand

**Does it read as Georgia Tech in 2026?** Mostly yes. The app bar is the strongest part: navy `#051E39`, the gold rule, the logo undistorted at 90 × 32 px, a thin divider, and then "Initiative Dashboard" in Barlow. The gold eyebrows with a short leading rule ("— 2027 STRATEGY PORTFOLIO") and the cream filter band on `/initiatives` carry the brand into the content. With the logo removed it would still feel collegiate, not generic SaaS.

**The app bar:** the logo is visible and correctly sized, and the gold rule is present. [verified] The brand block (logo and title) looks about 10 px higher than the nav links' baseline at this width. [inferred, visual] Nav links pass contrast easily.

**Typography:** the hierarchy is clear at the top (h1 Barlow 28 px, h2 22 px). Below that it splits: card titles, stat numbers and right-hand subtitles switch to IBM Plex Serif, and the `/checks` headings are serif too. Underlined serif titles on the six priority cards are the heaviest element on the Overview. No font failed to load. Small-caps labels at 12 px with letter-spacing are fine on screen but are at the floor for a projector.

**Colour:** navy, gold and cream are coherent and warm. Two places break it:

- The **priority palette** (navy, plum, gold, blue, orange, cyan) is a set of distinct categories, not a scale, and has no legend.
- The **data-requirements table** on `/outcomes` colours whole rows of text teal, pink or gold, which is the most garish thing in the app.

**Spacing and alignment:** cards and tiles are evenly spaced, with consistent radii and borders. The visible misalignments are the breadcrumb at x = 0 (#10) and the `/people/2` bars, which don't share a left edge (#15).

### 4.2 Usability and flow

**First five seconds:** taxonomy, not status (#8). Bill learns there are 22 initiatives, 6 priorities and 4 teams before learning whether anything is wrong. The amber "21" is the only signal.

**Clickability:** stat tiles, goal rows, priority titles, "View cascade →" and team counts are all links, and they show hover and focus states. The "6 Priorities" and "4 Teams" tiles jump to anchors further down the page, which works but is a little surprising. **Dead ends:** `/teams` 404 (#10). On MI-001, the named initiatives ("OMS AI; Digital Credentials…") are plain text, not links.

**Filters and group-by:** the filters on `/initiatives` work (#24 covers the friction). Group-by on `/team-initiatives` and the cascade pages works through query strings (`?group=team`) and is easy to find as chips. It isn't offered on `/initiatives`, the table people will use most.

**Drawer:** it opens, reads cleanly and closes well (see section 2). The content is good: owner, status, %, goals, priorities, Feeds, Latest and Diary. It's let down by the unstyled Update button and the run-on Feeds line (#11).

**Search:** clicking a result navigates correctly (P03 opens `/priorities/Pathways`). Pressing Enter breaks (#1). The index excludes Team Initiatives and arrow keys don't move through results (#9). There are two × controls side by side (clear and close).

**Moments where I had to think:**

- What is "source" target status, and what is "CONFIRM"?
- Why does the nav say "Initiatives" when I'm on a goal page?
- Why does P05 say 2 milestones reached when only one says MET?
- Why do 29 Team Initiatives sit beside 22 Initiatives, when goal counts on the Overview add up to 29 initiatives and priority counts to 25? (Items can carry several tags, but nothing says so.)

### 4.3 Data presentation

- **Progress:** done well on `/goals/1` and `/outcomes`, where the bars are proportionate. Elsewhere it's inconsistent (#15), and the Outcomes track is too faint (#14).
- **Status:** the badge words are always present and pass contrast. There are no icons, though, and some status words appear uncoloured (cascade rows, MI-001 "Not started"). The vocabulary is the real problem (#6).
- **Priority colours:** these are identification colours that look like they ought to mean something (#17). A legend would help, or keep the codes and drop the warm hues.
- **Tables:** headers are clear and none are clipped. IDs and badges wrap (#16). On `/team-initiatives` the long Target text makes each row 6 to 10 lines tall, so only two rows fit on screen. A one-line target with expand-on-click would scan far better.
- **Context and denominators:** the Initiatives table progress has no target date. "Last update: 2 days" is identical on every row, so it doesn't help tell rows apart. The priority Measure has no current value (#20). Outcomes have no prior period ("vs last week").
- **Misleading figures:** the `/checks` coverage bars (#15) and the milestone counts that don't reconcile (#12).

### 4.4 Accessibility (WCAG 2.1 AA, best effort)

| Check | Result |
|---|---|
| Text contrast | Headings 16.8:1. Body and muted text 6.8:1. Badges 4.75 to 6.0:1. The "21" is 5.45:1. The banner text is 4.77:1. **Fails:** P03, P05 and P06 codes at 3.25 to 3.59:1 (#13). The "Owner:" line on outcome cards is 4.65:1 at 12 px, which passes but only just. |
| Non-text contrast | **Fails:** the Outcomes progress track at 1.48:1 (#14). The focus rings are fine. |
| Colour-only meaning | Status always has a word. Priority dots are `aria-hidden` and the code text sits next to them, which is acceptable. The data-requirements table's row colour repeats the "Have it / No" text, which is acceptable but loud. |
| Keyboard | The tab order is: banner close, brand, Search, then nav. I hit no skip link before the nav. Focus is visible on both navy and white. Tiles and table rows are reachable. The drawer traps focus and returns it correctly. The search palette can't be driven with arrow keys (#9). |
| Names and roles | The user menu has `aria-label="User menu for Bill"` and Search has "Search (Command K)", both good. The logo has no text alternative (#18). Progress bars are plain `div`s with no `role="progressbar"` or value, so screen readers get only the adjacent "10 %" text. The breadcrumb `aria-current` is on the wrong item (#10). |
| Screen reader | Not run. These conclusions come from the DOM. |

---

## 5. The top five fixes

1. **Fix search.** Make Enter open the first result (or a fully styled results page), add arrow-key navigation, and index Team Initiatives by ID and name. (#1, #9)
2. **Clean up `/outcomes` for the Dean.** Hide the "Owner · updated" line until there's data, or show "Owner TBC by Oct 12". Fix `&minus;`. Move "Scope and scale", the data-requirements table and the trade-offs to `/checks` or a separate planning page. List every milestone the count refers to. (#2, #3, #4, #12)
3. **One vocabulary.** Give each priority one canonical code and name everywhere (P01 One Shared Identity). Use one status set for milestones and one for targets, and define "source", "CONFIRM" and "Due Dec" in a small legend. Reconcile "Need review" with "Needs update". (#6, #7)
4. **Make the Overview answer "how are we doing?"** Add a status mix (a small stacked bar or counts) to each goal and priority card, and lead with a one-line portfolio health summary above the taxonomy. (#8)
5. **Check MI-021 to MI-028 against the source register.** If the targets really are shifted, a mis-sorted import is a data-integrity bug that no styling can hide. (#5)

Next in line: the wayfinding fixes (#10), restyling the drawer's Update button (#11), and the three contrast failures (#13, #14).
