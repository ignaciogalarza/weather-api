# Skills

Modular skills for Claude Code to assist with this project. Each skill is self-contained and can be extended independently.

## Available Skills

| Skill | Description | File |
|-------|-------------|------|
| Architecture Diagrams | C4 model and sequence diagrams | [architecture-diagrams.md](architecture-diagrams.md) |
| Peer Review | Code review checklist and process | [peer-review.md](peer-review.md) |
| Test Coverage | Ensuring 90%+ coverage | [test-coverage.md](test-coverage.md) |
| Commit Standards | Commit message formatting | [commit-standards.md](commit-standards.md) |
| Deployment | Docker and Kubernetes deployment | [deployment.md](deployment.md) |
| Observability | Logging, metrics, tracing | [observability.md](observability.md) |
| Performance | Benchmarking and optimization | [performance.md](performance.md) |

## Skill Structure

Each skill file follows this format:

```markdown
# Skill: <Name>

## Purpose
What this skill enables.

## Triggers
Commands or phrases that activate this skill.

## Rules
Specific guidelines to follow.

## Examples
Example inputs and outputs.

## Extensions
How to extend this skill.
```

## Adding New Skills

1. Create a new file in `docs/skills/`
2. Follow the skill structure template
3. Add to the skills table in this README
4. Reference in CLAUDE.md if needed
