# COO Codebase Notes — Day 1 Retrospective

## What Went Well

- **Modular role architecture**: Theorist, Auditor, Bundler, Cartographer, Chronicler as independent modules with clean interfaces. Adding Matrix comms was trivial — drop a file in `skills/comms/`, import where needed.
- **Invariant enforcement in code, not docs**: `check_narrative_bleed()` in bundler.py actually raises `BundleError` on violation. `validate_model_diversity()` in llm_client.py actually checks cross-family at dispatch time. These aren't aspirational — they halt execution.
- **Test-to-code ratio (37%)**: 2,216 LOC tests vs 5,978 LOC production. 208/208 passing. Every phase has integration coverage, not just unit tests. `test_integration_phase2.py` runs the full fetch-extract-audit-bundle pipeline.
- **Injection guard is real security**: 4-layer (preprocess → regex → TF-IDF semantic → halt) with zero external dependencies. Pure stdlib math for cosine similarity. No supply chain risk from sentence-transformers. `attack_vectors.jsonl` is auditable and extensible.
- **Config-driven behavior**: `heartbeat.yaml`, `security.yaml`, role YAML files. Model routing, compression thresholds, jitter ranges — all configurable without code changes.
- **Cost discipline**: $0.003/video at scale. deepseek for extraction (cheap + good at structured output), gemini-flash for audit (free tier, different family). Rate limit fallback built into llm_client.py.

## Technical Debt Accumulated

- **pydantic imported but unused**: In requirements.txt but not referenced in any source file. Safe to remove — zero dependencies on it.
- **openai package unused**: Listed in requirements.txt (legacy from initial scaffold). All LLM calls go through OpenRouter via httpx. Remove to reduce install footprint.
- **Queue processor YAML is not atomic**: `save_queue()` does a full-file rewrite. If process crashes mid-write, queue state is corrupted. Single-threaded supervisor makes this acceptable today, but it's a ticking bomb for concurrent access. Fix: write to `.tmp` then `os.rename()`.
- **Supadata polling is synchronous**: `time.sleep()` loops in a nominally async skill. Works under supervisor but blocks the heartbeat loop during transcript fetch. Not a problem at 5 videos/batch; will bottleneck at 50+.
- **THEORY.md is a placeholder**: Chronicler role contract exists (`roles/chronicler.yaml`, 57 lines) but implementation is missing. Bead compression threshold (25 beads / 750 tokens) is configured but never triggered. Memory will grow unbounded until this ships.
- **models.yaml is a 1-line stub**: Model routing is hardcoded in `llm_client.py`. Config file exists but isn't consumed. Either populate it or remove the file to avoid confusion.
- **No circuit breaker on API calls**: Rate limit handling is `sleep(5)` on 429. No exponential backoff on the API client level (supervisor has it for process restarts, but not for individual API calls). No max retry count — could sleep-loop indefinitely on sustained rate limiting.

## Potential Expansion Ideas

**Easy (current architecture supports directly):**
- Error/crash alerting via Matrix — `send_message()` already works; just call it from supervisor.py and exception handlers
- Bundle content hashing — SHA-256 of markdown content, append to index.jsonl. 5 lines of code.
- Daily summary Matrix message — aggregate from index.jsonl + bead counts. Cron or heartbeat-triggered.
- Health check endpoint — `http.server` on localhost, return JSON status. 20 lines.

**Medium (some refactoring):**
- Concurrent video extraction — `asyncio.gather()` on multiple transcript fetches. Requires making Supadata truly async (it has the `async def` signatures but uses sync `requests` internally).
- Chronicler implementation — clustering signatures by drawer + semantic similarity, then summarizing clusters into THEORY.md. Algorithm is specified in `roles/chronicler.yaml`; needs ~200 LOC implementation.
- Contradiction detection — compare IF-THEN signatures across videos where conditions overlap but actions differ. Would surface ICT teaching evolution over time.

**Hard (significant new work):**
- Vector DB for corpus search — current flat-file approach (JSONL + YAML) won't scale past ~2000 videos. Would need schema design, indexing, query interface.
- Real-time processing — websocket listener for new video notifications, auto-queue, auto-extract. Currently batch-only.
- Developer role (code generation) — generate backtest code from validated signatures. Specified in roadmap but untouched. Requires sandboxed execution environment.

## Performance Observations

- **No bottlenecks at current scale**: 5 videos/batch processes cleanly. Sequential with 5s inter-video delay.
- **Rate limits**: OpenRouter 429 encountered once during Phase 5 testing. 5s sleep resolved it. No sustained throttling observed.
- **Memory**: Bead files small (6.3 KB for full day). Bundle files ~5-15 KB each. Queue YAML is large (11,817 lines for 790 videos) but loads in <1s.
- **yt-dlp**: 300s timeout on cartographer survey is generous. Actual channel enumeration completed in ~45s for 790 videos.
- **LLM latency**: deepseek extraction ~3-8s per chunk. gemini-flash audit ~1-2s per signature batch. Total per-video: ~30-60s depending on transcript length.
- **Scaling concern**: At 100+ videos, sequential processing with 5s delays = 8+ hours. Concurrent extraction would cut this significantly but requires async refactoring.

## Security Observations

- **Injection guard is the strongest component**: 4-layer design with semantic similarity is genuinely robust. The stdlib-only approach (no sentence-transformers) eliminates a major supply chain attack vector.
- **Model diversity is enforced, not just documented**: `validate_model_diversity()` checks at dispatch time. If someone swaps both roles to the same family, it raises `ValueError`.
- **Network isolation is configured but not verified**: `--network none` is in docker-sandbox.sh, but there's no test that confirms the container actually can't reach external hosts. Should add a smoke test.
- **API keys are clean**: All from env vars, none in source, `.env` gitignored and never committed. Good hygiene.
- **Bead chain is an audit trail**: Every extraction, rejection, and heartbeat is recorded with timestamps. Forensic reconstruction is possible. But no integrity verification (no hashing or signing of beads).
- **Concern — no credential rotation reminders**: Keys are set-and-forget. Should add a Matrix reminder every 30/60/90 days.

## Recommendations for Phase 6

1. **Ship Chronicler first** (HIGH): Memory growth is the biggest operational risk. Bead compression + THEORY.md summarization prevents unbounded accumulation. The role contract already specifies the algorithm — it's ~200 LOC of implementation.

2. **Atomic queue writes** (HIGH): Change `save_queue()` to write-tmp-then-rename pattern. 5 lines of code, eliminates corruption risk. Do this before scaling batch size.

3. **Expand Matrix alerting** (MEDIUM): Currently only bundle creation triggers alerts. Add: crash alerts from supervisor.py, error alerts from exception handlers, daily summary digest. The plumbing exists — just wire it.

4. **launchd daemon** (MEDIUM): Replace TMUX + Amphetamine with a proper launchd plist. Makes Mac Mini a true always-on refinery. Eliminates human dependency for restarts.

5. **Remove dead dependencies** (LOW): Drop `pydantic` and `openai` from requirements.txt. Reduces install surface and avoids confusion.

6. **Defer Developer role** (recommendation): Code generation from signatures is exciting but premature. Extraction pipeline needs to stabilize and accumulate 100+ validated signatures before backtest generation adds value. Focus on extraction quality and volume first.
