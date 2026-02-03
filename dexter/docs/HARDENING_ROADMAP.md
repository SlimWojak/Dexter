# DEXTER HARDENING ROADMAP
## From MVP to Production-Grade 24/7 Operation

### Current State (Day 1 MVP)
- Docker isolation: Security sandbox (`--network none`)
- supervisor.py: Crash recovery with exponential backoff (1s base, 2x multiplier, 60s cap)
- TMUX: Manual workaround for session persistence
- Mac sleep prevention: Manual (Amphetamine app)
- Auto-restart: Partial (`--restart unless-stopped` in docker-sandbox.sh)

### Gap Analysis

#### GAP 1: Process Resilience
| Issue | Current | Target |
|-------|---------|--------|
| Script crash | supervisor.py restarts (exponential backoff) | Verified + logged + Matrix alert |
| Container crash | `--restart unless-stopped` flag | Health checks + alerts |
| Mac reboot | Manual restart | launchd plist auto-start on boot |
| Mac sleep | Amphetamine (manual) | pmset / launchd caffeinate |
| TMUX dependency | Manual session creation | Eliminated via daemon mode |

#### GAP 2: Observability
| Issue | Current | Target |
|-------|---------|--------|
| Logs | File-based, per-role loggers (dexter.theorist, etc.) | Structured JSON + rotated |
| Metrics | Per-run cost logging in llm_client.py | Dashboard / daily Matrix summary |
| Alerts | Matrix (new bundles only) | Errors + drift + crash alerts |
| Health | None | Heartbeat ping + status endpoint |
| Bead audit | Append-only JSONL per day | Query interface + archival |

#### GAP 3: Security Hardening
| Issue | Current | Target |
|-------|---------|--------|
| Injection guard | 4-layer active (preprocess, regex, TF-IDF semantic, halt) | Audit + expand attack_vectors.jsonl |
| Credential rotation | Manual | Scheduled reminders via Matrix |
| Network isolation | `--network none` in docker-sandbox.sh | Verify + document + test |
| Audit trail | Git commits + bead chain | Immutable bundle content hashes |
| Model diversity | Cross-family enforced (deepseek/google) | Audit log + drift detection |

#### GAP 4: Data Integrity
| Issue | Current | Target |
|-------|---------|--------|
| Bundle versioning | B-YYYYMMDD-HHMMSS (17 chars, UTC) | + SHA-256 content hash |
| Bead persistence | JSONL files (unbounded growth) | Chronicler compression + backup |
| Queue state | YAML full-file rewrite (no txn safety) | Atomic updates + recovery |
| THEORY.md | Placeholder (Chronicler not implemented) | Scheduled compression every 25 beads |
| Bundle index | Append-only index.jsonl (20 entries) | Rotation + archive policy |

### Hardening Phases (Proposed)

#### Phase H1: Daemon Mode (Priority: HIGH)
- [ ] launchd plist for auto-start on boot (replace TMUX dependency)
- [ ] supervisord integration (complement supervisor.py exponential backoff)
- [ ] `caffeinate -dimsu` or pmset for sleep prevention (replace Amphetamine)
- [ ] Crash alerting to Matrix (not just bundles)
- [ ] Clean shutdown signal handling (SIGTERM → graceful bead flush)

#### Phase H2: Observability (Priority: MEDIUM)
- [ ] Structured logging (JSON format with timestamp, role, level, message)
- [ ] Log rotation (logrotate or Python RotatingFileHandler)
- [ ] Daily summary Matrix message (videos processed, sigs extracted, rejection rate, cost)
- [ ] Error alerting (immediate Matrix push on exceptions)
- [ ] Simple health check endpoint (HTTP ping on localhost)

#### Phase H3: Security Audit (Priority: MEDIUM)
- [ ] Expand attack_vectors.jsonl with Feb 2026 injection patterns
- [ ] Pen-test injection guard with multi-turn and indirect attacks
- [ ] Audit all API key handling paths (env → httpx → OpenRouter)
- [ ] Document network isolation verification procedure
- [ ] Add SHA-256 content hash to every bundle
- [ ] Rate-limit circuit breaker (beyond current 429 → 5s sleep)

#### Phase H4: Recovery & Backup (Priority: LOW)
- [ ] Automated bead backup (daily snapshot to separate volume)
- [ ] Queue state atomic writes (write-tmp + rename pattern)
- [ ] Bundle archive to cloud (optional, sovereign tradeoff)
- [ ] Disaster recovery runbook
- [ ] Chronicler implementation (clustering + archival of beads > 25 per session)

### Quick Wins (Can Do Tomorrow)
1. Verify supervisor.py → Docker integration path end-to-end
2. Add error/crash alerting to Matrix (extend `send_message` usage beyond `send_bundle_alert`)
3. Add `caffeinate -dimsu &` to docker-sandbox.sh startup
4. Document current security posture (network isolation, injection guard, model diversity)
5. Remove unused `pydantic` from requirements.txt (not imported anywhere)
