# Contributing to LogLens

Thank you for your interest in contributing to LogLens.

This document outlines the recommended workflow for developing, testing and contributing to the project.

---

# Development Environment

Requirements

- Python 3.11+
- Node.js 20+
- Docker
- Docker Compose

Clone the repository:

```bash
git clone <repository-url>

cd log-lens
```

Start the application:

```bash
docker compose up --build
```

---

# Project Structure

```
backend/
frontend/
docs/
validation/
tests/
```

---

# Branch Naming

Use descriptive branch names.

Examples:

```
feature/security-dashboard

feature/sigma-rules

fix/goaccess-grouping

fix/parser-normalization
```

---

# Coding Standards

Backend

- Follow PEP 8
- Use type hints
- Keep modules focused
- Prefer dependency injection where appropriate

Frontend

- Prefer functional components
- Use TypeScript
- Keep components reusable
- Avoid duplicated logic

---

# Commit Messages

Use conventional commits.

Examples:

```
feat:

fix:

refactor:

docs:

test:

chore:
```

Example:

```
feat(security): add sigma execution diagnostics
```

---

# Pull Requests

Each PR should include:

- Problem statement
- Root cause
- Solution
- Validation performed
- Remaining limitations

Small, focused pull requests are preferred over large unrelated changes.

---

# Testing

Before submitting changes:

Backend:

```bash
pytest
```

Frontend:

```bash
npm run build
```

Docker:

```bash
docker compose up
```

---

# Validation Suite

The repository includes a comprehensive validation suite.

```
validation/
```

Use these datasets to verify:

- Parser detection
- Analytics
- Security detections
- Dashboard metrics
- Diagnostics

Expected behaviour is documented in:

```
validation/expected_results/
```

---

# Sigma Rules

Official rules reside under:

```
backend/rules/sigma/official/
```

Custom organization-specific rules should be placed under:

```
backend/rules/sigma/custom/
```

After adding or removing rules:

1. Reload Sigma
2. Verify diagnostics
3. Validate findings
4. Update documentation if required

---

# Analytics

Analytics should continue using GoAccess as the primary provider.

DuckDB should only be used when:

- GoAccess cannot process the dataset
- Unsupported log formats are uploaded
- Partial analytics are required

Avoid modifying this architecture unless necessary.

---

# Reporting Bugs

Include:

- Log format
- Dataset
- Expected behaviour
- Actual behaviour
- Screenshots
- Backend logs
- Browser console (if applicable)

---

# Documentation

When introducing significant functionality, update:

- README.md
- ARCHITECTURE.md
- validation documentation

Keeping documentation synchronized with implementation is part of every contribution.

---

# Code Review Checklist

Before requesting review:

- Code builds successfully
- Tests pass
- Validation datasets execute correctly
- No unnecessary files are committed
- Documentation is updated
- Feature has been manually verified

---

# License

By contributing to LogLens, you agree that your contributions will be licensed under the project's MIT License.
