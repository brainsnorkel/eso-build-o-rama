# Accessibility Testing Guide

This guide provides instructions for testing the accessibility features of ESO Build-O-Rama.

## Prerequisites

### Automated Testing Tools
1. **axe DevTools** - Browser extension
   - [Chrome](https://chrome.google.com/webstore/detail/axe-devtools-web-accessib/lhdoppojpmngadmnindnejefpokejbdd)
   - [Firefox](https://addons.mozilla.org/en-US/firefox/addon/axe-devtools/)
   
2. **WAVE** - Web Accessibility Evaluation Tool
   - [Chrome Extension](https://chrome.google.com/webstore/detail/wave-evaluation-tool/jbbplnpkjmmeebjpijfedlgcdilocofh)
   - [Firefox Extension](https://addons.mozilla.org/en-US/firefox/addon/wave-accessibility-tool/)

3. **Lighthouse** - Built into Chrome DevTools
   - Open DevTools (F12) → Lighthouse tab

### Screen Readers
- **Windows**: NVDA (free) - https://www.nvaccess.org/download/
- **macOS**: VoiceOver (built-in) - Cmd+F5 to activate
- **Linux**: Orca (pre-installed on many distros)

## Automated Testing

### Using axe DevTools

1. Generate the site HTML:
   ```bash
   python -m src.eso_build_o_rama.main --trial-id 1
   ```

2. Open a generated page in your browser:
   ```bash
   # Using Python's built-in server
   cd output-dev
   python3 -m http.server 8000
   # Then open http://localhost:8000/index.html
   ```

3. Open browser DevTools (F12)

4. Go to the "axe DevTools" tab

5. Click "Scan ALL of my page"

6. Review results:
   - **0 Violations** = Success! ✅
   - Any violations: Review and fix

### Using WAVE

1. With a page open in your browser

2. Click the WAVE extension icon

3. Review the summary:
   - **Errors**: Critical issues (should be 0)
   - **Contrast Errors**: Color contrast issues (should be 0)
   - **Alerts**: Potential issues to review
   - **Features**: Accessibility features detected
   - **Structural Elements**: Semantic HTML elements
   - **ARIA**: ARIA attributes found

### Using Lighthouse

1. Open Chrome DevTools (F12)

2. Go to "Lighthouse" tab

3. Select:
   - Categories: ✅ Accessibility
   - Device: Desktop (or Mobile)

4. Click "Analyze page load"

5. Target Score: **95+** (ideally 100)

## Manual Keyboard Testing

Test all pages with keyboard only (no mouse):

### Basic Navigation
1. **Tab Key**: Move forward through interactive elements
2. **Shift+Tab**: Move backward through interactive elements
3. **Enter/Space**: Activate links and buttons
4. **Arrow Keys**: Navigate within lists and menus

### Test Checklist

#### Home Page (index.html)
- [ ] Press Tab - Skip link appears and is visible
- [ ] Press Enter on skip link - Jumps to main content
- [ ] Tab through trial cards - All are focusable
- [ ] Focus indicator is visible on each trial card
- [ ] Press Enter on a trial card - Navigates to trial page

#### Trial Page (e.g., rockgrove.html)
- [ ] Tab to breadcrumb links - All are focusable
- [ ] Tab through table rows - Each row is accessible
- [ ] "View Build" links are focusable
- [ ] Focus indicator is clear and visible
- [ ] Press Enter on "View Build" - Navigates to build page

#### Build Page (detailed build view)
- [ ] Tab through breadcrumb navigation
- [ ] Tab through info boxes (Trial & Boss, Model Player, Mundus)
- [ ] Tab through ability icons (if interactive)
- [ ] Tab through gear table cells
- [ ] Tab through "View on ESO Logs" links
- [ ] All focusable elements have visible indicators

### Focus Indicator Verification
The focus indicator should:
- Be **3px solid #38ef7d** (bright green)
- Have **2px offset** from the element
- Be visible against all backgrounds
- Meet **3:1 contrast ratio** minimum

## Screen Reader Testing

### NVDA (Windows)

1. **Install and Start NVDA**:
   ```
   Download from: https://www.nvaccess.org/download/
   Start: Ctrl+Alt+N
   ```

2. **Basic Commands**:
   - `H`: Next heading
   - `Shift+H`: Previous heading
   - `L`: Next link
   - `Shift+L`: Previous link
   - `T`: Next table
   - `Ctrl+Alt+Arrow Keys`: Navigate table cells
   - `D`: Next landmark
   - `Shift+D`: Previous landmark
   - `Insert+F7`: Elements list

3. **Test Scenarios**:

#### Test 1: Skip Link
- Load home page
- Press Tab
- NVDA should announce: "Skip to main content, link"
- Press Enter
- NVDA should announce: "main, region"

#### Test 2: Landmarks
- Press `D` repeatedly
- Should announce: "banner, region" → "main, region" → "contentinfo, region"

#### Test 3: Breadcrumbs
- Navigate to any trial or build page
- Press `D` until you hear "navigation, region, Breadcrumb"
- Press down arrow to hear breadcrumb items
- Last item should have "current page"

#### Test 4: Role Indicators
- Navigate to a trial page
- Press `T` to jump to first table
- Press `Ctrl+Alt+Right Arrow` to move through cells
- First column should announce: "DPS" or "Healer" or "Tank" (not just emoji)

#### Test 5: Image Alt Text
- Navigate to a build page
- Use arrow keys to read ability icons
- Should announce: "[Ability Name] from [Skill Line]"

#### Test 6: Table Navigation
- Press `T` to jump to a table
- NVDA should announce the table caption
- Press `Ctrl+Alt+Down` to enter table
- Press `Ctrl+Alt+Right` to move through columns
- Headers should be announced with each cell

### VoiceOver (macOS)

1. **Activate VoiceOver**:
   ```
   Cmd+F5 (or System Settings → Accessibility → VoiceOver)
   ```

2. **Basic Commands**:
   - `VO` = Control+Option (modifier key)
   - `VO+Right/Left`: Navigate elements
   - `VO+H`: Next heading
   - `VO+Shift+H`: Previous heading
   - `VO+Cmd+H`: Open Heading menu
   - `VO+U`: Open rotor (elements menu)
   - `VO+Space`: Activate element

3. **Test Scenarios**:

#### Test 1: Rotor Navigation
- Press `VO+U` to open rotor
- Use Left/Right arrows to switch between:
  - Landmarks
  - Headings
  - Links
  - Tables
- Verify all major elements are listed

#### Test 2: Table Navigation
- Navigate to a table
- Press `VO+Cmd+C` to read column header
- Move through cells with `VO+Arrow Keys`
- Headers should be read with each cell

## Color Contrast Testing

### Manual Testing

1. **Use Browser DevTools**:
   - Right-click element → Inspect
   - Check computed color values
   - Verify against WCAG standards

2. **WCAG Standards**:
   - **Normal text** (< 18pt): 4.5:1 minimum
   - **Large text** (≥ 18pt or 14pt bold): 3:1 minimum
   - **UI components**: 3:1 minimum
   - **Focus indicators**: 3:1 vs adjacent colors

### Key Color Combinations to Test

| Element | Foreground | Background | Required Ratio |
|---------|-----------|------------|----------------|
| Body text | #e8e8e8 | #1a1a2e | 4.5:1 |
| Headings | #ffffff | #1a1a2e | 4.5:1 |
| Links | #38ef7d | #1a1a2e | 4.5:1 |
| Focus outline | #38ef7d | Various | 3:1 |
| Table headers | #ffffff | #2d1b69 | 4.5:1 |

### Using Contrast Checker

1. Visit: https://webaim.org/resources/contrastchecker/

2. Enter foreground and background colors

3. Check results:
   - ✅ **WCAG AA**: Normal and Large text pass
   - ✅ **WCAG AAA**: Enhanced contrast (bonus)

## Mobile Accessibility Testing

### VoiceOver on iOS

1. **Enable VoiceOver**:
   - Settings → Accessibility → VoiceOver → On
   - Or triple-click Home button (if configured)

2. **Test swipe gestures**:
   - Swipe right: Next element
   - Swipe left: Previous element
   - Double-tap: Activate element
   - Three-finger swipe: Scroll

3. **Verify**:
   - All content is reachable
   - Labels are meaningful
   - Tables are navigable
   - Forms are usable (if any)

### TalkBack on Android

1. **Enable TalkBack**:
   - Settings → Accessibility → TalkBack → On

2. **Test gestures**:
   - Swipe right: Next item
   - Swipe left: Previous item
   - Double-tap: Activate
   - Swipe down then right: Read from top

## Documentation

After testing, document your findings:

### Create Test Report

```markdown
# Accessibility Test Report - [Date]

## Automated Testing
- **axe DevTools**: [X] violations found
- **WAVE**: [X] errors, [X] alerts
- **Lighthouse**: Score [X]/100

## Manual Testing
- **Keyboard Navigation**: ✅ All pages navigable
- **Focus Indicators**: ✅ Visible and meets contrast
- **Screen Reader (NVDA)**: ✅ All content accessible
- **Color Contrast**: ✅ All combinations pass

## Issues Found
1. [Description of issue]
   - **Impact**: High/Medium/Low
   - **WCAG Criterion**: [e.g., 2.4.7 Focus Visible]
   - **Fix**: [Proposed solution]

## Recommendations
- [Any suggestions for improvement]
```

### Update accessibility.md

Add test results to `docs/accessibility.md`:

```markdown
### Testing Results (Last Updated: YYYY-MM-DD)

#### Automated Testing
- axe DevTools: 0 violations
- WAVE: 0 errors, [X] alerts
- Lighthouse: [X]/100 accessibility score

#### Screen Reader Testing
- NVDA + Firefox: Fully accessible
- VoiceOver + Safari: Fully accessible
```

## Continuous Testing

### Before Each Release

1. Run automated tests on sample pages
2. Perform keyboard navigation test
3. Test with at least one screen reader
4. Verify any new features for accessibility
5. Update accessibility documentation

### When Adding Features

- [ ] Keyboard accessible?
- [ ] Screen reader compatible?
- [ ] Proper ARIA labels?
- [ ] Color contrast verified?
- [ ] Focus indicators visible?
- [ ] Semantic HTML used?

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Articles](https://webaim.org/articles/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [axe Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)

## Support

Questions about accessibility testing? Open an issue:
- GitHub: https://github.com/brainsnorkel/eso-build-o-rama/issues
- Label: `accessibility` or `a11y`

