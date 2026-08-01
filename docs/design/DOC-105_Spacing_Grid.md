# DOC-105 — Spacing & Grid

**Document ID:** DOC-105  
**Title:** Spacing & Grid  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines the spatial system used throughout the ARCHIVE platform.

Every margin, padding, gap, container, grid, and alignment decision must originate from this document.

Consistency of spacing is mandatory.

No arbitrary spacing values may be introduced.

---

# 2. Design Philosophy

Space is not empty.

Space creates rhythm.

Space creates hierarchy.

Space creates elegance.

Generous spacing communicates confidence.

Crowded layouts communicate low quality.

When uncertain, increase whitespace instead of adding visual separators.

---

# 3. Base Unit

The entire spacing system is built on an **8px grid**.

All spacing values must be multiples of this system.

---

# 4. Spacing Scale

| Token | Value |
|--------|------:|
| XS | 4px |
| S | 8px |
| M | 16px |
| L | 24px |
| XL | 32px |
| 2XL | 48px |
| 3XL | 64px |
| 4XL | 96px |
| 5XL | 128px |

No additional spacing values should be introduced unless explicitly documented.

---

# 5. Containers

Maximum Content Width

1440px

Reading Width

760px

Dashboard Width

1600px

Form Width

720px

Authentication Width

480px

Large empty margins are encouraged.

Content should never feel stretched across the screen.

---

# 6. Page Margins

Desktop

64px

Large Desktop

96px

Tablet

32px

Mobile

20px

Margins must remain visually consistent across all pages.

---

# 7. Vertical Rhythm

Sections should breathe.

Recommended spacing:

Between sections

96px

Between large content groups

64px

Between related content

32px

Between closely related controls

16px

Never compress unrelated content.

---

# 8. Grid System

Desktop

12 Columns

Tablet

8 Columns

Mobile

4 Columns

Grid must remain invisible.

Users should feel balance rather than notice alignment.

---

# 9. Grid Gap

Desktop

32px

Tablet

24px

Mobile

16px

Consistent gutters are mandatory.

---

# 10. Cards

Internal Padding

24px

Large Cards

32px

Compact Cards

20px

Cards should never feel cramped.

Content should never touch borders.

---

# 11. Product Grid

Desktop

Prefer 3 columns.

Only use 4 columns on ultra-wide displays.

Tablet

2 columns

Mobile

1–2 columns

Photography must remain dominant.

Do not sacrifice image size to fit more products.

---

# 12. Product Cards

Image

Approximately 75–80% of card height.

Text should occupy significantly less space than imagery.

Avoid dense metadata.

Cards should breathe.

---

# 13. Forms

Space Between Label and Input

8px

Space Between Fields

24px

Space Between Groups

40px

Space Before Primary Action

48px

Long forms should be divided into logical sections.

---

# 14. Dialogs

Internal Padding

32px

Maximum Width

640px

Confirmation Dialog

480px

Dialogs should feel spacious and uncluttered.

---

# 15. Navigation

Header Height

80px

Desktop Navigation Gap

32px

Navigation Items

Minimum Height

40px

Navigation should never appear crowded.

---

# 16. Tables

Cell Padding Vertical

16px

Cell Padding Horizontal

24px

Header Padding

24px

Rows should remain comfortable to scan.

Avoid compressed enterprise-style tables.

---

# 17. Dashboard Layout

Metric Cards Gap

24px

Section Gap

64px

Charts Gap

32px

Dashboard elements should align perfectly.

Numbers require visual breathing room.

---

# 18. Images

Images should dominate available space.

Never shrink imagery simply to display more interface elements.

Allow generous whitespace around photography.

---

# 19. Empty States

Minimum Vertical Padding

96px

Illustrations or icons should never dominate the page.

Whitespace communicates calmness.

---

# 20. Lists

Space Between Items

16px

Grouped Lists

8px

Independent Groups

32px

Maintain consistent rhythm.

---

# 21. Alignment

Everything should align to the grid.

Avoid arbitrary positioning.

Avoid visual corrections unless absolutely necessary.

Alignment should feel architectural.

---

# 22. Responsive Behaviour

Whitespace should decrease gradually.

Never dramatically compress layouts.

The feeling of openness must remain consistent across all screen sizes.

---

# 23. AI Implementation Rules

AI tools must not invent spacing values.

Only spacing tokens defined in this document may be used.

If uncertainty exists, choose the larger spacing value.

Prefer generous spacing over dense layouts.

Never reduce whitespace to fit additional content.

---

# 24. Definition of Success

The interface should feel balanced before users consciously notice the spacing.

Layouts should appear effortless, calm, and architectural.

Users should perceive clarity without being aware of the underlying grid system.