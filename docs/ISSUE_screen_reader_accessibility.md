# Screen Reader Accessibility Improvements

## Overview
Implement comprehensive screen reader accessibility improvements to make ESO Build-O-Rama fully accessible to users with visual impairments, following WCAG 2.1 Level AA guidelines.

## Priority: High
Accessibility is a fundamental requirement for inclusive web applications.

## Description

The current site has several accessibility barriers for screen reader users:

### Critical Issues (WCAG Level A)
1. ⚠️ **Missing skip navigation link** - Users must tab through entire header
2. ⚠️ **Emoji role indicators without text alternatives** - ⚔️ ✚ 🛡️ are not announced by screen readers
3. ⚠️ **Missing ARIA landmarks** - No proper semantic navigation structure
4. ⚠️ **CSS-only tooltips** - Not accessible to screen readers
5. ⚠️ **Table headers missing scope attributes** - Complex tables not properly announced

### Important Issues (WCAG Level AA)
6. ⚠️ **Insufficient focus indicators** - May not meet 3:1 contrast ratio
7. ⚠️ **Generic link text** - "View Build →" lacks context
8. ⚠️ **Color contrast issues** - Gradient text colors need verification
9. ⚠️ **Breadcrumb navigation** - Needs proper ARIA structure
10. ⚠️ **Status indicators** - Color-only information

## Proposed Solution

### Phase 1: Base Template (templates/base.html)
- Add skip-to-main-content link
- Implement ARIA landmarks (banner, main, contentinfo)
- Add `.sr-only` utility class
- Enhance focus indicators (3px solid outline with 2px offset)
- Add `.skip-link` styles

### Phase 2: Content Templates
- **home.html**: Add aria-labels to trial card links
- **trial.html**: 
  - Accessible breadcrumb navigation
  - Role indicators with sr-only text
  - Table scope attributes
  - Descriptive link aria-labels
- **build_page.html**:
  - Full breadcrumb trail
  - Proper alt text for ability icons
  - Table captions and scope

### Phase 3: Testing
- Automated: axe-core, WAVE, Lighthouse
- Manual: NVDA (Windows), VoiceOver (macOS)
- Document results in `docs/accessibility.md`

### Phase 4: Documentation
- Create comprehensive `docs/accessibility.md`
- Update `CHANGELOG.md`
- Add accessibility section to `README.md`

## Success Criteria

- [ ] All pages navigable by keyboard alone
- [ ] All interactive elements have visible focus indicators (3:1 contrast)
- [ ] All non-text content has text alternatives
- [ ] All color-based information has non-color alternatives
- [ ] Proper heading hierarchy maintained
- [ ] ARIA landmarks properly implemented
- [ ] Tables have proper headers and scope
- [ ] Links have descriptive text or aria-labels
- [ ] Passes axe-core automated testing (0 violations)
- [ ] Successfully tested with NVDA and VoiceOver
- [ ] WCAG 2.1 Level AA compliant

## Testing Plan

### Automated Testing
```bash
# After generating pages
# 1. Install axe DevTools browser extension
# 2. Open output/index.html in browser
# 3. Run axe scan
# 4. Document violations in docs/accessibility.md
```

### Manual Testing
1. Navigate entire site using only Tab/Shift+Tab
2. Verify all interactive elements reachable
3. Test with NVDA on Windows (or VoiceOver on macOS)
4. Navigate by landmarks (H, L keys in screen readers)
5. Verify table navigation (Ctrl+Alt+Arrow keys)
6. Test breadcrumb navigation
7. Verify all images have meaningful alt text

## Implementation Checklist

- [ ] Add skip link and ARIA landmarks to base.html
- [ ] Implement .sr-only and focus styles
- [ ] Replace emoji-only role indicators with accessible alternatives
- [ ] Add table captions and scope attributes
- [ ] Implement accessible breadcrumb navigation
- [ ] Add aria-labels to generic links
- [ ] Improve alt text for ability icons
- [ ] Replace CSS-only tooltips with ARIA patterns
- [ ] Verify color contrast (4.5:1 for text, 3:1 for large text)
- [ ] Run automated tests (axe-core, WAVE)
- [ ] Perform manual screen reader testing
- [ ] Create docs/accessibility.md
- [ ] Update CHANGELOG.md
- [ ] Update README.md

## Resources

- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Screen Reader Testing](https://webaim.org/articles/screenreader_testing/)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)

## Related Files

- `templates/base.html` - Foundation template with styles
- `templates/home.html` - Home page
- `templates/trial.html` - Trial listing
- `templates/build_page.html` - Build details
- `docs/accessibility.md` - New documentation file

## Labels
`enhancement`, `accessibility`, `a11y`, `screen-reader`, `wcag`

---

**To create this issue on GitHub:**
```bash
# Option 1: Use GitHub CLI
gh issue create --title "Screen Reader Accessibility Improvements" --body-file docs/ISSUE_screen_reader_accessibility.md --label "enhancement,accessibility"

# Option 2: Manually copy content above and paste at:
# https://github.com/brainsnorkel/eso-build-o-rama/issues/new
```

