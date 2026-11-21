# CarbonTrace AI: Design System

Format follows the awesome-design-md convention so humans and coding agents build the same product.

## Overview

CarbonTrace is an audit-grade carbon ledger. Sustainability analysts upload bills, invoices and
manifests; the product turns them into Scope 1, 2 and 3 emissions with a traceable path back to
the source line. The interface should feel like a careful instrument: quiet surfaces, exact
numbers, and colour spent only on what the data means.

**Key characteristics**
- Mineral, cool neutrals (stone and pine), never cream and never pure black.
- One action colour (pine). Three scope colours, used only to encode scope data.
- One family (Public Sans) with tabular figures on every number.
- The emissions trend chart is the single bold element on the dashboard. Everything around it stays calm.
- System light/dark by default, with a manual override.

## Colors

### Light
| Token | Hex | Use |
|---|---|---|
| `canvas` | #F5F7F6 | Page background |
| `surface` | #FFFFFF | Panels, table rows, sidebar |
| `ink` | #15211D | Headings, numbers, body |
| `ink-2` | #56635E | Secondary text, axis labels |
| `rule` | #DFE5E2 | Hairlines, table dividers |
| `pine` | #17695A | Primary action, selection, focus |
| `pine-wash` | #E3F0EC | Selected nav item, pine tint |

### Dark
| Token | Hex |
|---|---|
| `canvas` | #0E1412 |
| `surface` | #151D1A |
| `ink` | #E4EBE8 |
| `ink-2` | #98A6A0 |
| `rule` | #26302C |
| `pine` | #4DBE9F |
| `pine-wash` | #17302A |

### Scope (data only)
| Scope | Meaning | Light | Dark |
|---|---|---|---|
| Scope 1 | Direct fuel combustion | #B0701C ochre | #D99A45 |
| Scope 2 | Purchased electricity | #3E6FAE grid blue | #7FA6DA |
| Scope 3 | Value chain | #6B8A3A moss | #9DBB67 |

### Status
Verified uses pine, needs review uses ochre text on a pale ochre wash, failed uses #B3261E (dark #F2938C).

## Typography

- Family: **Public Sans** (variable, 400–600). Chosen for its public-sector, compliance vernacular.
- Numbers: `font-variant-numeric: tabular-nums` everywhere numbers align.
- Scale (px): 12 caption, 14 UI, 16 body, 20 section title, 28 page title, 40 headline figure.
- Weights: 400 body, 500 UI and labels, 600 headline figures only.
- Sentence case everywhere. No all-caps labels, no monospace labels.

## Layout

- Desktop-first. Fixed 248px sidebar; main column max 1180px with 32px gutters.
- Spacing base 4px; common steps 8, 12, 16, 24, 32, 48.
- Dashboard order: header (title, period, upload) → trend chart with scope totals as its legend →
  two columns: top sources table, recent documents.
- Under 1024px the sidebar becomes a top bar with a menu button; columns stack.
- Left-aligned text throughout; numbers right-aligned in tables.

## Elevation and shape

- Flat. Surfaces separate by tone and a 1px rule, not shadow.
- Radius: 6px controls, 10px panels, full for status pills and the theme switch.

## Components

- **Buttons:** primary is pine fill with white text; secondary is surface with a rule border.
  Labels are verbs ("Upload documents", "Review item").
- **Nav item:** 36px tall, icon plus label; selected state uses `pine-wash` and pine text.
- **Status pill:** 22px tall, sentence-case label, tinted background with same-family text.
- **Tables:** 44px rows, hairline dividers, numbers right-aligned in tabular figures.
- **Chart:** stacked monthly bars by scope, 2px gap between stacks, tooltip lists all three scopes.

## Motion

Only in response to the user: theme switch cross-fade (150ms), menu open, row hover tint.
`prefers-reduced-motion` disables transitions.

## Accessibility

- Text contrast ≥ 4.5:1 in both themes; scope colours are never the only signal (labels always present).
- Visible focus ring: 2px pine outline with 2px offset.
- All icon-only buttons have an `aria-label`.
