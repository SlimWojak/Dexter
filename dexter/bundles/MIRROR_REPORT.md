# Mirror Report — Trading Logic Synthesis

**Generated:** 2026-02-05 12:53 UTC
**Purpose:** CSO (Olya) review of extracted methodology
**Source:** Dexter Evidence Refinery

---

*This report synthesizes IF-THEN trading logic extracted from your notes, ICT 2022 Mentorship, and supplementary materials. Review for accuracy — your corrections will improve the extraction.*

---

# Trading Logic Synthesis Report for Olya

## Section 1: What We Found In Your Notes

### Higher Timeframe Direction

Your approach to higher timeframe analysis shows a sophisticated multi-layered framework. You consistently reference the relationship between daily direction exhaustion and the emergence of smaller timeframe models ("Daily direction order flow gets exhausted → market maker small 5/15 min models start"). This appears frequently across your notes, particularly in your tips document.

A core pattern in your methodology: when price enters external liquidity on higher timeframes and hits targets, your focus immediately shifts to lower timeframe opposite liquidity levels, with special emphasis on the last 5-day range within a 20-day context. This granular approach to timeframe transition appears unique to your practice.

Your use of the 4-hour timeframe as a pivotal level-finder when daily exhaustion occurs is precise and repeatable. You've also developed clear rules around when Asia Range runs aren't required - specifically when "clear draw on liquidity exists AND top down analysis confirms AND DXY alignment is on point."

### Market Structure

Your market structure analysis emphasizes "low resistance liquidity runs" - a concept you return to repeatedly. You've identified that when price has one-sided expansion followed by pullback into the created range, these low resistance areas become high-probability purge zones (appears in NOTES.pdf multiple times).

A critical insight from your practice: "lack of liquidity run or no clear direction to price → price will gravitate towards those areas." This gravitational pull toward unclear liquidity is a refinement you apply consistently.

Your breaker block identification is more stringent than standard teaching - you require "high probability OB for opposing direction has engulfing candle close through and above/below it" before classifying as a breaker. You also note breakers at the beginning of runs should NOT be traded.

The relationship between midpoint breaks, 15-minute MSS, and FVG formation appears as a trinity in your execution logic, particularly in your 5-minute scalping methodology.

### Premium & Discount Zones

Your BPR (Balanced Price Range) concept is distinctive: "BPR above or below an order block → price is likely NOT to return to that OB." This filtration mechanism appears across multiple strategy documents.

You've developed specific rules for Asia Range validity - the 30-pip maximum threshold is absolute in your system. When exceeded, you classify the setup as invalid without exception.

Your treatment of breakers varies by location: breakers forming after one-sided delivery into premium/discount are valid, but those at the beginning of runs are explicitly avoided. This nuanced approach to the same structure based on context is a hallmark of your methodology.

### Entry Patterns

Your entry logic shows remarkable precision around timing and structure. The "Option A/B/C" framework from your TIPS document provides clear decision trees:
- Option A: Strong protraction with liquidity run into opposing PDAs during killzone
- Option B: Strong isolation with "31st L type structure" when current PA can't be trusted
- Option C: Continuation when LTF orderflow makes liquidity runs impractical

Your 5-minute liquidity scalp model is perhaps your most refined system. The requirements are strict: clear liquidity draw (usually Asia highs/lows), no opposite side liquidity taken, visible 5-minute MMM, and clear liquidity run within that MMM. If opposite side strong FVG remains open, the setup is invalidated entirely.

The Asia Range Sweep strategy shows similar precision: sweeps must occur between 00:20-1:25 AM, extend 1-20 pips beyond the range (more than 20 pips invalidates), and the 5-minute FVG must sit inside the range for validity.

### Confirmation Signals

Your confirmation requirements layer multiple factors. The 15-minute model flexibility ("15min model is not very clear BUT all other pieces are there → trade can still be valid") shows discretionary judgment, but only when near HTF targets.

You've developed a hierarchy of confluences for 5-minute scalps: IFVG formation during liquidity take, 5-minute EMA break, BPR break within midpoint, and 15-minute EMA break. These aren't required but add probability when present.

Your use of SMT divergence is selective - you look for it specifically after new highs are taken on liquidity grabs, not as a standalone signal.

## Section 2: What ICT 2022 Mentorship Teaches

### Higher Timeframe Direction

The ICT methodology emphasizes liquidity draw identification as the primary filter ("cannot identify the draw on liquidity first → do not enter a trade"). The standard teaching uses the 50% dealing range level during NY AM session for bias determination.

Market structure shifts after liquidity sweeps are presented as the core entry signal throughout the mentorship. The teaching emphasizes looking for displacement after fair value gaps, particularly during the London session.

### Market Structure

ICT's approach to market structure centers on the relationship between liquidity sweeps and structure shifts. The canonical pattern: sweep → shift → entry appears repeatedly in the source material.

The teaching emphasizes consecutive candle body gaps and their fills as continuation signals. Weekly candle wicks into breaker blocks are taught as reversal indicators.

### Premium & Discount Zones

The mentorship teaches standard premium/discount concepts based on dealing ranges, with emphasis on the 50% level for bias determination. Fair value gaps are treated uniformly as retracement and continuation zones.

### Entry Patterns

ICT teaches specific session-based patterns: Asian high swept during London → look for reversal to downside. The optimal trade entry (OTE) using previous day's data for London setups is a cornerstone concept.

The teaching emphasizes time-based entries during kill zones with less emphasis on the granular structural requirements you've developed.

### Confirmation Signals

Standard ICT confirmation comes from alignment of multiple timeframes, displacement after FVG entries, and market structure shifts post-liquidity runs.

## Section 3: What Blessed Trader Emphasises

The Blessed Trader material focuses heavily on CBDR (Central Bank Dealer Range) integration with standard ICT concepts:

- CBDR quiet + Asian Range quiet (<30p) = high probability expansion day
- 1-SD/2-SD CBDR extensions as reversal zones (Juda swing concept)
- Deep discount = step aside from shorts
- CBDR >50p or Asian >30p = avoid next day LOKZ trading
- Juda swing exceeding 40-50 pips = red flag day

The visual examples emphasized quick scalps against daily momentum after SSLQ sweeps and targeting deeper liquidity after FVG pullbacks.

## Section 4: Where Your Practice Differs From The Teaching

| Topic | ICT Teaching | Your Applied Logic | Delta |
|-------|--------------|-------------------|-------|
| **Timeframe Transition** | Standard HTF → LTF progression | Daily exhaustion → 4HR levels → 5/15min models | You've identified specific exhaustion patterns that trigger model transitions |
| **Liquidity Focus** | General liquidity pool identification | 20-day range with emphasis on last 5 days + "low resistance liquidity" classification | Much more granular liquidity categorization system |
| **Asia Range Usage** | General reference point | Strict 30-pip maximum threshold + specific 00:20-1:25 AM sweep window | Quantified rules vs conceptual framework |
| **Breaker Blocks** | Treat similar to order blocks | Must have engulfing close through high probability OB + location-based validity | Additional filters for breaker classification and usage |
| **5-Minute Scalping** | Not specifically taught | Complete model: clear draw + no opposite liquidity taken + 5min MMM visible + opposite FVG check | Entirely new execution model |
| **Entry Flexibility** | MSS after sweep = entry | Option A/B/C framework based on market conditions | Conditional entry logic vs rigid rules |
| **Confirmation Requirements** | Multi-timeframe alignment | Layered confluences with hierarchy + flexibility near HTF targets | Weighted confirmation system |
| **BPR Usage** | Standard balanced price concept | BPR above/below OB = price won't return | Predictive filtering mechanism |
| **Structure Requirements** | Strong highs/lows before moves | "No strong high/low needed - price makes structure at liquidity" | Inverted logic on structure formation |
| **Session Timing** | Kill zones as windows | Precise timing: LOKZ MR 03:00-04:00, sweep windows, late London invalidation | Micro-timing within macro-windows |

## Section 5: Patterns That Repeat Across Your Notes

### Core Beliefs (3+ appearances across different contexts):

1. **Low Resistance Liquidity Concept** - Appears in contexts of range development, pullback analysis, and intraday structure. You consistently identify and trade toward these "easy" liquidity pools.

2. **Exhaustion → Model Transition** - Whether daily → 4HR → 5/15min or noting "last stages of MMM → quick pullback to nearest OB," you consistently identify exhaustion patterns that trigger systematic transitions.

3. **Opposite Side Liquidity Status** - Checking whether opposite liquidity has been taken appears in your Asia strategy, 5-minute scalps, and 15-minute OTE setups. This is a core filter.

4. **Midpoint + MSS + FVG Trinity** - This combination appears in multiple strategies as your structural confirmation cluster.

5. **HTF Proximity Flexibility** - When "very close to main HTF target," you consistently relax LTF requirements, showing systematic discretion.

6. **IFVG Development Monitoring** - You specifically watch for IFVG formation during liquidity takes across multiple strategies.

7. **Time-Based Invalidation** - Late timing invalidates setups across your Asia sweep, LOKZ, and general entry strategies.

## Section 6: Open Questions

### Potential Extraction Gaps or Clarification Needs:

1. **"31st L type structure"** (TIPS document) - This appears to be a specific pattern you recognize but wasn't fully explained in the extraction. What defines this structure?

2. **Conflict: 1HR Relevance** - Your 5-minute scalp notes state "1hr is irrelevant" but other strategies reference 1HR extensively. Is this context-specific to just 5-minute scalps?

3. **IOFED Relationship to MMM** - You note IOFED happens in "late phases of MMM" but also mention avoiding trades against hourly IOFED. How do these concepts integrate?

4. **BPR Formation Timing** - When exactly does a BPR form in your analysis? The extraction shows you use it as a filter but not the formation criteria.

5. **DXY Alignment Specifics** - Referenced in your no-AR-run scenario but specific alignment criteria weren't captured.

6. **"Option B" Conditions** - What exactly makes "current price action cannot be trusted"? This discretionary element could use clarification.

7. **5-Minute MMM Recognition** - You reference "small 5min MMM visible" - what constitutes "small" and what are the visual markers?

8. **4HR Level Selection** - When daily exhaustion occurs, how do you identify which 4HR levels to use?

These questions highlight where your intuitive pattern recognition might benefit from explicit codification, or where the extraction may have missed nuanced explanations in your original notes.

---

## Report Metadata

| Tier | Claims Included |
|------|-----------------|
| Your Notes (OLYA_PRIMARY) | 172 |
| ICT 2022 Mentorship | 804 |
| Blessed Trader (LATERAL) | 10 |
| **Total** | **986** |

*Generated by Dexter Mirror Report Generator v1.0*
