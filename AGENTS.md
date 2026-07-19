# Tomb World Solo Guide

## Project Overview

The Tomb World Solo Guide is a mobile-first web application that assists players in running solo Kill Team games.

The application is intentionally built as a lightweight static web application and is hosted through GitHub Pages.

The project should remain easy to understand, easy to modify, and free from unnecessary complexity.

---

# Repository Structure

Primary files:

- index.html
- app.js
- styles.css
- Assets/

Responsibilities:

index.html
- Application shell
- Screen layout
- Dialog markup
- Script/style references

app.js
- All application logic
- State management
- Dialog flow
- Event handlers
- Game engine

styles.css
- All visual styling
- Mobile responsiveness
- Layout
- Typography

Assets/
- Maps
- Icons
- Images
- Static content

---

# Technology Requirements

This project intentionally uses:

- HTML
- CSS
- Vanilla JavaScript

Do NOT:

- Convert to React
- Convert to Vue
- Convert to Angular
- Convert to TypeScript
- Introduce Node.js
- Introduce build tooling
- Introduce package managers

unless explicitly instructed.

---

# Development Philosophy

Always prefer the smallest reliable change.

Avoid rewriting stable, working code unless it is necessary to implement the requested change or to fix a defect.

Avoid unnecessary refactoring.

Avoid changing architecture.

Preserve existing functionality.

Modify only the files necessary to implement the requested change.
Avoid unrelated edits, formatting changes, or refactoring.

Do not make cosmetic changes unrelated to the requested task.

---

# Mobile First

The application is designed primarily for iPhone users.

Every change must be verified for approximately a 390px viewport.

Requirements:

- No horizontal scrolling
- No clipped dialogs
- No hidden buttons
- No overlapping controls
- Internal dialog scrolling when needed
- Large touch targets
- Responsive layout
- Readable text
- Maintain existing spacing
- Prevent accidental double-tap zoom

Desktop compatibility should be preserved but mobile usability is the priority.

---

# User Interface Standards

Maintain the current visual style.

Reuse existing dialog styles.

Reuse existing buttons.

Reuse existing spacing.

Reuse existing typography.

Do not introduce new UI patterns unless requested.

Do not redesign existing screens.

---

# Application State

Preserve saved game compatibility whenever practical.

Do not rename localStorage keys without implementing a migration.

Do not silently clear user data.

Cancel operations should restore the previous application state whenever possible.

---

# Versioning

Every numbered release MUST:

1. Update every visible version number.

2. Update every internal version constant.

3. Search the repository for stale version numbers.

4. Verify the application displays the new version.

Version consistency is mandatory.

---

# Code Quality

Prefer readable code over clever code.

Reuse helper functions.

Avoid duplicate logic.

Keep functions reasonably small.

Do not introduce unnecessary abstractions.

Comment only when the intent is not obvious.

---

# JavaScript

Before completing any task:

- Check for syntax errors.
- Check browser console errors.
- Ensure event handlers still function.
- Ensure dialogs still open.
- Ensure no JavaScript exceptions occur.

---

# Before Editing

Before modifying code:

1. Understand the existing implementation.

2. Identify every file that requires modification.

3. Explain the implementation plan.

4. Modify only the required files.

---

# Change Safety

Before completing any task, compare your changes against the original code.

Verify:

- No existing functionality was unintentionally removed.
- No unrelated files were modified.
- No unrelated formatting changes were introduced.
- Existing workflows still function.
- The requested feature works.

If any unrelated change is detected, revert it before completing the task.

---

# Engineering Mindset

Optimize for correctness over speed.

Prefer preserving existing behavior.

When multiple implementation approaches are possible:

- choose the least disruptive approach
- minimize code changes
- maximize readability
- preserve backward compatibility

When uncertain, explain the uncertainty instead of making assumptions.

---

# After Editing

Before completing work:

Verify:

- Application loads successfully
- JavaScript has no errors
- All requested functionality works
- Existing functionality still works
- Mobile layout is preserved
- Version number is correct

Review the final diff for unrelated changes.

---

# Release Notes

When completing a versioned release, always provide:

- Version number
- Files modified
- Summary of changes
- Testing performed
- Any remaining risks

---

# Never Do These Things

Do NOT:

- Combine app.js into index.html
- Combine styles.css into index.html
- Rename files unnecessarily
- Change project architecture
- Introduce frameworks
- Introduce dependencies
- Modify unrelated functionality
- Remove existing features unless requested
- Change terminology unless requested
- Change visual styling unless requested

---

# Always Do These Things

Always:

- Preserve GitHub Pages compatibility
- Preserve mobile-first behavior
- Keep changes focused
- Keep code readable
- Maintain existing UX patterns
- Update version numbers
- Review your own changes before finishing

---

# Working Style

For every task:

1. Read the relevant code.

2. Explain the implementation plan.

3. Make the smallest reliable change.

4. Review your own diff.

5. Correct any issues you discover.

6. Summarize exactly what changed.

---

# Project Lessons Learned

This project has several recurring requirements that must always be respected.

## Version Numbers

Version numbers have previously been missed.

Always verify that every displayed version number has been updated before completing work.

---

## Mobile

Never assume desktop behavior is sufficient.

Every feature must work on iPhone-sized screens.

---

## Existing Features

Users value stability over refactoring.

Avoid touching unrelated functionality.

---

## UI Consistency

New dialogs should match the style of existing dialogs.

Do not invent new layouts when an existing one can be reused.

---

## Incremental Development

Prefer many small releases over one large release.

Implement only the requested functionality.

---

## Communication

If a requested implementation could impact existing functionality, explain the potential impact before making the change.

If assumptions are required, clearly state them instead of guessing.

If uncertain, ask for clarification rather than making architectural decisions.

