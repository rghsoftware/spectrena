# Spec Backlog

> Ordered list of specs to implement. Use `/spectrena.specify {spec-id}` to start.

## Status Legend

| Emoji | Meaning |
|-------|---------|
| ⬜ | Not started |
| 🟨 | In progress |
| 🟩 | Complete |
| 🚫 | Blocked |

---

## Phase 1: Foundation

### core-001-project-setup

**Scope:** Project structure, build system, tooling configuration

| Attribute | Value |
|-----------|-------|
| **Weight** | STANDARD |
| **Status** | ⬜ |
| **Depends On** | (none) |
| **References** | ARCH §Project Structure |

**Covers:**
- Repository structure
- Build tooling setup
- Development environment

**Does NOT cover:**
- Application implementation
- Database setup

---

### core-002-database-schema

**Scope:** Database schema and migrations setup

| Attribute | Value |
|-----------|-------|
| **Weight** | STANDARD |
| **Status** | ⬜ |
| **Depends On** | core-001 |
| **References** | ARCH §Database, DOM |

**Covers:**
- Schema definition
- Migration tooling
- Seed data

**Does NOT cover:**
- Application queries
- ORM setup

---

## Phase 2: Core Features

### core-003-authentication

**Scope:** User authentication system

| Attribute | Value |
|-----------|-------|
| **Weight** | FORMAL |
| **Status** | ⬜ |
| **Depends On** | core-001 core-002 |
| **References** | REQ §Auth, ARCH §Security |

**Covers:**
- Login/logout flows
- Session management
- Password handling

**Does NOT cover:**
- OAuth providers (separate spec)
- Authorization/permissions

---

<!-- Add more specs following this pattern -->
