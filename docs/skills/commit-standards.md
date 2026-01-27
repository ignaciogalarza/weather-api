# Skill: Commit Standards

## Purpose

Ensure all commits follow the project's standardized format with end-user and technical descriptions.

## Triggers

- "Commit these changes"
- "Create a commit"
- "Format commit message"
- "Commit message for..."
- "Stage and commit"

## Rules

### Commit Format

```
<type>: <short description>

<end-user paragraph>

<technical paragraph>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Commit Types

| Type | Use For | Example |
|------|---------|---------|
| `feat` | New features | feat: add weather alerts |
| `fix` | Bug fixes | fix: handle null temperature |
| `docs` | Documentation | docs: add API examples |
| `test` | Test changes | test: add edge case coverage |
| `refactor` | Code restructuring | refactor: extract HTTP client |
| `perf` | Performance | perf: add response caching |
| `chore` | Maintenance | chore: update dependencies |

### Paragraph Requirements

#### End-User Paragraph
- Written for non-technical readers
- Explains what users can do now
- Describes the benefit or change
- No technical jargon

#### Technical Paragraph
- Written for developers
- Describes implementation details
- Lists affected files/modules
- Notes testing approach

### Validation Checklist

- [ ] Type is appropriate for the change
- [ ] Short description is imperative mood
- [ ] Short description under 50 characters
- [ ] End-user paragraph explains value
- [ ] Technical paragraph has implementation details
- [ ] Co-author attribution present

## Examples

### Feature Commit

```bash
git commit -m "$(cat <<'EOF'
feat: add 7-day extended forecast endpoint

Users can now request a week-long weather forecast by calling
GET /forecast/extended/{city}. The response includes daily
high/low temperatures, precipitation probability, and
conditions for the next 7 days.

Adds ExtendedForecastResponse schema with daily breakdown.
Extends weather service with get_extended_forecast() using
Open-Meteo daily forecast API. Includes 12 new tests covering
success, error, and edge cases. Coverage: 94%.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

### Fix Commit

```bash
git commit -m "$(cat <<'EOF'
fix: handle cities with special characters in names

City names with apostrophes, accents, or spaces (e.g., "São Paulo",
"Xi'an", "New York") now work correctly. Previously these would
return a 404 error due to improper URL encoding.

Adds URL encoding in get_coordinates() before calling geocoding API.
Updates tests with parametrized international city names including
UTF-8 characters. All 28 tests passing.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

### Documentation Commit

```bash
git commit -m "$(cat <<'EOF'
docs: add observability implementation plan

Documents the strategy for adding logging, metrics, and tracing
to the Weather API. Includes tooling recommendations and
implementation timeline for production monitoring.

Adds docs/plans/observability.md with detailed research on
OpenTelemetry, Prometheus, and structured logging. Defines
metrics to track (latency, error rates, external API health).
Includes Kubernetes deployment considerations for collectors.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

## Commands

```bash
# Stage specific files
git add src/weather_api/routes/forecast.py tests/test_forecast.py

# Commit with heredoc for multi-line message
git commit -m "$(cat <<'EOF'
<type>: <description>

<end-user paragraph>

<technical paragraph>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"

# Verify commit message
git log -1

# Amend if needed (before push only)
git commit --amend
```

## Extensions

### Commit Hooks

Add pre-commit validation:

```bash
# .git/hooks/commit-msg
#!/bin/bash
if ! grep -q "Co-Authored-By:" "$1"; then
    echo "Error: Missing Co-Authored-By line"
    exit 1
fi
```

### Changelog Generation

Commits following this format enable automatic changelog:

```
## [1.1.0] - 2026-01-28

### Added
- feat: add 7-day extended forecast endpoint

### Fixed
- fix: handle cities with special characters
```
