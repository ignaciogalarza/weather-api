# Skill: Peer Review

## Purpose

Conduct thorough code reviews ensuring all project standards are met before merging changes.

## Triggers

- "Review this PR"
- "Check this code"
- "Peer review the changes"
- "Is this ready to merge?"
- "Review checklist"

## Rules

### Mandatory Checks

All PRs must pass these checks before approval:

#### Code Quality
- [ ] MyPy strict mode passes
- [ ] Ruff check passes (zero errors)
- [ ] No `# type: ignore` without justification
- [ ] No hardcoded secrets or credentials

#### Testing
- [ ] All tests pass
- [ ] Coverage >= 90%
- [ ] New code has corresponding tests
- [ ] Edge cases covered
- [ ] Error scenarios tested

#### Documentation
- [ ] Code comments where logic is complex
- [ ] Docstrings for public functions
- [ ] API docs updated (if endpoint changed)
- [ ] C4 diagrams updated (if architecture changed)
- [ ] ADR created (if decision made)

#### Commits
- [ ] Commit messages follow standard format
- [ ] End-user paragraph present
- [ ] Technical paragraph present
- [ ] Co-author attribution included

#### Deployment
- [ ] Kubernetes manifests updated (if needed)
- [ ] Dockerfile updated (if dependencies changed)
- [ ] No breaking changes without migration plan

### Review Process

```
1. PR Created
   ↓
2. Automated Checks (CI)
   - Tests, Linting, Type checking
   ↓
3. Manual Review
   - Code quality
   - Architecture alignment
   - Security concerns
   ↓
4. Feedback Loop
   - Request changes if needed
   - Re-review after fixes
   ↓
5. Approval & Merge
```

### Review Comments

Use these prefixes for clarity:

| Prefix | Meaning |
|--------|---------|
| `BLOCKER:` | Must fix before merge |
| `SUGGESTION:` | Nice to have, not required |
| `QUESTION:` | Clarification needed |
| `NIT:` | Minor style preference |
| `PRAISE:` | Positive feedback |

## Examples

### Review Comment Examples

```
BLOCKER: This function is missing type annotations. MyPy strict requires
all parameters and return types to be annotated.

SUGGESTION: Consider extracting this logic into a separate function
for better testability.

QUESTION: Why was httpx chosen over aiohttp here? Should we document
this in an ADR?

NIT: Line 45 exceeds 88 characters.

PRAISE: Great error handling! The exception chaining makes debugging
much easier.
```

### PR Approval Template

```markdown
## Review Summary

✅ Code Quality: Passes
✅ Tests: 24 passing, 92% coverage
✅ Documentation: Updated
✅ Commits: Follow standard

**Approved** - Ready to merge.
```

### PR Request Changes Template

```markdown
## Review Summary

✅ Code Quality: Passes
❌ Tests: Missing error case coverage
✅ Documentation: Updated
✅ Commits: Follow standard

**Changes Requested**:
1. Add test for 503 error when weather API fails
2. Coverage currently at 87%, needs to be >= 90%

Please address and re-request review.
```

## Extensions

### Custom Checks

Add project-specific checks:

```markdown
#### Project-Specific
- [ ] WMO codes updated (if weather conditions changed)
- [ ] Rate limiting considered (if new external calls)
- [ ] Caching strategy documented (if applicable)
```

### Automated Review Tools

Integrate with:
- GitHub Actions for CI checks
- Codecov for coverage reports
- SonarQube for code quality metrics
