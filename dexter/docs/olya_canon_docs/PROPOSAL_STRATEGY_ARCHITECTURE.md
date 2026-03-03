# PROPOSAL: Strategy Architecture for MERIDIAN ZERO

**From:** Olya (CSO)  
**To:** Dexter CTO Team  
**Date:** 2026-02-12  
**Subject:** Standardizing Multiple Strategies Within One Framework

---

## The Problem

We now have two strategies:
1. **ICT Directional Method** — requires daily bias, HTF context, 5-factor checklist
2. **Asia Range Scalp** — no daily bias needed, pure mean reversion

More strategies will come. We need a consistent structure so:
- The team always knows where to find things
- The system can handle any strategy type
- Documentation stays clean and comparable

---

## Proposed Solution: 5-Drawer Framework + Strategy Cartridges

### The Framework (Always Present)

Every strategy uses the same **5 drawers**. The drawers are the "operating system." Strategies are "cartridges" that plug into them.

| Drawer | Purpose | Question It Answers |
|--------|---------|---------------------|
| **Drawer 1: Context** | What do I need to know before the session? | "What's the setup environment?" |
| **Drawer 2: Monitoring** | What am I watching for? | "What should I be tracking?" |
| **Drawer 3: Setup** | What triggers a potential trade? | "Is there a valid setup?" |
| **Drawer 4: Execution** | How do I enter? | "How exactly do I get in?" |
| **Drawer 5: Management** | How do I manage and exit? | "What do I do after entry?" |

### Strategy Cartridges

Each strategy fills out all 5 drawers, but the **content** differs based on what that strategy needs.

---

## Example: Two Strategies Side-by-Side

### ICT Directional (Current v0.3 Method)

| Drawer | Content |
|--------|---------|
| **1: Context** | HTF Order Flow (Weekly → Daily MSS), Three Questions, dealing range, Draw on Liquidity targets |
| **2: Monitoring** | Midnight open, Asia liquidity build, accumulation recognition |
| **3: Setup** | LOKZ manipulation, liquidity sweep, engine event (sweep + MSS + FVG) |
| **4: Execution** | 5-factor checklist, entry types (FVG retrace, OB, sweep-into-PDA), OTE, stop by swing |
| **5: Management** | BE-only trailing, no partials, single target, overnight holds OK, 2 losses = done |

**Requires daily bias:** YES

---

### Asia Range Scalp

| Drawer | Content |
|--------|---------|
| **1: Context** | Asia range measurement (19:00-00:00), validate ≤30 pips, no HTF needed |
| **2: Monitoring** | Sweep window (00:00-04:00), track extensions per direction |
| **3: Setup** | Sweep 1-20 pips + re-acceptance + FVG formation |
| **4: Execution** | Immediate entry at Candle C close, SL at sweep extreme ± 0.5 pip, TP at opposite boundary |
| **5: Management** | Set-and-forget, 1 trade per session max, 1% risk |

**Requires daily bias:** NO

---

## File Structure Proposal

```
OLYA_TRADING_SYSTEM/
├── FRAMEWORK.yaml              # The 5-drawer structure (shared)
├── SHARED_INFRASTRUCTURE.yaml  # Common elements (timezone, risk, etc.)
│
├── strategies/
│   ├── ICT_DIRECTIONAL_v0.3.yaml
│   └── ASIA_RANGE_SCALP_v1.0.yaml
│
└── docs/
    ├── SYNTHETIC_OLYA_METHOD_v0.3.md    # Human-readable ICT method
    └── ASIA_RANGE_SCALP_v1.0.md         # Human-readable Asia scalp
```

---

## Shared Infrastructure (Used by All Strategies)

These elements are consistent across all strategies:

| Element | Value |
|---------|-------|
| Timezone | Always NY Time (UTC-5 winter, UTC-4 summer) |
| Instrument | EURUSD only (for now) |
| Risk per trade | 1% account equity |
| Asia Range window | 19:00-00:00 NY (locked) |
| Asia Range max | 30 pips |
| FVG definition | 3-candle structure, bodies inside = respected |
| Day separator | 17:00 NY |

---

## Benefits of This Approach

1. **Consistency** — Every strategy has the same 5-drawer structure
2. **Clarity** — Team always knows where to look (Drawer 3 = setup logic, etc.)
3. **Scalability** — Adding a new strategy = filling out 5 drawers
4. **Comparison** — Easy to compare strategies side-by-side
5. **Flexibility** — Simple strategies can have simple drawer content; complex strategies can have detailed content

---

## What Changes from Current v0.3

**Nothing breaks.** The current v0.3 content stays exactly the same — we're just reorganizing it into the 5-drawer structure and making room for additional strategies.

Current mapping:
- Phase 1 (Pre-Session) → Drawer 1 (Context)
- Phase 2 (Session Monitoring) → Drawer 2 (Monitoring)  
- Phase 3 (London Manipulation) → Drawer 3 (Setup)
- Phase 4 (Entry Execution) → Drawer 4 (Execution)
- Phase 5 + 6 (Management + Session Close) → Drawer 5 (Management)

---

## Next Steps

1. **Team reviews this proposal**
2. **If approved:** Restructure v0.3 into 5-drawer format
3. **Add Asia Range Scalp** as second cartridge
4. **Create FRAMEWORK.yaml** and **SHARED_INFRASTRUCTURE.yaml**

---

## Questions for Team

1. Does the 5-drawer naming make sense, or prefer "Phase 1-5"?
2. Should we keep strategies in separate files or one combined file?
3. Any concerns about this architecture before we build it?

---

**Awaiting team feedback.**

— Olya
