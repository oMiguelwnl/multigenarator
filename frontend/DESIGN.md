# Multilang — Graphite + Blue

## Direction

The user chose a restrained dark interface with graphite and blue (2026-11-11).
The studio prioritizes production, review and recovery. The store will use the
same brand but needs its own presentation and purchasing flows.

Use neutral surfaces, readable supporting text and a single prominent action per
section. Avoid decorative dashboards, invented statistics, heavy gradients and
large promotional blocks in the operational interface.

## Palette

CSS custom properties in `apps/admin/src/styles.css` are the source of truth.

| Role | Token | Color |
| --- | --- | --- |
| Page | `--canvas` | `#101318` |
| Navigation | `--sidebar` | `#0C0F14` |
| Panel | `--surface` | `#171C24` |
| Raised surface | `--surface-raised` | `#1D2430` |
| Primary text | `--text` | `#EEF2F8` |
| Supporting text | `--text-muted` | `#9DAABD` |
| Primary action | `--accent` | `#3568E8` |
| Link/focus/selection text | `--accent-text` | `#98B9FF` |
| Selected surface | `--accent-soft` | `#1B2B48` |
| Completed | `--success` | `#7DD3B0` |
| Needs attention | `--warning` | `#E8BF79` |
| Failed | `--danger` | `#F1A5AC` |

Pair primary blue buttons with white text. Bright accent text is for dark
surfaces. Never reuse button blue for small text on dark surfaces. Status labels
accompany color; color alone must not communicate a required decision. Inputs
have a stronger border than decorative separators. Disabled actions retain
readable labels and explain missing capabilities nearby.

## Typography and layout

- System font stack: Segoe UI Variable, Segoe UI, system-ui, sans-serif. No
  external font requests. A brand font can be evaluated separately.
- Normal interface text: 13–15 px; supporting text: predominantly 12 px.
- Compact metadata: 10–11 px only for short, secondary labels.
- Page titles: 29–34 px; card target word: 41–46 px.
- Buttons have a minimum 44 px height; mobile input text is 16 px.
- Spacing follows a 4 px base, with 16/24/32 px groups.
- Summary metrics use dividers, not three independently elevated cards.
- Preview cards have their own surface and a clear front/back indicator.
- Breakpoints at 1200, 1000 and 680 px preserve reading size. Mobile tables and
  the review item strip can scroll inside their own region.
- Keyboard focus, a skip link and reduced-motion preferences are supported.

## Reference tools

- [Impeccable](https://impeccable.style/docs/impeccable/) is the recommended
  optional design skill for critique and refinement. It is not installed by
  this change; this iteration does not claim an Impeccable audit.
- [Shoogle](https://shoogle.dev/mcp/shoogle-skills) finds shadcn registry
  components; its skill requires its MCP tools. No new component stack added.
- [Lazyweb](https://design.lazyweb.com/mcp) supplies product research through
  its service. No external account or MCP configured.
- [Dribbble](https://dribbble.com/search/language-dashboard) and
  [Dark Design](https://www.dark.design/) are discovery references, not a
  component library or evidence of accessibility/usability.

## Verification boundary

Build and color-pair checks support this iteration. They do not certify the
whole interface against WCAG or replace browser/phone review. Preview text,
production outcomes and audio availability remain demonstrative. Existing
Anki templates, provider behavior and lexical inventories are unchanged.
