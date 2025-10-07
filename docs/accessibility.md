# Accessibility Statement

## Overview

ESO Build-O-Rama is committed to providing an accessible experience for all users, including those who use assistive technologies such as screen readers. This document outlines our accessibility features and compliance status.

## WCAG 2.1 Compliance

We strive to meet **WCAG 2.1 Level AA** standards. The following improvements have been implemented to ensure accessibility:

### Keyboard Navigation

- **Skip Navigation Link**: A "Skip to main content" link appears when users navigate with the keyboard (Tab key), allowing them to bypass repetitive header content
- **Focus Indicators**: All interactive elements have visible focus indicators with a 3px solid outline (#38ef7d) and 2px offset
- **Logical Tab Order**: All content follows a logical tab order that matches the visual layout
- **No Keyboard Traps**: Users can navigate through all content using only the keyboard

### Screen Reader Support

#### ARIA Landmarks
- `role="banner"` on the header
- `role="main"` on the main content area with `id="main-content"`
- `role="contentinfo"` on the footer
- `aria-label="Breadcrumb"` on breadcrumb navigation

#### Descriptive Labels
- All links have descriptive text or `aria-label` attributes
- Form elements (if added) use proper `<label>` associations
- Images have meaningful `alt` text
- Decorative images and icons use `aria-hidden="true"`

#### Table Accessibility
- All tables include `<caption>` elements (visually hidden with `.sr-only`)
- Table headers use `scope="col"` attributes
- Role indicators use screen reader text (e.g., "DPS", "Healer", "Tank") alongside visual emojis
- Mobile responsive tables maintain accessibility through `data-label` attributes

#### Breadcrumb Navigation
- Semantic `<nav>` with `aria-label="Breadcrumb"`
- Ordered list structure for breadcrumb items
- `aria-current="page"` on the current page indicator
- Visual separators marked as `aria-hidden="true"`

### Visual Design

#### Color Contrast
- Text colors meet WCAG AA standards (4.5:1 for normal text, 3:1 for large text)
- Focus indicators meet 3:1 contrast ratio against adjacent colors
- Color is not used as the only means of conveying information

#### Responsive Design
- Fully responsive layout works across desktop, tablet, and mobile devices
- Touch targets meet minimum size requirements (44x44px)
- Text can be resized up to 200% without loss of functionality
- No horizontal scrolling required on mobile devices

### Content Structure

#### Semantic HTML
- Proper heading hierarchy (h1 → h2 → h3, etc.)
- Semantic elements used throughout (`<header>`, `<main>`, `<footer>`, `<nav>`, `<table>`)
- Lists use proper `<ul>`, `<ol>`, and `<li>` elements

#### Link Best Practices
- All external links include `rel="noopener noreferrer"` for security
- Link purpose is clear from link text or `aria-label`
- No generic "click here" or "read more" without context

### Testing

This site has been tested with the following tools and assistive technologies:

#### Automated Testing
- **axe DevTools**: Accessibility scanner
- **WAVE**: Web Accessibility Evaluation Tool
- **Lighthouse**: Google's accessibility audit
- **HTML Validator**: W3C Markup Validation Service

#### Screen Reader Testing
- **NVDA** (Windows): Tested with Firefox and Chrome
- **VoiceOver** (macOS): Tested with Safari
- **Browser Testing**: Chrome, Firefox, Safari, Edge

### Known Limitations

1. **CSS-Generated Content**: Some decorative elements use CSS pseudo-elements, which are properly hidden from screen readers
2. **Third-Party Content**: Links to external services (ESO Logs, UESP) may not be fully accessible - we provide clear labeling but cannot control external site accessibility
3. **Icon Images**: Ability icons are images pulled from game data - we provide meaningful alt text including skill line information

### Accessibility Features

#### Screen Reader Only Content
- `.sr-only` utility class hides content visually while keeping it accessible to screen readers
- Used for table captions, role indicators, and other descriptive text

#### Skip Links
- Skip navigation link appears at the top of the page on keyboard focus
- Styled with high contrast (#38ef7d background, #000 text)
- Allows users to jump directly to main content

#### Focus Management
- Enhanced focus indicators with 3px solid outline
- Uses `:focus-visible` to show indicators only for keyboard navigation
- High contrast colors ensure visibility against all backgrounds

### Feedback and Contact

We are committed to continuous improvement of our accessibility features. If you encounter any accessibility barriers or have suggestions for improvement:

- **Report Issues**: [GitHub Issues](https://github.com/brainsnorkel/eso-build-o-rama/issues)
- **Label**: Use the `accessibility` or `a11y` label when reporting accessibility issues
- **Email**: For private accessibility concerns, contact [@brainsnorkel](https://github.com/brainsnorkel)

### Standards and Guidelines

Our accessibility implementation follows these standards:

- [WCAG 2.1 Level AA](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide (APG)](https://www.w3.org/WAI/ARIA/apg/)
- [HTML5 Specification](https://html.spec.whatwg.org/)
- [WebAIM Guidelines](https://webaim.org/)

### Updates and Maintenance

This accessibility statement was last updated: **October 7, 2025**

We regularly review and update our accessibility features as part of our ongoing development process. Major updates are documented in the [CHANGELOG.md](../CHANGELOG.md).

### Third-Party Content

This site uses data from:
- **ESO Logs**: Combat log data (external links provided)
- **Game Icons**: Ability and set icons from ESO game data
- **External References**: UESP, LibSets documentation

We cannot guarantee the accessibility of external websites, but we strive to provide clear context for all external links.

### Technical Implementation

For developers interested in our accessibility implementation:

- **Templates**: Jinja2 templates with ARIA attributes
- **CSS**: Custom focus styles and screen reader utilities
- **Semantic HTML**: Proper landmark roles and heading hierarchy
- **Testing**: Automated and manual testing as part of CI/CD

See our [GitHub repository](https://github.com/brainsnorkel/eso-build-o-rama) for complete source code and implementation details.

---

**Accessibility is an ongoing journey.** We welcome your feedback and are committed to making this site accessible to all users.

