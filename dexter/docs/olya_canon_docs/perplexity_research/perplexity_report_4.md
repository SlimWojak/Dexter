Review of Olya ICT Methodology  
(five‑drawer structure)

***

## 1. Plain‑language overview

Olya’s ICT methodology is organized into five “drawers,” each answering one governing question about the trade lifecycle:  

1. Foundation – What are the core concepts? [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
2. Context – What is the market environment? [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
3. Conditions – Is this setup valid here and now? [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
4. Entry – When and how do we act? [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
5. Management – How do we manage after entry? [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

This creates a **top‑down** pipeline: first define concepts, then read context, then gate setups, then execute, then manage outcomes, with strict ownership (who calculates vs who consumes) to avoid duplication or ambiguity. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

***

## 2. The five drawers in human language

### 2.1 Foundation (Drawer 1 – “What ARE these concepts?”)

Although the Foundation YAML itself is summarized in index.yaml rather than attached, the index describes its role clearly. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)

- Purpose: One canonical place for definitions: MSS (market structure shift), FVG, order blocks, liquidity concepts, PD (premium/discount), IPDA ranges, and universal invariants and prohibitions. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
- Rules:  
  - Each concept is defined once in Foundation, never re‑defined elsewhere.  
  - Other drawers only **reference** these definitions. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
  - Universal rules and “never do” prohibitions also live here (e.g., “do not use midnight boundaries for PDH/PDL; use 17:00 NY wicks only” is implemented in Context but defined in Foundation via GAP‑9). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

Effectively, Foundation is the ontology: terminology, universal formulas, and guardrails that everything else must obey. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)

***

### 2.2 Context (Drawer 2 – “Where is the market?”)

Context answers: “What is the current environment on the higher time frames, and what is the directional narrative for today?” [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

Key components:

- Time‑framing and cadence  
  - Weekly context: evaluated once per week at Sunday 17:00 NY, used only for macro limits and external objectives (PWHPWL, major PDAs), not for intraday execution or entry PD. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Daily analysis: at 00:00 NY, Context detects structure (Daily MSS), defines the daily dealing range, identifies PDAs and liquidity pools, and sets a daily objective (Draw on Liquidity). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Daily bias: after daily analysis, Context runs the 3Q framework and synthesizes a frozen trade bias until next 00:00 NY. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

- Structure and ranges  
  - Weekly MSS and weekly range define the big “box”; weekly role is strictly for limits and large objectives, never directly for entries. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Daily MSS, daily order flow, validated swings and IPDA ranges define the daily dealing range and equilibrium. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Structural premium/discount state (PD): formula defined in Foundation, implemented here as “structural PD”, using dealing range and equilibrium to label price as premium, discount or equilibrium. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

- Liquidity and objectives (Draw on Liquidity framework)  
  - PDH/PDL and PWH/PWL are calculated as wick extremes of the 17:00–17:00 Forex day/week, explicitly forbidding midnight boundaries and close‑based levels (GAP‑9). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
  - The daily objective is selected from a hierarchy: MMXM high/low, then PDH/PDL, then PWH/PWL, then daily/weekly FVG, filtered to only LIQUIDITYUNDELIVERED targets in the direction of Daily MSS (GAP‑7). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)

- Three Questions (3Q) Framework (BLUR‑001)  
  - Q1 – Location: “Where is price right now?” as a percentage in the daily dealing range, mapped to zones (deep discount → deep premium) and to nearest PDA. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Q2 – Objective: “Where is price likely to go?” via the Draw on Liquidity logic above. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Q3 – Respect: “Where is price coming FROM?” combining daily order flow and PDA respect to infer HTF directional intent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Bias synthesis: combines Q1–Q3 to output a trade bias (long‑only, short‑only, both, or none) with a bias note, frozen until next 00:00 NY. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

- PDA detection and registry (BLUR‑003)  
  - Context detects and registers immutable PDAs: FVGs (including IFVG and BPR), OBs and related ranges, with fixed price levels, timeframe, timestamp and quality metadata. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Conditions later tracks mutable status (untouched/tapped/respected/violated) but cannot alter the registry itself. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

- State machine and validation  
  - Warm‑up states (NOSTRUCTURE → WEEKLYONLY → NORANGE → NOOBJECTIVE → EQUILIBRIUM → FULLCONTEXT) mark when the system is not yet tradeable and what is missing. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - A validation checklist requires MSS, range, objective, non‑equilibrium PD state, synthesized bias and PDA tracking before labeling the day FULLCONTEXT. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

In spirit, Context is a **diagnostic framework** that converts raw price data into a structured, HTF narrative that can be consumed by the downstream drawers. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

***

### 2.3 Conditions (Drawer 3 – “Is this setup valid?”)

Conditions reads Context and decides whether you should even be looking for a trade here. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

Core ideas:

- Ownership discipline (BLUR‑001, BLUR‑002, BLUR‑003)  
  - Conditions does not calculate bias or PD; it **consumes** trade bias from Context’s 3Q framework and PD state from Context’s structural PD. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
  - Bias input: a dedicated signal reads tradebias, biasnote, HTF direction and Q1/Q2 outputs, and enforces “no‑trade” when Context says tradebias = none. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
  - PD check: uses structural PD (premium/discount/equilibrium) to gate long vs short vs no trade (equilibrium = no trade). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

- Alignment and confluence  
  - Weekly–daily alignment signal defines how weekly and daily roles interact: strong alignment, defer to weekly, or both directions allowed. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
  - HTF alignment count (weekly, daily, H4) provides a numeric measure of bullish/bearish unanimity and whether HTF is fully aligned. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
  - Layer confluence measures how many layers support long/short, whether entry direction is unanimous, and flags conflicting signals. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

- PDA and zone quality  
  - PDA status tracking: Conditions evaluates each PDA from the registry as untouched, tapped, respected, or violated, with trade permissions tied directly to status (violated PDAs are invalid; untouched are highest quality). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
  - FVG and OB status extend the same logic with additional columns for fill percentage, touch count, “in zone” flags and body‑only acceptance for OBs. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
  - Freshness and zone age metrics quantify time since structure break, bar age and touch count, enabling gates like “Freshness Gate” (age and break thresholds). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

- Composite gates  
  - High Quality Long/Short gates require structural discount/premium plus HTF entry match, and delegate numeric thresholds (freshness score, touch count) to an evaluator, so Conditions outputs counts while the evaluator decides on actual cutoffs. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
  - Alignment and Freshness gates aggregate multiple signals into simple outputs (ALIGNED, FRESH) for downstream use. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

- Known conflicts and resolutions  
  - A documented conflict notes that Layer 8 used structural PD while Layer 11 used daily PD; the recommendation is to align Layer 11 to structural PD, standardizing PD ownership in Context (BLUR‑002). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - Another conflict (threshold location) is marked as resolved by moving thresholds to the evaluator instead of baking them into Conditions. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

Conditions is essentially the **gatekeeper**: if Context says “we have a valid, directional day”, Conditions further asks “is this location/zone/setup high enough quality to justify looking for entries at all?”. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

***

### 2.4 Entry (Drawer 4 – “When/how to act?”)

Entry turns valid setups into concrete, time‑bound signals—session rules, kill zones, triggers and execution logic. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

Main components:

- Sessions and kill zones  
  - Three main sessions are defined in NY time: Asia (19:00–00:00), London (02:00–05:00), New York (07:00–10:00), plus off‑session ranges for low‑resistance liquidity. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - Each session has a “manipulation hour” (first hour) and a one‑hour kill zone starting one hour into the session (e.g., London KZ 03:00–04:00). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - Timing columns (isAsiaSession, isLondonSession, iskzAsia, etc.) make session/KZ logic machine‑readable. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

- Day‑of‑week context  
  - Each weekday has a qualitative role (e.g., Monday often consolidation, Tuesday/Wednesday often set H/L of week, Friday often distribution and profit‑taking). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - This supports expectation management for how aggressive to be on specific days. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

- Reference levels  
  - Weekly open (Sunday 17:00 NY) and NY midnight open (00:00 NY each day) are tracked and extended as key reference lines, with a note that many high‑quality entries form near the NY midnight open. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - These levels are used to contextualize price at the moment of entry. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

- Triggers and patterns  
  - Sweep entries: liquidity is taken into a PDA, followed by confirmation (MSS or displacement). This requires identification of the liquidity pool, a qualitative “extension”, PDA destination, and a confirmation event. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - Displacement entries: qualitative displacement defined in Foundation (forceful exit, structure removal, FVG creation, one‑sided intent) must be present. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - LTF MSS entries: 5‑minute and 15‑minute MSS with displacement and FVG. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - OB and FVG entries: entry at OB mean threshold or FVG boundaries/CE, with quality factors such as body size, speed and FVG coupling. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

- Timing priorities and liquidity pools  
  - Timing priority ranks kill zone > session > off‑session for sweep entries. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - Liquidity pools include session highs/lows, PDH/PDL, PWH/PWL, off‑session highs/lows and recent swing highs/lows, consolidating Context’s HTF liquidity with intraday structures. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

- Execution details  
  - Stop placement options mirror Management: full candle, body or swing stop, each with a risk profile. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
  - Position sizing is explicitly out of scope for Entry, delegated to risk management at a higher layer. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- Gaps and flags  
  - GAP‑ENTRY‑001: specific entry price choice inside FVG (top/bottom vs CE) is deliberately left to evaluator logic. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
  - GAP‑ENTRY‑002: multi‑entry scaling is not covered at this layer and is explicitly deferred to Management. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Entry is the **tactical** layer: it takes the approved context and conditions and defines exactly when and how to get into the market, with explicit time windows and pattern definitions. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

***

### 2.5 Management (Drawer 5 – “How to manage the trade?”)

Management governs everything after entry: targets, stops, lifecycle states and adjustments. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Initially this was the thinnest drawer, but many gaps have been explicitly decided and documented as “no‑feature” rules. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Targets and exits:

- Primary and post‑expansion targets  
  - Primary target prioritizes the daily objective (Draw on Liquidity) then PDH/PDL, PWH/PWL, then higher‑timeframe PDAs, aligned with Context’s objective. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
  - Post‑expansion behavior: after the daily objective is delivered with displacement, structure shifts to a rebalance mode where H4/H1 PDAs become targets; daily role becomes a direction filter only. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- Partial targets and post‑expansion gaps  
  - The YAML notes that detailed partial exit rules and post‑expansion targets were initially gaps; later, a major decision resolves this by choosing “NO PARTIALS” and a set‑and‑forget style (see gaps section below). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Stops, invalidation and trailing:

- Stop placement  
  - Initial stop options mirror Entry: beyond full candle, beyond body, or behind recent swing, with corresponding risk profiles. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
  - Invalidation conditions include price closing through OB body, FVG fully broken, new MSS against the trade, or displacement against the position. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- Trailing stop  
  - Originally a gap, now resolved as “trail to breakeven only,” with explicit triggers (15‑minute swing break or price moving 1R in favor) and a rule that SL is locked at entry with no further trailing. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Lifecycle and state transitions:

- MMM trade lifecycle and daily expansion lifecycle  
  - Phases: accumulation (wait), manipulation (alert/prep), distribution (active entries) tied to MMM logic. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
  - Pre‑expansion vs post‑expansion management states re‑use Context’s structure state and post‑expansion classification (impulsive vs grind). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
  - Delivery classification (impulsive vs grind) has operational consequences: impulsive with FVG allows post‑expansion trading, grind blocks it (GAP‑8). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Adjustments, re‑entry, scaling and time:

- Re‑entry criteria  
  - Initially a gap; now resolved by an explicit **NO RE‑ENTRY** rule: one attempt per narrative, with a single exception if a completely new MSS creates a new narrative. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- Scaling  
  - Position scaling is resolved as **NO SCALING**: full position at single entry, single TP or SL/BE exit; no adding or partials. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- Time‑based exits  
  - Explicit **NO TIME EXITS** rule: no forced close at session end or arbitrary time; exits are only price based (TP, SL, or BE). Overnight holds are allowed. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Risk per trade:

- Fixed risk model  
  - Risk per trade is fixed at 1% of account equity, independent of setup quality; no grading or variable risk. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
  - Position size formula is documented, and risk is calculated once at entry and never adjusted mid‑trade. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Scope notes:

- In scope: target identification, stop placements, invalidation rules, MMM phase transitions, post‑expansion behavior. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
- Out of scope: portfolio‑level rules, detailed position sizing implementation and account constraints. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

Management is the **policy** layer: it enforces simplicity and consistency (no partials, no scaling, no re‑entries, no time exits, fixed risk, breakeven‑only trailing) to reduce mid‑trade discretion. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

***

## 3. Conflict points and gaps (addendum)

### 3.1 Conflicts documented in the YAML

1. PD definition and usage (Conditions conflict CONFLICT‑COND‑001)  
   - Problem: Layer 8 was using structural PD, while Layer 11 used daily PD, creating two competing PD concepts. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
   - Resolution: The recommendation is to align Layer 11 to the structural PD state from Context, enforcing a single PD owner (Context via BLUR‑002). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
   - Status: Marked as a conflict with a recommendation; you should treat it as a mandatory refactor item.

2. Threshold ownership (CONFLICT‑COND‑002)  
   - Problem: Freshness and touch thresholds were initially baked into Conditions logic, blurring signal vs evaluator roles. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
   - Resolution: Thresholds moved to the evaluator; Conditions now outputs counts and raw metrics only. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
   - Status: Marked as resolved.

3. Blur fixes and ownership boundaries  
   - BLUR‑001: 3Q framework calculation in Context, consumption in Conditions is now enforced. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
   - BLUR‑002: PD formula defined in Foundation, implemented in Context, read‑only in Conditions is now enforced. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
   - BLUR‑003: PDA detection and registry in Context, status tracking in Conditions is now enforced. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)

### 3.2 Gaps explicitly recorded

Many gaps are listed and, importantly, several are already resolved by global policy decisions.

From Entry:

- GAP‑ENTRY‑001 – Specific entry price inside FVG (boundary vs CE)  
  - Status: flagged; left deliberately to evaluator discretion, with guidance from Foundation’s FVG definition. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

- GAP‑ENTRY‑002 – Multi‑entry scaling  
  - Status: flagged and delegated to Management; later resolved globally in Management as “NO SCALING”. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

From Management (gaps and decisions):

- GAP‑MGMT‑001 – Partial exit rules  
  - Status: RESOLVED – decision: **NO PARTIALS**.  
  - Implication: Only full exits at TP or SL; this simplifies management but removes flexibility. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- GAP‑MGMT‑002 – Trailing stop logic  
  - Status: RESOLVED – decision: **trail to breakeven only**, no further trailing. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- GAP‑MGMT‑003 – Re‑entry criteria  
  - Status: RESOLVED – decision: **NO RE‑ENTRY**; only new narrative after a new MSS creates a fresh opportunity. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- GAP‑MGMT‑004 – Position scaling  
  - Status: RESOLVED – decision: **NO SCALING** in or out. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- GAP‑MGMT‑005 – Time‑based exits  
  - Status: RESOLVED – decision: **NO TIME EXITS**, exits are exclusively price‑based. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

- GAP‑MGMT‑006 – Risk per trade  
  - Status: RESOLVED – decision: **FIXED RISK** 1% per trade, no grading or dynamic adjustment. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)

From Context (gaps 7–9, now resolved):

- GAP‑7 – Liquidity status model  
  - Resolution: Four‑state model LIQUIDITY/UNDELIVERED/SWEEP/REJECTED/BREAK and rule “only UNDELIVERED can be a valid target; SWEEP is the trigger, not destination”. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)

- GAP‑8 – Post‑expansion impulsive vs grind classification  
  - Resolution: Explicit candle‑based rules and operational consequences for post‑expansion trading permission, including a “impulsive with FVG” vs “grind” split. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)

- GAP‑9 – PDH/PDL/PWH/PWL Forex day/week definitions  
  - Resolution: Fixed on 17:00 NY wick‑based day/week; forbids 00:00 boundaries and close‑based levels. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)

### 3.3 Additional practical gaps or tensions

Beyond the YAML’s own “gaps” fields, several practical tensions emerge:

1. Thin explicit link between Context’s state machine and Management rules  
   - Context’s structure state (PREEXPANSION vs POSTEXPANSION) and delivery classification (impulsive vs grind) clearly drive when post‑expansion trading is allowed or blocked. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
   - However, Management’s state transitions could reference these explicitly in a single, summarized table or rule set (e.g., “if structurestate = POSTEXPANSION and delivery = grind, then no new entries; manage open positions only”). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)

2. Evaluator dependence vs codified rules  
   - Several critical judgements (sweep quality, displacement quality, FVG vs OB entry preference) remain “evaluator decides,” which is appropriate for discretionary trading but an obstacle for automation. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
   - A small rubric for each (e.g., minimum body percentage, maximum overlap, timing tolerance) would close this ambiguity while preserving discretion at the margin. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

3. Portfolio and risk aggregation  
   - Management explicitly excludes portfolio‑level rules and account constraints. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml)
   - For practical deployment (e.g., prop accounts), you might want a separate risk drawer or overlay that caps total directional exposure, correlated pairs, or number of concurrent trades.

***

## 4. Suggested improvements and academic‑style methodology comparison

This section compares Olya’s methodology structure against general expectations in academic methodology and evaluation frameworks, and suggests specific improvements. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf)

### 4.1 Methodological structure vs academic norms

Academic methodology frameworks typically emphasize four qualities: contribution, defensible design, rigour and credibility. [assets.publishing.service.gov](https://assets.publishing.service.gov.uk/media/5a8179c1ed915d74e33fe69e/Quality-in-qualitative-evaulation_tcm6-38739.pdf)

- Contribution (does it add knowledge/edge?)  
  - Olya’s methodology contributes a coherent, fully specified ICT‑style framework: PDA registry, 3Q bias, draw‑on‑liquidity hierarchy, explicit post‑expansion rules and a strongly rule‑based management scheme. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - It advances beyond generic ICT/SMC tutorials by formalizing ownership boundaries and data flow (Foundation → Context → Conditions → Entry → Management), which is rarely explicit in retail education. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained)

- Defensible design (can the design logically answer the central question?)  
  - Design is decomposed by question: each drawer answers exactly one question, and each signal/gate has a stated purpose and dependencies. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
  - This is close to a mixed‑methods research design where each component answers a sub‑question that rolls up to a main research question (“Should we take this trade, and how?”). [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf)

- Rigour (are procedures systematic and reproducible?)  
  - Rigour is strong on definitional clarity: PDH/PDL boundaries, PDA detection rules, daily bias freezing, and fixed risk policies are explicit and reproducible. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
  - The existence of state machines, validation checklists and composite gates further formalizes the process, which is consistent with quality frameworks for qualitative evaluation (clear criteria, step‑wise procedures). [assets.publishing.service.gov](https://assets.publishing.service.gov.uk/media/5a8179c1ed915d74e33fe69e/Quality-in-qualitative-evaulation_tcm6-38739.pdf)
  - However, measurement and validation of performance (e.g., expected value, win‑rate, drawdown characteristics) are not documented here, which would be essential in academic‑style evaluation.

- Credibility (is there evidence and transparency?)  
  - The YAML references internal sources (NEX docs, CSO filings), showing traceability of rules. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml)
  - For academic‑style credibility, adding explicit backtest protocols, out‑of‑sample validation and limitations would strengthen the methodology. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf)

### 4.2 Alignment with ICT and SMC literature

Public ICT material and SMC overviews emphasize order blocks, fair value gaps, liquidity pools, kill zones and time‑based setups as core concepts. [phidiaspropfirm](https://phidiaspropfirm.com/education/ict-vs-smc)

- Conceptual alignment  
  - Olya’s ontology (Foundation + Context) aligns closely with ICT: MMS/MSS, PD, OBs, FVGs, PDH/PDL, kill zones, MMXM, etc., and uses similar narrative framing (liquidity engineering, market maker model). [hw](https://hw.online/faq/ict-vs-smc-in-forex-trading-a-comprehensive-comparison/)
  - The addition of the 3Q framework and PDA registry gives more explicit structure than most public ICT/SMC presentations. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained)

- Structural differentiation  
  - Many ICT/SMC write‑ups blend context, conditions and entries together, while Olya’s five‑drawer decomposition enforces single‑question ownership and deduplication. [tradingview](https://www.tradingview.com/chart/XAUUSD/tbeKLkDL-Two-Roads-to-Profit-A-Comparison-of-ICT-SMC-and-Advanced-VSA/)
  - This is closer to software or research architecture than to the typical trading “strategy PDF.”

### 4.3 Concrete suggestions for improvement

1. Add an explicit “Method and Evaluation” overlay  

   Borrowing from qualitative evaluation frameworks, you could add a sixth, meta‑layer that describes:

   - Data sources and sampling: which instruments, time periods and sessions are in‑scope for this methodology. [assets.publishing.service.gov](https://assets.publishing.service.gov.uk/media/5a8179c1ed915d74e33fe69e/Quality-in-qualitative-evaulation_tcm6-38739.pdf)
   - Evaluation design: how trades are tagged (by gate, PD state, 3Q pattern, day of week), how performance is measured per drawer, and what constitutes evidence of edge. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf)
   - Limitations: conditions where the method is known to degrade (e.g., news spikes, low‑liquidity days, holidays).

   This would make the methodology more **defensible and auditable**, moving it closer to academic standards. [assets.publishing.service.gov](https://assets.publishing.service.gov.uk/media/5a8179c1ed915d74e33fe69e/Quality-in-qualitative-evaulation_tcm6-38739.pdf)

2. Define minimal quantitative rubrics for subjective components  

   To increase rigour and reproducibility without killing discretion:

   - For displacement and “impulsive” moves: codify minimum body‑to‑range ratios, maximum allowed overlaps, and maximum number of opposing candles (some of this already exists for post‑expansion; extend it to entry triggers). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
   - For sweep quality: define a minimal extension distance beyond the liquidity pool (in pips or % of dealing range). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
   - For PDA and zone quality: transform freshness and touch metrics into ordinal grades (A/B/C) with suggested usage rules (e.g., A‑grade zones only during pre‑expansion). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)

3. Strengthen explicit cross‑drawer contracts  

   The design already defines ownership, but could be made more explicit in a short “interface spec”:

   - Context → Conditions: list the exact fields Conditions may read (tradebias, pdstate, pdaregistry, structure state, objective) and which invariants must hold. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
   - Conditions → Entry: specify what Entry is allowed to assume (e.g., ALIGNED gate true, minimum freshness grade, allowed direction list). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)
   - Entry → Management: formalize the required metadata (entry reason, PD type, state at entry, risk multiple) so that Management can apply differentiated rules if desired. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

   This mirrors “defensible design” in research, where each module’s inputs and outputs are clearly stated. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf)

4. Document scenario‑based examples  

   For each drawer, create at least one worked example:

   - A full day where Context transitions from NOOBJECTIVE to FULLCONTEXT, then to POSTEXPANSION impulsive delivery, with screenshots or structured logs. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml)
   - Conditions deciding between two candidate PDAs, explaining freshness, touch counts and PD state. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
   - Entry selecting a sweep‑plus‑MSS entry in London KZ on a Tuesday, and Management applying “no partials, 1% fixed risk, trail to breakeven only”. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml)

   In academic terms, these are “case vignettes” that demonstrate how the methodology behaves in practice. [assets.publishing.service.gov](https://assets.publishing.service.gov.uk/media/5a8179c1ed915d74e33fe69e/Quality-in-qualitative-evaulation_tcm6-38739.pdf)

5. Consider an optional “advanced management profile”  

   While the core policy correctly prioritizes simplicity (no partials, no scaling, no re‑entries, fixed risk), a documented optional profile could be introduced for experienced users:

   - Example: “Profile B” allows limited partial exits at HTF PDAs or opposite‑side PDAs, or graded risk for A‑grade vs B‑grade setups, with strict rules. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml)
   - This should include clear conditions and backtest expectations to remain defensible.

### 4.4 Summary comparison table

Below is a concise comparison between Olya’s methodology, generic ICT/SMC presentations, and academic methodology expectations. [hw](https://hw.online/faq/ict-vs-smc-in-forex-trading-a-comprehensive-comparison/)

| Aspect | Olya ICT 5‑drawer | Typical ICT/SMC public material | Academic methodology expectation |
| --- | --- | --- | --- |
| Concept definitions | Centralized in Foundation; single source of truth. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml) | Often scattered across videos/posts. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained) | Clear, stable constructs and definitions. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf) |
| Structure | Five drawers by question; strict ownership and deduping. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/cbd5070a-5893-4c6e-92e5-ab9c23183040/index.yaml) | Context, setup and entries often mixed together. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained) | Modular design where each component addresses a sub‑question. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf) |
| Context logic | Rich HTF framework: MSS, PD state, 3Q bias, PDAs, warm‑up states. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/b967a053-d33e-41a3-bf2a-b65f0f6c3d48/context.yaml) | Usually partial; bias often informal. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained) | Systematic context characterization with explicit criteria. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf) |
| Conditions | Formal gates for PD, bias, alignment, PDA status and freshness. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a3ad94fd-6077-4227-8dfa-8edcff5d3b66/conditions.yaml) | Often described verbally as “confluence” without precise gates. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained) | Transparent inclusion/exclusion criteria. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf) |
| Entry | Explicit sessions, kill zones, triggers, and liquidity pools. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/264e2865-9983-4169-8d14-6cc29904ac9e/entry.yaml) | Sessions/kill zones present but often less formally encoded. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained) | Clear operational procedures that can be replicated. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf) |
| Management | Simple, rule‑based: no partials, no re‑entries, no scaling, fixed risk, BE‑only trailing. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/164227298/a104e67a-9e52-438d-8072-0375ca85c88e/management.yaml) | Management sometimes under‑specified or discretionary. [eplanetbrokers](https://eplanetbrokers.com/en-US/training/ict-trading-strategy-explained) | Prespecified decision rules to limit bias and drift. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf) |
| Evaluation | Not included in these YAMLs; backtest/validation implied but not documented. | Rarely formalized publicly. | Explicit evaluation design, evidence and limitations. [dera.ioe.ac](https://dera.ioe.ac.uk/id/eprint/21069/2/a-quality-framework-tcm6-38740.pdf) |

***

If you’d like, I can next turn this into a formatted PDF‑style text (with headings, page‑break suggestions and a short executive summary) ready to hand to team members or external reviewers.