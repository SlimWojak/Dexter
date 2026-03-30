# CURSOR HANDOFF — Lab Foundation Build
# COO (Claude Code on M3) → Cursor (on playground-dgx)
# Date: 2026-03-30

## What COO Already Completed

All infrastructure scaffolding is done. You are picking up from a clean foundation.

### 1. Directory Structure — DONE
```
~/lab/
├── data/river/          # RiverWriter repo cloned (git pull for updates)
├── data/detections/     # empty — awaiting first detect.py export from M3
├── data/traces/         # empty — awaiting first ARS trace sync from M3
├── constitution/        # 5 methodology docs + ground truth (READ ONLY)
│   ├── vLOCK.yaml
│   ├── STATE_DETECTION_v2.yaml
│   ├── ARS_CANON_v1_3.md
│   ├── calibration_results.yaml
│   ├── HTF_MAP_SPEC_v0_1.yaml
│   └── ground_truth/annotated_trades.yaml
├── tools/               # empty subdirs ready for your builds
│   ├── detect_runner/   backtest/   data_loader/
│   ├── synthetic_gen/   map_replayer/   report_gen/
├── vault/               # Obsidian vault structure
│   ├── hypotheses/   experiments/   findings/
│   ├── dead_ends/    proposals/     weekly_reviews/
├── hermes/              # empty — config/  skills/  context/
├── honcho/              # docker-compose.yml ready (not started)
├── logs/
└── scripts/
    ├── sync_river.sh          # daily RiverWriter pull (cron: 06:30 local)
    ├── sync_constitution.sh   # weekly en1gma doc sync (cron: Sunday 07:00)
    └── health_check.sh        # infrastructure validation
```

### 2. Cron Jobs — DONE
```
30 6 * * *   ~/lab/scripts/sync_river.sh      # daily RiverWriter
0  7 * * 0   ~/lab/scripts/sync_constitution.sh # weekly constitution
```

### 3. Constitution Docs — DONE
Copied from en1gma on M3. These are the Lab's ground truth.
The Lab reads them, never modifies them.

### 4. Qwen/vLLM — ALREADY RUNNING
```
Model:    Qwen/Qwen3.5-35B-A3B-GPTQ-Int4
Endpoint: http://localhost:8000/v1/  (OpenAI-compatible)
Version:  vLLM 0.17.1+cu130
Context:  32K tokens
Features: tool calling, reasoning mode
```
Test: `curl http://localhost:8000/v1/models`

### 5. Honcho Docker Compose — READY (not started)
```
~/lab/honcho/docker-compose.yml
  - postgres:16-alpine on port 5433
  - honcho on port 8001
Start: cd ~/lab/honcho && docker compose up -d
```

### 6. Health Check — DONE
```
bash ~/lab/scripts/health_check.sh
```
Last run: all PASS (vLLM, constitution, ground truth, RiverWriter, vault)

---

## What Cursor Needs To Build

Reference spec: ~/playground/PLAYGROUND_FOUNDATION_SPEC_v0_2.md
(Full design intent — read sections 4, 5, 8, 9 for implementation detail)

### Priority 1: Hermes Agent Setup
- Install Hermes Agent (NousResearch/hermes-agent)
- Configure to use local Qwen at localhost:8000 as backend
- Set up ~/lab/hermes/config.yaml with model routing
- Create ~/lab/CLAUDE.md as the agent orientation file
  (point to constitution, vault, tools, daily rhythm)
- Verify: Hermes starts, can call Qwen, can read files

### Priority 2: Honcho Memory Service
- `cd ~/lab/honcho && docker compose up -d`
- Verify postgres + honcho are healthy
- Wire Honcho into Hermes config (endpoint: http://localhost:8001)
- Create user peer (G) and AI peer (Lab Manager)
- Verify: Hermes can store and recall cross-session memory

### Priority 3: Core Skills
- **detect_runner**: vendor detect.py from en1gma + ra_engine dependencies
  into ~/lab/tools/detect_runner/. Must run independently of en1gma.
  Config: ~/lab/tools/detect_runner/locked_baseline.yaml
  (copy default params from en1gma detection config)
- **data_loader**: parquet reader -> candle DataFrames with TF aggregation
  (RiverWriter stores 1m parquet, Lab needs 5m/15m/1H/4H/D)
- **backtest harness**: walk-forward validation with mandatory train/val split
  Train: 2021-2024, Validate: 2025-current. No override without flag.
- **obsidian_cli**: read/write to ~/lab/vault/ with structured YAML frontmatter

### Priority 4: Frontier Model Wiring
- Factory.ai CLI as Hermes skill (for Opus reviews)
- Anthropic API direct (for overfitting checks)
- OpenAI API (for GPT lateral perspective)
- Perplexity API (for ICT methodology scanning)
- Rule: Qwen does ALL grinding. Frontier models for JUDGMENT only.
- Budget cap: ~$2-5/day in API calls

### Priority 5: Telegram Notification
- Wire Telegram bot for Lab -> en1gma supergroup messages
- Events: morning summary, significant findings, weekly review
- Bot token: same as COO bot or separate Lab bot (ask G)

### Priority 6: Daily Rhythm Automation
- Overnight research loop (22:00-06:00 local): iterate hypotheses
- Morning summary (06:00): synthesize findings -> Telegram
- Afternoon frontier session (14:00-16:00): strategic thinking with Opus/GPT
- Cron or systemd timers for each phase

### Priority 7: Seed Hypotheses
Create 3 YAML files in ~/lab/vault/hypotheses/:
- HYPOTHESIS_001_SILVER_BULLET_MAP_CONFIG.yaml
- HYPOTHESIS_002_MAP_STABILITY_LONG_HORIZON.yaml
- HYPOTHESIS_003_CROSS_PAIR_PRIMITIVE_TRANSFER.yaml
(Content defined in spec section 6b)

---

## Key Invariants (from spec section 10)

- INV-LAB-ISOLATED: Lab cannot access production en1gma or brokers
- INV-NOTHING-CROSSES-WITHOUT-HUMAN: proposals are docs, humans decide
- INV-CONSTITUTION-READ-ONLY: never modify constitution docs
- INV-FITNESS-NOT-PERFORMANCE: measure detection fidelity, not P&L
- INV-WALK-FORWARD-MANDATORY: every quantitative claim needs walk-forward
- INV-NO-PARAM-HUNTING: explore structure, not thresholds
- INV-FRONTIER-FOR-JUDGMENT: Opus/GPT for judgment, Qwen for grinding

---

## Environment Notes

- Platform: DGX Spark (aarch64, NVIDIA GB10, 128GB unified, CUDA 13.0)
- Python: ~/a8ra-inference/bin/python (uv-managed venv, has vLLM + torch)
- Package manager: ~/.local/bin/uv
- Docker: available (v29.1.3 + Compose v5.0.1)
- Disk: 3.2TB free
- Network: Tailscale mesh (playground-dgx, 100.125.254.45)
