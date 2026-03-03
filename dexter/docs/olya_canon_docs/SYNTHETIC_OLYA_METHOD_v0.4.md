# Synthetic Olya Method v0.4
## "Does this describe your trading?"

---

**Date:** 2026-02-24  
**Source Taxonomy:** reference_taxonomy_v1.1 (55 concepts)  
**Status:** CLAIM — v0.4 incorporates Volume Imbalance (VI) as equal concept to FVG (Olya decision 2026-02-24)  
**Instrument:** EURUSD (primary only)  
**Changelog:** Volume Imbalance (VI) added as equal concept to FVG. VI = body-to-body gap (wicks may overlap). Both detected and named separately. Both treated identically in all trading logic. Amendments: engine event detection, five-factor checklist, entry types, limit order placement. Zone respect definition generalized to cover both FVG and VI.

---

## How to Read This Document

This is **v0.4** — updated from Olya's decision on 2026-02-24 to add Volume Imbalance (VI) as a concept equal to FVG. VI is a body-to-body three-candle gap (where wicks may overlap), while FVG is the wick-to-wick gap. Both are detected and labeled separately in system outputs but treated identically in all trading logic. This reflects the reality that Interactive Brokers data feeds sometimes produce body-to-body gaps where other brokers show wick-to-wick gaps — both are valid reaction zones.

This document describes the method as Olya actually trades it. v0.3 incorporated her full validation pass (13 corrections). v0.4 adds VI as a first-class concept alongside FVG.

---

## Chart Setup

**Timezone:** Always NY Time. UTC-5 in winter (EST), UTC-4 in summer (EDT during US daylight saving).

**Sessions:**
- **Asia:** 19:00–00:00 NY (locked — not approximate)
- **LOKZ (London Open Kill Zone):** 02:00–05:00 NY
- **NYOKZ (NY Open Kill Zone):** 07:00–10:00 NY

**Highest-probability reversal windows within Kill Zones:**
- London Open: 03:00–04:00 NY
- NY Open: 08:00–09:00 NY

**Reference levels:**
- Each trading day opens at 17:00 NY Time
- Sunday Opening Price: Sunday 17:00 NY, extended to Friday
- NY Midnight Opening Price: 00:00 each day, extended to end of day

**News rules:**
- No entry within 1 hour before high-impact news (red folder events)
- No trading during NYOKZ on CPI or FOMC days
- No trading Thursday and Friday of NFP week

**Bank holidays:** If one market is on holiday, trade the active side's session. Example: USD holiday, EUR active — LOKZ is still valid if the setup is clean.

---

## Layer 0: The Operating System

Before any specific rule or entry technique, there is a framework — an operating system that governs everything. These components are **not equal-weight**. They form a strict hierarchy, where each layer gates the next. If a higher layer says "no," nothing below it matters.

### The Hierarchy

**1. Direction: HTF Order Flow (the primary gate).** Every analysis starts with one question: *Which direction is HTF Order Flow?* Weekly MSS sets the macro direction. Daily MSS confirms the daily intent. Higher Highs and Higher Lows in MSS-defined swings = bullish. Lower Highs and Lower Lows = bearish. Mixed = no trade. **If Order Flow is unclear, you do not trade.** Full stop. No targets, no timing, no execution — nothing below matters until direction is established.

This is expressed through **the Three Questions Protocol**, answered once per day at midnight New York time:
1. **Q1: What is the HTF Order Flow direction?** (Weekly → Daily MSS) — this is the PRIMARY GATE
2. **Q2: What targets exist in that direction?** (Draw on Liquidity) — only relevant after Q1 is answered
3. **Q3: What phase are we in?** (Premium/Discount position, MMXM timing) — refinement for execution

The bias output is **long only**, **short only**, or **none**. There is no "both." If you can't determine a clear direction, you don't trade. The bias is **frozen for the entire day**. No intraday re-biasing. One decision per day.

**2. Targets: IPDA and Draw on Liquidity (subordinate to direction).** Once direction is established, you ask: *Where within that direction is price being delivered?* The Interbank Price Delivery Algorithm (IPDA) delivers price to specific liquidity pools over 20, 40, and 60-day lookback windows. IPDA tells you *where within the direction* — it does not tell you *which direction*. Targets exist within the direction. They are not independent of it.

**Market Maker Models (MMXM)** serve dual roles as both target identification and pattern recognition. As an origin: you trade *away* from the manipulation. As a target: the original MMXM consolidation boundary *is itself* a liquidity pool — you trade *toward* it. Higher timeframe MMXM always overrides lower. MMXM is only valid after the last Daily MSS — each MSS resets the narrative. Timeframe priority: Daily (highest) > H4 (secondary) > H1 (execution only).

**3. Timing: Power of 3 (when within the direction + targets).** Each trading day can follow three phases within one Daily candle: **Accumulation** (positions build around the midnight open), **Manipulation** (price sweeps liquidity against the real direction, typically during LOKZ), and **Distribution** (price expands toward the actual daily target during NYOKZ). This doesn't happen every day — a few times per week — but when it does, it's the structure you trade.

**4. Execution Filter: The 60-Minute Middleman (final gate).** Before dropping to execution timeframes, the 60-minute chart must agree with (or at least not contradict) the anticipated direction. If the 60-minute is totally against your bias, you do not drop to lower timeframes. You wait.

**The key insight:** these are not five equal lenses. They are a cascade. Order Flow gates targets. Targets exist within direction. Timing tells you when to look. The Middleman tells you whether to engage. Start at the top. If the top says no, stop.

---

## Phase 1: Pre-Session Preparation (Before 00:00 NY)

### Weekly Context

Once per week at Sunday 17:00 NY, you evaluate the Weekly chart. The Weekly provides **macro permission only** — it tells you the big-picture direction but is never used for execution, entries, or dealing ranges.

You mark the Previous Week High (PWH), Previous Week Low (PWL), any weekly Fair Value Gaps, and weekly Order Blocks. These become potential targets or boundaries for the week ahead.

The key question: *Is there a Weekly Market Structure Shift?* A valid Weekly MSS requires three things simultaneously: price closes beyond the prior MSS-defined swing, the move shows displacement (forceful, one-sided, no rotation — qualitative, never measured in pips), and a Fair Value Gap is created or respected. If no Weekly MSS exists, the system is in a NO_STRUCTURE state and waits.

### Daily Bias Determination

At midnight New York (00:00), you determine the Daily direction. This is the most important decision of the day, and once made, it does not change until the next midnight.

The Daily MSS follows the same three-component rule as the Weekly: close beyond swing + displacement + FVG. For the very first MSS after a period of no structure, the Previous Day High/Low and Previous Week High/Low serve as initial boundary markers only — a bootstrap to get started. Once the first genuine MSS forms, those initial markers become irrelevant.

You run the Three Questions Protocol in priority order:

1. **Q1: What is the HTF Order Flow direction?** Read Weekly → Daily MSS. Higher Highs + Higher Lows = bullish. Lower Highs + Lower Lows = bearish. Mixed (Higher Highs + Lower Lows) = conflicting — **no trade.** If you cannot answer this question clearly, stop here. Nothing else matters.
2. **Q2: What targets exist in that direction?** Identify the primary Draw on Liquidity — MMXM boundaries, PDH/PDL, PWH/PWL, or undelivered FVGs — but only in the direction established by Q1.
3. **Q3: What phase are we in?** Where is price within the structural range (Premium/Discount)? What is the MMXM timing? This refines entry timing within the established direction and targets.

The output is your bias: **long only**, **short only**, or **none**. If Order Flow is unclear, no Daily MSS exists, no dealing range can be defined, or no clear Draw on Liquidity target exists in the direction — you do not trade.

### Dealing Range

The structural range within which you operate. The dealing range is defined from MSS boundaries — never from arbitrary time windows or recent bar highs/lows.

Boundary priority (highest quality first):
1. Equal Highs/Lows (these are liquidity pools — the strongest boundaries)
2. External levels like PDH/PDL/PWH/PWL (institutional reference levels)
3. MSS Swings (the pivots created by Market Structure Shifts)
4. Validated Swings (local pivots where price reacted with immediate displacement)

Previous Day High and Low are measured by **wicks only** (not closes) on the **17:00 NY forex day** (not midnight). Liquidity sits at wick extremes, not at closing prices.

The midpoint of the dealing range — Equilibrium — is a decision threshold. In Discount (below 50%), you look for longs. In Premium (above 50%), you look for shorts. At Equilibrium, you *can* still enter if all 5 factors are present and the setup is clean — but probability is lower, so you need full confluence. Equilibrium is not an automatic no-trade; it's a higher bar.

### Draw on Liquidity Targets

In the direction of your bias, identify what price is being delivered *toward*:

1. **MMXM Boundary** (highest priority) — the original consolidation boundary of a Market Maker manipulation
2. **Previous Day High/Low** — the nearest daily liquidity pool
3. **Previous Week High/Low** — the nearest weekly liquidity pool
4. **Undelivered Daily/Weekly FVGs** — imbalances the algorithm hasn't yet rebalanced

Not all targets are equal. A target that has **never been touched** (NOT_DELIVERED) is highest quality. A target that has been approached but produced no structural consequence (LIQUIDITY_RUN) is still valid. A target where a consequence has already occurred — displacement, MSS, or FVG formed at that level — is **invalid**. The job was done. Cross it off.

### Asia Range Filter

Check the Asia Range (19:00–00:00 NY — locked, not approximate). The range must be under 30 pips for a clean LOKZ setup. If Asia Range exceeds 30 pips, skip the LOKZ model — the market has already expanded during quiet time and the manipulation phase won't behave predictably.

### HTF Alignment Check

Verify alignment across timeframes:

- **Full alignment** (Weekly + Daily + H4 all agree): Full conviction. Full risk. Target can extend to external liquidity.
- **Partial alignment** (Daily clear but against Weekly, or H4 not confirming): Scalps only. Target stays at nearest internal liquidity.
- **Misalignment** (Weekly and Daily disagree): You can still take scalps on lower execution timeframes. Risk stays at 1%.

You trade with a fixed 1% risk regardless of alignment level. What changes with alignment is not *how much* you risk, but *what kind* of setup you take and *how far* your target extends.

### Middleman Gate

Before dropping to lower timeframes for execution, check the 60-minute chart.

**Green light:** 60min supports or is neutral to anticipated direction. Proceed to LTF.  
**Red light:** 60min totally against direction. Do **not** drop to lower timeframes. Wait.  
**Scalp exception:** 60min must be at minimum neutral (not supportive, just not against).

A common mistake: the 2-minute or 5-minute chart looks perfect, but the 60-minute is retracing sharply against your direction. Do not enter. Wait for the 60-minute imbalance to fill, then re-evaluate.

### Post-Expansion Shift

If the daily objective has been **delivered with displacement** — an impulsive move to the target, not a slow grind — the system shifts from Daily range analysis to H4/H1 **rebalance mode**. The expansion is done. Now look for rebalancing setups within the H4/H1 timeframes. This shift persists until a new Daily MSS forms.

In rebalance mode, the same 5-factor checklist applies — sweep + PDA + MSS + OTE + LTF confirmation — but applied to H4/H1 timeframes rather than Daily. The rules don't change. The timeframe does.

---

## Phase 2: Session Monitoring (00:00 – 02:00 NY)

### Midnight Open

At 00:00 NY, record the opening price. Draw a horizontal line extending to the end of the day. This is your intraday anchor — the center point of the Power of 3 accumulation.

The midnight open provides a directional filter:
- During London, **bearish opportunities** tend to form above the midnight open line (price sweeps up, then reverses down)
- **Bullish opportunities** tend to form below it (price sweeps down, then reverses up)

This is a guide, not an absolute rule. Sometimes price explodes immediately after a tiny sweep. But as a filter, it's reliable.

### Asia Liquidity Build

The Asia session (19:00–00:00 NY) builds the liquidity pools that London will target. Mark the Asia session high and low. These are the pools the manipulation phase will sweep.

No core model execution happens during this period. You are observing, not trading.

The Asia range must be under 30 pips — the market should be coiled, ready for the next directional move. A wide Asia range (30+ pips) already consumed some of the day's movement and means you skip the LOKZ model.

### Accumulation Recognition

This is Power of 3, Phase 1. Price consolidates around the midnight open price. Positions are building. The range is small.

**Do not enter during accumulation.** It's too early. The manipulation hasn't happened yet, and entering before the sweep means you're likely to get stopped out by the very move you're waiting for.

---

## Phase 3: London Manipulation (02:00 – 05:00 NY)

### London Open Killzone (LOKZ)

02:00 to 05:00 NY, with the highest-probability reversal window at 03:00–04:00 NY. This is where the daily trading thesis is tested. The institutional algorithm sweeps the liquidity pools built during Asia, sets the High of Day or Low of Day, and then reverses toward the daily objective.

On a bearish day: price pushes **up** during London, sweeps the Asia high (and potentially PDH), then reverses **down**. The London high becomes the HOD.

On a bullish day: price pushes **down** during London, sweeps the Asia low (and potentially PDL), then reverses **up**. The London low becomes the LOD.

### Liquidity Sweep

The manipulation move against the anticipated direction — also known as a Judas Swing. These are the same concept: the false move that sweeps liquidity before the real move begins.

The sweep should not exceed 30–40 pips. Beyond that, it's becoming the trend, not a sweep.

Price trades beyond a named level — the Asia high or low, the Previous Day high or low, equal highs/lows, a recent swing point — then closes back inside the range. The breach triggers stop-loss orders (the liquidity). The close back inside shows rejection. Stops were hit. The institutional order flow can now proceed.

A sweep alone is not a Market Structure Shift. It's just a sweep. MSS requires what happens *after* the sweep: displacement and a Fair Value Gap.

### Engine Event

This is the composite event that enables entry. **All three components must fire simultaneously:**

1. **Liquidity Sweep** — price breaches a named liquidity pool and returns
2. **Market Structure Shift with Displacement** — price closes beyond the prior MSS-defined swing with a forceful, one-sided move that leaves no room for debate. Displacement is qualitative: forceful exit from a level, existing structure removed, imbalance left behind, one-sided (no rotating consolidation), and no significant rotation afterward
3. **Imbalance (FVG or VI)** — one of the following:
 - **Fair Value Gap (FVG):** a three-candle wick-to-wick imbalance where Candle A wick high doesn't overlap Candle C wick low (bullish), or Candle A wick low doesn't overlap Candle C wick high (bearish)
 - **Volume Imbalance (VI):** a three-candle body-to-body imbalance where Candle A body top doesn't overlap Candle C body bottom (bullish), or Candle A body bottom doesn't overlap Candle C body top (bearish). Wicks may overlap.

FVG and VI are detected and labeled separately in system outputs but **treated identically in all trading logic**. Why both exist: Interactive Brokers data feeds sometimes produce body-to-body gaps (VI) where other brokers show wick-to-wick gaps (FVG). Both are valid reaction zones.

Note on zone respect (applies equally to FVG and VI): the MSS condition requires an FVG or VI "created OR respected." A *respected* zone means candle **bodies** stay inside the zone boundaries — wicks can breach the zone, but bodies must remain within.

**If any of the three is missing, there is no valid setup. Wait.**

---

## Phase 4: Entry Execution (When the Engine Fires)

### The Five-Factor Checklist

All five factors are required. **No exceptions. Skip if any factor is missing.**

1. **Liquidity swept** — Asia range, PDH/PDL, or a swing point has been taken
2. **PDA engaged** — Order Block, FVG, VI, or Breaker is present in the correct zone (Discount for longs, Premium for shorts)
3. **MSS confirmed** — with displacement and an FVG or VI
4. **OTE zone reached** — price has retraced 61.8% to 79% of the dealing range or recent expansion
5. **LTF PDA available** — a 5-minute Order Block, FVG, or VI exists for precise entry

If you have four out of five, you don't have a trade. This is not discretionary. The 5-factor checklist IS the confluence system — all five present means trade, any missing means no trade. No numeric scoring. Binary.

### Entry Types

**FVG Retrace Entry:** After displacement creates a Fair Value Gap, price retraces into it. Enter at the FVG boundary or at Consequent Encroachment (the 50% midpoint of the FVG). The FVG should be in Discount for longs or Premium for shorts, and within the OTE zone. Fresh (untouched) FVGs are preferred.

**VI Retrace Entry:** After displacement creates a Volume Imbalance, price retraces into it. Enter at the VI body boundary or at Consequent Encroachment (the 50% midpoint of the VI). The VI should be in Discount for longs or Premium for shorts, and within the OTE zone. Fresh (untouched) VIs are preferred. Treated identically to FVG retrace in all logic.

**Order Block Entry:** Price retraces to an Order Block. Enter at the body edge (conservative) or the Mean Threshold at 50% (aggressive). A high-quality Order Block has a big body, fast move away from it, and a coupled FVG. Mark bodies only — not wicks.

**Sweep-into-PDA Entry:** A liquidity sweep drives price into a PDA where the Engine Event confirms. You've been watching the liquidity pool. Price sweeps it. The sweep pushes price into a PDA. MSS and displacement confirm there. Enter. Kill zone timing adds priority.

### OTE Confirmation

The Optimal Trade Entry zone sits at the 61.8% to 79% Fibonacci retracement of the expansion or dealing range. Apply the Fibonacci tool from body low to body high of the expansion (or from Order Block high to wick top). Your entry should fall within this zone for the highest probability.

### Position Sizing

**Fixed 1% of account equity per trade. Always. No grading.** The system calculates lot size automatically based on stop distance. One setup, one size, one outcome.

### Stop Loss Placement

Stop loss is placed by **swings, not by pips**. Place the stop beyond the swing that provided the liquidity.

For longs: below the swing low that provided the liquidity.  
For shorts: above the swing high that provided the liquidity.

This usually lines up around 8–12 pips, but the swing is what determines placement — not an arbitrary pip count.

---

## Phase 5: Trade Management (Post-Entry)

### After Entry: Set and Forget

This is where your method diverges most from standard Blessed Trader teaching. Five overrides define your management approach, and each exists for the same reason: **eliminate mid-trade decisions**.

**Breakeven-only trailing.** When price makes a 15-minute swing break in the trade direction (or moves approximately 1R in your favor), move the stop loss to entry price. That is the only adjustment. No further trailing. The trade either hits target or comes back to breakeven.

**No partial exits.** Full exit at a single target. The position is on or off. No mid-trade decisions about how much to keep on.

**No re-entry.** One attempt per narrative. If stopped out, that narrative is done. The only exception: a completely new MSS creates a genuinely new narrative — not a retry of the same idea. This prevents revenge trading and overtrading.

**No position scaling.** Single entry, single exit. No adding to winners. No adding to losers. Full position at entry. One price, one size, one outcome.

These four overrides, combined with fixed 1% risk, create a binary outcome model: you win your target or you lose 1%. There is nothing in between. This is intentional. The method removes every possible mid-trade decision point, leaving only the pre-trade analysis and entry.

### Take Profit Targets

Where you exit depends on what's available and how strongly aligned the higher timeframes are.

Target hierarchy (nearest to farthest):
1. Nearest internal liquidity (session highs/lows within the dealing range)
2. Previous Day High/Low
3. 20-day IPDA levels
4. External liquidity (major swing points, PWH/PWL)

With full HTF alignment — Weekly, Daily, and H4 all agreeing — the single target can extend to external liquidity. Without full alignment, the target stays at the nearest internal level.

There are no "runners" in the traditional sense. What changes with alignment is *how far* the single target extends, not whether a portion of the position stays on. Partial alignment = internal target. Full alignment = external target. Still one entry, one exit, no partials.

### Overnight Holds

Positions can run overnight if structure is still intact — meaning no MSS has formed against the position and the original thesis remains valid.

---

## Phase 6: Session Close & Review

### No New Entries After NYOKZ

No new entries after NYOKZ is over (10:00 NY). Open positions can continue to run if structure is intact.

### Daily Loss Limit

**2 losses = done for the day.** Not percentage-based. If you get stopped out twice, you stop trading. This prevents emotional spiraling and revenge trading.

### Counter-Trend Risk Reduction

When alignment is imperfect, the default response is to **wait**, not to trade defensively. Counter-trend trades are rare.

- **Against the Daily direction:** Rarely taken. If taken at all: scalp only, same 1% risk, internal liquidity target only. Usually you just skip and wait for alignment to return.
- **Against the 60-minute:** Do not enter at all (scalp exception: 60min must be at minimum neutral).
- **No clear HTF direction:** No trade. Wait for clarity.

### Friday

Trade normally, but expect profit-taking behavior from the market. You're more likely to take profits at internal liquidity rather than holding for external targets. Stop trading by noon NY — Friday afternoon is unreliable.

### Instrument

EURUSD only for now. Pair expansion comes after the system is validated on a single instrument.

---

## Appendix A: Olya's Overrides

| What Blessed Teaches | What You Do | Why |
|---|---|---|
| Tiered risk: 1% / 0.5% / 0.25% based on context quality | Fixed 1% always | Remove sizing decisions. One setup, one size. |
| 50% off at TP1, 50% at TP2 | Full exit at single target | No mid-trade decisions. On or off. |
| Re-enter at next OTE if thesis intact | One attempt per narrative | Prevent revenge trading and overtrading. |
| Add to winners at key levels | Single entry, single exit | Full position at entry. Simplicity. |
| Progressive trailing with structure | Breakeven-only | Set and forget after BE trigger. |
| Fixed 10 pip stop with buffer logic | Stop beyond the swing that provided liquidity | Structure-based, not arbitrary. Usually 8–12 pips anyway. |
| 15 min time stop for scalps | No time stops | Let the trade work. Structure tells you when it's done. |
| CBDR 14:00–20:00 with SD box extensions | No CBDR — only Asia Range (19:00–00:00, max 30 pips) | Simplified filter. Asia Range is what matters. |
| SMT as confirmation tool | SMT removed for now | Simplify. May add back after core method validated. |

**The common thread:** every override removes a decision point. The method front-loads all decisions to the pre-trade analysis and entry. Once in the trade, there is nothing to decide except whether the target or the stop is hit.

---

## Appendix B: Concept Coverage Status

### Resolved in v0.4 (VI Amendment — Olya Decision 2026-02-24)

| Area | Resolution |
|---|---|
| Volume Imbalance vs FVG | VI (body-to-body gap) added as equal concept to FVG (wick-to-wick gap). Both detected and named separately. Both treated identically in all trading logic. |
| FVG respect definition | Generalized to "zone respect definition" covering both FVG and VI equally. Bodies inside, wicks can breach. |

### Resolved in v0.3 (From Olya's Full Validation Pass)

| Area | Resolution |
|---|---|
| Equilibrium rule | Can still enter with full 5-factor confluence — lower probability, not automatic no-trade. |
| CBDR usage | Removed. Not used. |
| Asia Range timing | Locked to 19:00–00:00 NY. Not approximate. Max 30 pips. |
| Misalignment rule | Can still take scalps on LTF when Weekly/Daily disagree. Risk stays 1%. |
| Judas Swing vs Liquidity Sweep | Same concept. Consolidated. Max 30–40 pips. |
| FVG respected definition | Candle bodies must stay inside FVG. Wicks can break, bodies cannot. |
| SMT usage | Removed for now. May add back after method validated. |
| Position sizing calculation | System handles it. Just specify 1% risk. |
| Stop loss placement | By swings, not pips. Below/above the swing that provided liquidity. |
| Time stop | Removed. No time stops used. |
| Structure break exit | Removed for now. |
| Session close / dead time | No new entries after NYOKZ. Positions can run overnight if structure intact. |
| News rules specifics | 1hr before red folder news. No NYOKZ on CPI/FOMC. No Thu/Fri of NFP week. |

### Resolved in v0.2 (From Olya's First Feedback)

| Area | Resolution |
|---|---|
| Order Flow vs IPDA hierarchy | Order Flow is PRIMARY gate. IPDA/targets subordinate. Framework restructured. |
| "Both" bias option | Dead code. Never used. Bias = long_only, short_only, or none. |
| Runner logic | No runners. Single target, distance varies by alignment (internal vs external). |
| Daily loss limit | 2 losses = done for the day. Not percentage-based. |
| Confluence scoring | No numeric scoring. 5-factor checklist is binary. |
| Counter-trend trades | Rarely taken. Prefers to wait. If taken: scalp, 1%, internal target only. |
| Post-expansion entries | Same 5-factor checklist on H4/H1 timeframes. |
| Friday rules | Trade normally, internal targets, stop by noon NY. |
| News events | Avoid before/after major news. |
| Pair selection | EURUSD only until system validated. |

### Remaining Gaps

| Area | Notes |
|---|---|
| Overnight hold management | Positions can run overnight if structure intact. No specific management rules beyond that. |
| Multiple concurrent trades | Likely single position given EURUSD-only constraint. Not formally confirmed. |
| Consolidation/ranging day activity | Asia Range filter skips LOKZ on volatile days. What happens on those days beyond skipping is unclear. |

---

## Appendix C: Validation History

| Version | Pass | Key Changes |
|---|---|---|
| v0.1 | Initial synthesis | 55-concept taxonomy → chronological method. 8 NEEDS VALIDATION items. |
| v0.2 | Olya first feedback | Order Flow hierarchy corrected (was inverted). 8 items resolved. |
| v0.3 | Olya full validation | 13 corrections: CBDR removed, SMT removed, stops by swings, sessions locked, equilibrium updated. |
| v0.4 | Olya VI amendment | Volume Imbalance added as equal concept to FVG. Zone respect generalized. 7 sections amended. |

---

*This document is a CLAIM (v0.4). It describes what the sources say your method is. Only you can promote it to FACT.*

*Human frames. Machine computes. Human promotes.*
