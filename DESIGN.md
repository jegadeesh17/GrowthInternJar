---
name: Jar Growth Intern Dashboard
description: A Minimal-UI-Kit analytics console rendered in pastels.
colors:
  lav-50: "#F3F1FF"
  lav-100: "#E6E2FD"
  lav-200: "#D5CEFA"
  lav-400: "#A497EE"
  lav-600: "#5B4AC0"
  mint-50: "#E9F7EF"
  mint-100: "#D3EFDF"
  mint-200: "#B9E5CC"
  mint-400: "#86CFA6"
  mint-600: "#23744B"
  butter-50: "#FFF6E1"
  butter-100: "#FDEBC4"
  butter-200: "#FBDEA3"
  butter-400: "#F1C370"
  butter-600: "#80560C"
  peach-50: "#FDEEEA"
  peach-100: "#FADCD4"
  peach-200: "#F6C7BC"
  peach-400: "#EEA090"
  peach-600: "#A8433A"
  sky-50: "#E8F3FB"
  sky-100: "#D2E8F6"
  sky-200: "#B8DBF1"
  sky-400: "#89C0E4"
  sky-600: "#25658C"
  grey-100: "#F9FAFB"
  grey-200: "#F4F6F8"
  grey-300: "#DFE3E8"
  grey-400: "#C4CDD5"
  grey-500: "#919EAB"
  grey-600: "#637381"
  grey-700: "#454F5B"
  grey-800: "#1C252E"
  line: "rgba(145, 158, 171, 0.2)"
  canvas: "#FBFAFE"
  card: "#FFFFFF"
typography:
  display:
    fontFamily: "Barlow, DM Sans, system-ui, sans-serif"
    fontSize: "1.9rem"
    fontWeight: 700
    lineHeight: 1.2
    fontFeature: "tnum"
  headline:
    fontFamily: "Barlow, DM Sans, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  title-head:
    fontFamily: "Barlow, DM Sans, system-ui, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 700
    lineHeight: 1.25
  title:
    fontFamily: "DM Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "1.06rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "DM Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "DM Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1
rounded:
  xs: "6px"
  sm: "10px"
  md: "12px"
  lg: "16px"
  full: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.grey-800}"
    textColor: "{colors.card}"
    rounded: "{rounded.sm}"
    padding: "0 16px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.grey-700}"
  button-soft:
    backgroundColor: "{colors.lav-100}"
    textColor: "{colors.lav-600}"
    rounded: "{rounded.sm}"
    height: "40px"
  button-soft-hover:
    backgroundColor: "{colors.lav-200}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.grey-600}"
    rounded: "{rounded.sm}"
    padding: "0 10px"
    height: "40px"
  nav-item:
    textColor: "{colors.grey-600}"
    rounded: "{rounded.sm}"
    padding: "8px 12px 8px 16px"
    height: "46px"
  nav-item-active:
    backgroundColor: "{colors.lav-50}"
    textColor: "{colors.lav-600}"
  nav-subitem:
    textColor: "{colors.grey-600}"
    rounded: "8px"
    padding: "6px 10px"
    height: "36px"
  nav-subitem-active:
    textColor: "{colors.lav-600}"
  step-button:
    backgroundColor: "{colors.card}"
    textColor: "{colors.grey-600}"
    rounded: "{rounded.sm}"
    size: "36px"
  step-button-active:
    backgroundColor: "{colors.lav-100}"
    textColor: "{colors.lav-600}"
  card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.lg}"
    padding: "24px"
  label-chip:
    backgroundColor: "{colors.grey-200}"
    textColor: "{colors.grey-600}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "0 8px"
    height: "24px"
  label-chip-mint:
    backgroundColor: "{colors.mint-100}"
    textColor: "{colors.mint-600}"
  table-head:
    backgroundColor: "{colors.grey-200}"
    textColor: "{colors.grey-600}"
    padding: "14px 16px"
---

# Design System: Jar Growth Intern Dashboard

## Overview

**Creative North Star: "The Pastel Console"**

A Minimal UI Kit analytics console with the kit's structure intact and its colours swapped for pastels. It has a white left sidebar, a blurred top bar, and white 16px cards on a faintly lavender canvas. The kit's cool grey ramp handles all text and structure. Five pastel hues carry meaning: lavender leads, and mint, butter, peach and sky act as categorical and status roles. Each hue fills surfaces with its light steps, draws chart marks with its 400 step, and sets text with its 600 step.

The density is calm and made for scanning. A reviewer reads the headline numbers first, then the tables. Depth comes from soft ambient shadows, never from borders. Inner dividers are dashed hairlines.

**Key Characteristics:**
- Kit grammar: sidebar with a tinted active pill, sticky blurred top bar, 16px white cards, grey 100–800 ramp.
- Five pastel roles with 50/100/200/400/600 steps: tints fill, 400 marks, 600 speaks.
- Barlow for headline numbers and section titles, DM Sans for everything else, tabular figures in data.
- Dashed hairlines inside cards, and no borders on cards.

## Colors

Soft pastel tints over a cool grey structure, with lavender as the one leading hue.

### Primary
- **Lavender** (`lav-*`): the active nav pill (50 fill, 600 text), links, the soft button, focus ring (400), text selection (200), and the margin line in every chart (600). Lavender is also the default tone for stat widgets and shortcut cards.

### Secondary
- **Mint** (`mint-*`): positive and healthy states, such as order bars, positive margin bars in tables, the "live" period dot, and the healthy-quadrant label chip.
- **Butter** (`butter-*`): targets and caution. It draws the dashed target line and the significant-fluctuation month bands.
- **Peach** (`peach-*`): loss and weakness. It covers loss rows (50, with 100 on hover), negative numbers and bars, and the swing-month markers.
- **Sky** (`sky-*`): neutral volume, such as the category sales bars and the Q1 shortcut card.

### Neutral
- **Grey 800** (ink): headings and body text, and the dark primary button.
- **Grey 600** (ink-2): secondary text, table head text, chart ticks and legends.
- **Grey 700**: long prose and text on tinted impact insets.
- **Grey 200**: the table head band, the code background, the neutral chip and the timeline rail.
- **Grey 100**: the table row hover and the unit-economics tiles.
- **Line** (grey 500 at 20% alpha): every divider, always dashed.
- **Canvas** (near-white lavender): the page behind the cards. The top bar is this colour at 80% alpha.

### Named Rules
**The Ink-on-Tint Rule.** Text on a pastel surface is that hue's 600 step on its 50 or 100 step, a pairing verified at 4.5:1 or better. The 400 step is only for marks (chart fills, dots, list markers, the focus ring) and never for text.

**The Lavender Leads Rule.** Lavender marks selection, links, focus and the primary chart series. The other four hues are roles with meaning, not decoration: mint is healthy, butter is target, peach is loss, and sky is volume.

## Typography

**Display Font:** Barlow (with DM Sans, system-ui)
**Body Font:** DM Sans (with system-ui, Segoe UI, Roboto)
**Mono:** ui-monospace, Cascadia Code, Menlo, Consolas (inline `code` only)

**Character:** Barlow is condensed and sturdy, which makes numbers and section titles feel like instrument readouts. DM Sans is round and quiet, which keeps the dense text friendly.

### Hierarchy
- **Display** (Barlow 700, 1.9rem, 1.2): stat widget values only. Always uses tabular figures.
- **Headline** (Barlow 700, 1.75rem, 1.25, −0.01em): the page title for each section. It drops to 1.45rem at 600px and below.
- **Title-head** (Barlow 700, 1.3rem; shortcut cards 1.45rem): sub-section heads and shortcut-card headlines.
- **Title** (DM Sans 600, 1.06rem, 1.4): card titles. The subtitle under a title is 0.875rem grey 600.
- **Body** (DM Sans 400, 15px, 1.6; 14px at 600px and below): prose is capped at 72–75ch.
- **Label** (DM Sans 700, 0.72–0.75rem): chips and tags. Table heads are 600 weight at 0.82rem, in sentence case.

### Named Rules
**The Barlow-Is-for-Readouts Rule.** Barlow sets only page titles, sub-heads, stat values and shortcut headlines. Card titles, labels and everything interactive use DM Sans.

**The Sentence-Case Rule.** Labels, table heads and chips are never uppercased or letter-spaced.

## Layout

A fixed 280px sidebar sits next to a main column capped at 1240px. The main column is padded 40px, dropping to 24px at 1199px and below and to 16px at 600px and below. Block rhythm inside a section is 24px, and a new sub-section takes a 40px gap. Grids are `auto-fit` with minimum widths of 240px (stats), 280px (thirds) and 440px (halves). They use a 24px gap, or 16px on mobile. The overview uses an 8/4 split that stacks at 899px and below. At 1199px and below the sidebar becomes an off-canvas drawer with a grey-800 scrim at 32% alpha. The top bar is 72px (64px on mobile), sticky, and blurred 6px over canvas at 80% alpha. Tables bleed to the card edges.

## Elevation & Depth

Depth is ambient and layered. Cards float on the canvas with the kit's two-layer shadow: a 2px contact hairline plus a soft 24px drop. Hovering a shortcut card or a part-nav link, or opening the drawer, raises it to the pop shadow. Stat widgets drop the shadow entirely and use a 135° tint gradient from the 50 step to the 100 step, with a white radial glow in the corner. The exact values live in `.impeccable/design.json`.

### Shadow Vocabulary
- **Card** (`0 0 2px 0 rgba(145,158,171,0.2), 0 12px 24px -4px rgba(145,158,171,0.12)`): every card and the period pill.
- **Pop** (`0 0 2px 0 rgba(145,158,171,0.24), -20px 20px 40px -4px rgba(145,158,171,0.24)`): hovered shortcut cards and part-nav links, and the open drawer.
- **Button lift** (`0 8px 16px 0 rgba(28,37,46,0.16)`): hover on the dark primary button only.

### Named Rules
**The No-Border Card Rule.** Cards never carry a border. Separation comes from the card shadow on canvas, and inner division uses dashed `line` hairlines.

## Shapes

Corners are soft and nested. Cards and banners use 16px. Icon tiles and insets use 12px (14px on stat icon tiles). Buttons, nav pills and tooltips use 10px. Chips, tags and code use 6px. Pills and dots are fully round. Chart bars use an 8px radius and doughnut segments 6px. Dividers are always `1px dashed` in the line colour. Icons are 1.8px-stroke outline SVGs with round caps, sized 22px by default.

## Components

### Buttons
- **Shape:** gently rounded (10px), 40px tall, DM Sans 600 at 0.875rem.
- **Primary:** grey-800 fill with white text. On hover it steps to grey 700 and adds the button-lift shadow.
- **Soft:** lavender 100 fill with lavender 600 text, stepping to lavender 200 on hover.
- **Ghost:** transparent with grey 600 text. On hover it takes a grey wash at 12% alpha. It is used for the drawer menu toggle.

### Chips (Labels)
- **Style:** soft labels with no border, 22–24px tall, 6px radius, 700 weight. The neutral chip is grey 600 on grey 200. Tone chips are the hue's 600 on its 100.
- **State:** the nav Q-number chip turns lavender 600 on lavender 200 inside the active pill.

### Cards / Containers
- **Corner Style:** 16px.
- **Background:** white on the canvas.
- **Shadow Strategy:** the card shadow (see Elevation).
- **Border:** none.
- **Internal Padding:** 24px (20px at 600px and below).

### Navigation
The sidebar is white with a dashed right edge. It holds the brand at the top, five vertical tabs, and a gradient PDF card pinned to the bottom. Tabs are 46px tall, 0.9rem 500 weight, and grey 600. On hover they take a grey wash at 8% alpha. The active tab is a lavender-50 pill with lavender-600 text at 600 weight. Switching sections plays a rise-and-fade: 8px up over 0.45s using the ease-out-expo curve.

**Sub-navigation.** A section split into parts (Q1 has three, one per part of the assignment) shows child items under its tab only while that tab is active, including in the mobile drawer. Children are indented under a 2px grey-200 guide line, 36px tall, 0.85rem 500 weight in grey 600, each with a 20px numbered tile (grey 600 on grey 200). The active child turns lavender 600 at 600 weight, its tile lavender 600 on lavender 100, with a 4px lavender-400 marker on the guide line. Children are plain buttons with `aria-current="page"`, not extra tabs. The breadcrumb reads "Dashboard / Section / Part".

### Section Parts
Each part opens with a header: a lavender-600 step line ("Q1 · Part 2 of 3"), the Barlow headline, and one grey-600 line restating what the assignment asks for. A stepper of 36px numbered buttons sits at the right (white with the card shadow; the current one lavender 600 on lavender 100, flat). The part ends with previous/next links: white cards with a grey-600 "Next · Part 3" line over a lavender-600 destination with an arrow. The last part links on to the next question. Only one part is visible at a time, and its charts build when it opens.

### Tables
A grey-200 head band carries sentence-case grey-600 heads with no bottom border. Rows are separated by dashed lines, the row hover is grey 100, and the numeric columns are right-aligned with tabular figures. Loss rows are tinted peach 50. The inline margin bars are 90×6px on a grey-200 track, mint for positive and peach for negative. A verdict column can carry tone chips (mint "Top performer", peach "Underperformer", neutral "Middle").

### Content Cards (Q2 / Q3)
A white card per item: the title first, then a meta row of tone chips under it (category, or priority and effort). Chips never sit above a heading. Body prose is grey 700, capped at 75ch. Visible blocks, in order:
- **Suggested fix** (improvement items): a 12px-radius block with a `1px dashed` line border, a grey-800 0.8rem 600 label, and the numbered fix list in grey 700.
- **Impact inset**: the item hue's 50 tint with a bold 600-step lead ("Estimated impact:" for strengths, "Expected impact:" for improvements, "How it uses Jar's strengths:" for verticals).
- **Expandable detail**: a `<details>` row under a dashed divider with a grey-500 chevron that rotates 180° when open, holding secondary analysis only.

An odd last card in a two-column grid spans both columns.

### Stat Widget (signature)
The kit's AnalyticsWidgetSummary in pastel. It is a 50-to-100 gradient card with no shadow (every 600 text pair on it holds 4.5:1) and a 48px icon tile in white at 70% alpha. It stacks a 600-weight label, a Barlow display value and a small sub line, all in the hue's 600. It has an optional trend readout at the top right and an optional 96×52 sparkline in currentColor, with a dashed target line.

### Charts
Charts use Chart.js themed from the tokens: DM Sans at 12px with grey-600 ticks. Legends sit at the top right as 8px circles. Tooltips are white with a grey-300 border, a 10px radius and 12px padding. Grid lines are 3/3 dashed hairlines in grey 500 at 24% alpha (dashes set by `border.dash`), and axis borders and x-grids are hidden. Series take the 400 fills (bars at 75–80% alpha), with the lavender-600 line for margin and a butter-600 dashed line for targets. Point markers have a 2px white ring.

## Do's and Don'ts

### Do:
- **Do** set text on a pastel tint in that hue's 600 step over its 50 or 100 step.
- **Do** reserve the 400 steps for chart fills, dots, markers and the focus ring.
- **Do** separate content inside cards with `1px dashed` line hairlines, and head tables with the grey-200 band.
- **Do** use tabular figures for every number in stats, tables and tiles.
- **Do** honour `prefers-reduced-motion`. All transitions, animations and chart animation switch off.

### Don't:
- **Don't** put borders on cards. Use the two-layer card shadow.
- **Don't** use saturated or default Chart.js colours. Chart series come from the pastel 400 and 600 steps.
- **Don't** uppercase or letter-space labels, chips or table heads.
- **Don't** set card titles or controls in Barlow. It is only for readouts and section titles.
- **Don't** hide the direct answer to an assignment question inside an expandable section. The suggestion, the reasoning and "how it uses Jar's strengths" stay visible; only supporting analysis collapses.
- **Don't** put a kicker chip or ID label above a heading. Meta chips go under the title.
