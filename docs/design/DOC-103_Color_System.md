# DOC-103 — Color System

**Document ID:** DOC-103  
**Title:** Color System  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines the complete color language of ARCHIVE.

Color is intentionally restrained.

The interface communicates hierarchy through typography, spacing, photography, and composition—not through colorful UI elements.

Every color used throughout the product must originate from this document.

No additional colors may be introduced without updating this specification.

---

# 2. Color Philosophy

ARCHIVE follows a monochrome-first design language.

Color is never decorative.

Color exists only to:

- improve readability
- improve accessibility
- communicate system feedback
- create subtle visual hierarchy

The interface must never feel colorful.

The products themselves provide the visual richness.

---

# 3. Visual Hierarchy

Hierarchy should always be created in the following order:

1. Layout
2. Whitespace
3. Typography
4. Photography
5. Contrast
6. Color

Color is the last tool—not the first.

---

# 4. Primary Palette

## Canvas

```text
#FAFAF8
```

The primary application background.

Almost every page begins from this color.

---

## Surface

```text
#FFFFFF
```

Used only for elevated surfaces.

Examples:

Cards

Dropdowns

Dialogs

Menus

Inputs

---

## Primary Text

```text
#111111
```

Primary reading color.

Maximum contrast.

---

## Secondary Text

```text
#4F4F4F
```

Supporting information.

Descriptions.

Metadata.

---

## Muted Text

```text
#8A8A8A
```

Hints.

Captions.

Disabled metadata.

Empty states.

---

## Disabled

```text
#BEBEBE
```

Disabled controls only.

Never use for normal content.

---

# 5. Neutral Scale

| Token | Color |
|--------|--------|
| Gray 50 | #FAFAF8 |
| Gray 100 | #F4F4F2 |
| Gray 200 | #ECECE8 |
| Gray 300 | #DDDDD8 |
| Gray 400 | #BDBDB8 |
| Gray 500 | #8A8A86 |
| Gray 600 | #6A6A67 |
| Gray 700 | #4D4D4A |
| Gray 800 | #2F2F2D |
| Gray 900 | #111111 |

No other grayscale values should be introduced.

---

# 6. Borders

Borders should almost disappear.

Default Border

```text
#E7E7E3
```

Strong Border

```text
#D6D6D2
```

Focus Border

```text
#111111
```

Borders should never dominate the layout.

---

# 7. Dividers

Dividers exist only to subtly separate content.

Color

```text
#ECECE8
```

If whitespace alone creates sufficient separation, remove the divider.

---

# 8. Background Layers

Application Background

```text
#FAFAF8
```

Section Background

```text
#F4F4F2
```

Elevated Surface

```text
#FFFFFF
```

Overlay

```text
rgba(17,17,17,0.04)
```

Modal Backdrop

```text
rgba(17,17,17,0.45)
```

---

# 9. Buttons

Primary Button

Background

```text
#111111
```

Text

```text
#FFFFFF
```

Hover

```text
#232323
```

Pressed

```text
#000000
```

---

Secondary Button

Background

Transparent

Border

```text
#111111
```

Text

```text
#111111
```

Hover

```text
#F4F4F2
```

---

Ghost Button

Transparent.

No border.

Hover

```text
#F4F4F2
```

---

# 10. Inputs

Background

```text
#FFFFFF
```

Border

```text
#E7E7E3
```

Hover

```text
#D6D6D2
```

Focus

```text
#111111
```

Placeholder

```text
#9A9A95
```

---

# 11. Navigation

Navigation should visually disappear.

Background

Transparent

Hover

```text
#F4F4F2
```

Active Text

```text
#111111
```

Inactive Text

```text
#666666
```

---

# 12. Cards

Cards should feel almost invisible.

Avoid heavy separation.

Prefer:

Whitespace

Photography

Typography

Cards should never look like floating containers.

---

# 13. Shadows

Shadows should be almost imperceptible.

Default

```css
0 2px 12px rgba(0,0,0,0.04)
```

Large

```css
0 10px 30px rgba(0,0,0,0.06)
```

Heavy shadows are prohibited.

---

# 14. Feedback Colors

Feedback colors must remain muted.

## Success

```text
#596B52
```

Muted Olive

---

## Warning

```text
#8B7355
```

Warm Stone

---

## Error

```text
#6C3A3A
```

Muted Burgundy

---

## Information

```text
#4C5D73
```

Muted Slate

---

These colors are reserved exclusively for system feedback.

They must never become part of the brand identity.

---

# 15. Forbidden Colors

The following colors are prohibited for normal interface elements:

Bright Orange

Bright Red

Bright Blue

Bright Green

Bright Purple

Bright Pink

Bright Yellow

Neon colors

Gradient backgrounds

Rainbow palettes

Material Design accent colors

Bootstrap default colors

Tailwind default accent palettes

Crypto-inspired colors

Gaming-inspired colors

---

# 16. Accessibility

Contrast ratios must satisfy WCAG AA at minimum.

Typography must never rely solely on color.

Interactive elements must remain distinguishable without color perception.

---

# 17. Photography Priority

Photography may contain vibrant colors.

The interface must remain visually neutral so that product photography becomes the dominant visual element.

The UI should behave as a gallery wall.

Not as a colorful frame.

---

# 18. Dark Mode

Dark mode is intentionally excluded from Version 1.

All design decisions should optimize for the light theme.

Future dark mode must preserve the same restrained visual language.

---

# 19. AI Implementation Rules

AI tools implementing the interface must not invent new colors.

Only colors defined in this document may be used.

If uncertainty exists, prefer the nearest existing neutral color rather than introducing a new one.

No component may define its own custom palette.

---

# 20. Definition of Success

Users should remember:

the products,

the photography,

the typography,

and the atmosphere.

They should never remember the color palette itself.

Color succeeds when it quietly disappears into the overall experience.