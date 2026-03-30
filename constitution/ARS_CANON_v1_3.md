# Asia Range Scalp Strategy - CANON
## Version: 1.3 - Machine Executable
## Date: March 28, 2026
## Status: COMPLETE (Core Logic — Walk-Forward Validated)
## Lineage: Supersedes asia_range_scalp_strategy_FINAL v1.0 (January 20, 2026)

### v1.3 Changes (Olya-directed, walk-forward validated, March 28, 2026)
6. Sweep extension minimum lowered: 3 pips → 2 pips (walk-forward validated)
7. FVG untouched minimum lowered: 1.0 pip → 0.5 pip (walk-forward validated)
8. FVG entry capped at 03:00 NY — no entry if Candle C closes after 03:00

### v1.2 Changes (Olya-directed, March 28, 2026)
5. Timeout removed: purely mechanical set-and-forget (SL or TP only, no time-based exit)

### v1.1 Changes (Olya-directed, March 28, 2026)
1. Sweep extension minimum raised: 1 pip → 3 pips (valid range now 2-20 pips per v1.3)
2. FVG Candle B position: body must be at least partially inside Asia range (intention to return)
3. R:R threshold lowered: 1.5R → 1.4R
4. TP adjusted 0.5 pip conservative (inward from opposite boundary wick)

---

## STRATEGY OVERVIEW

**Name:** Asia Range Scalp Strategy
**Pair:** EUR/USD only
**Session:** Asia session consolidation → London Killzone (LOKZ) sweep
**Edge:** Mean reversion after liquidity sweep of low-volatility range
**Risk per trade:** 1% account equity
**Minimum R:R:** 1.4R
**Max trades per session:** 1 (hard cap)

---

## 1. SESSION WINDOWS

### Asia Range Definition Window
```
Time: 7:00 PM - 12:00 AM NY time
UTC Winter (EST, UTC-5): 00:00 - 05:00 UTC
UTC Summer (EDT, UTC-4): 23:00 - 04:00 UTC (previous day)
```

### Valid Sweep Window
```
Time: 12:00 AM - 4:00 AM NY time
UTC Winter (EST): 05:00 - 09:00 UTC
UTC Summer (EDT): 04:00 - 08:00 UTC
```

**DST Handling:**
- All timestamps anchored to UTC
- Offsets adjust based on DST status
- Follow NY local time behavior

---

## 2. ASIA RANGE MEASUREMENT

### Definition
```python
# Measure during 7:00 PM - 12:00 AM NY

asia_high = max(all_candle_high_wicks)  # Highest wick
asia_low = min(all_candle_low_wicks)    # Lowest wick
asia_range = asia_high - asia_low       # Pips

# Example:
# Highest wick: 1.1630
# Lowest wick: 1.1605
# Range: 25 pips
```

### Validation
```python
# Consolidation requirement
if asia_range > 30:  # pips (0.0030 for EUR/USD)
    reject_session()  # Too wide, not consolidating
```

**Rules:**
- Always wick-to-wick measurement
- Timeframe irrelevant (highs/lows identical across TFs)
- Range >30 pips = invalidate entire session

---

## 3. SWEEP DETECTION

### Sweep Definition

**High Sweep:**
```python
max_price_beyond = get_max_price()  # Furthest traded price during sweep window
extension = max_price_beyond - asia_high

valid_high_sweep = (2 <= extension <= 20)  # Pips
```

**Low Sweep:**
```python
min_price_beyond = get_min_price()
extension = asia_low - min_price_beyond

valid_low_sweep = (2 <= extension <= 20)  # Pips
```

### Extension Validation

**Per-Direction Tracking:**
```python
# Track separately for high vs low

max_high_extension = 0
max_low_extension = 0

# During sweep window:
if price > asia_high:
    extension = price - asia_high
    max_high_extension = max(max_high_extension, extension)

if price < asia_low:
    extension = asia_low - price
    max_low_extension = max(max_low_extension, extension)

# Validation:
if max_high_extension > 20:
    invalidate_high_sweep_setups()  # High only

if max_low_extension > 20:
    invalidate_low_sweep_setups()   # Low only

# Minimum extension check:
if max_high_extension < 2:
    no_valid_high_sweep = True  # Insufficient penetration

if max_low_extension < 2:
    no_valid_low_sweep = True   # Insufficient penetration
```

**Rules:**
- Extension = furthest traded price beyond boundary (any timeframe)
- Valid range: 2-20 pips (inclusive)
- Extensions <2 pips are noise, not genuine liquidity sweeps
- Track maximum extension across ALL attempts per direction
- If ANY extension >20 pips in a direction → invalidate that direction's setups
- Opposite direction remains valid if within limits

### Re-acceptance Requirement

```python
# At least ONE 5-min candle must close strictly back inside Asia range

sweep_valid = False

for candle in candles_after_sweep:
    if asia_low < candle.close < asia_high:  # Strictly inside
        sweep_valid = True
        break

# If no close back inside → invalid sweep, no FVG entry
```

**Rules:**
- Must be 5-minute candle close
- Must be STRICTLY inside (not on boundary)
- Boundary = liquidity level, not acceptance
- Can occur on same candle as FVG or earlier

---

## 4. FVG (FAIR VALUE GAP) DETECTION

### Structure

**3 consecutive 5-minute candles:**
- Candle A (first)
- Candle B (middle) — must show intention to return to range
- Candle C (third/current) — must close inside range

### Bullish FVG (After Low Sweep)

```python
# Formation conditions
candle_A = candle[n-2]
candle_B = candle[n-1]
candle_C = candle[n]

# 1. Gap exists
gap_exists = (candle_A.high < candle_C.low)

# 2. Partial body untouched (≥0.5 pip)
b_body_top = max(candle_B.open, candle_B.close)
b_body_bottom = min(candle_B.open, candle_B.close)

untouched_bottom = max(candle_A.high, b_body_bottom)
untouched_top = min(candle_C.low, b_body_top)
untouched_size = untouched_top - untouched_bottom

untouched_valid = (untouched_size >= 0.00005)  # 0.5 pip for EUR/USD

# 3. Candle B body at least partially inside Asia range (intention to return)
b_body_overlaps_range = (b_body_top > asia_low AND b_body_bottom < asia_high)

# 4. Candle C closes strictly inside Asia range
c_inside = (candle_C.close > asia_low AND candle_C.close < asia_high)

# Valid bullish FVG
valid_fvg = gap_exists AND untouched_valid AND b_body_overlaps_range AND c_inside

# FVG zone boundaries
if valid_fvg:
    fvg_top = candle_C.low       # Wick
    fvg_bottom = candle_A.high   # Wick
    true_imbalance = [untouched_bottom, untouched_top]
```

### Bearish FVG (After High Sweep)

```python
# 1. Gap exists
gap_exists = (candle_A.low > candle_C.high)

# 2. Partial body untouched
b_body_top = max(candle_B.open, candle_B.close)
b_body_bottom = min(candle_B.open, candle_B.close)

untouched_bottom = max(candle_C.high, b_body_bottom)
untouched_top = min(candle_A.low, b_body_top)
untouched_size = untouched_top - untouched_bottom

untouched_valid = (untouched_size >= 0.00005)  # 0.5 pip

# 3. Candle B body at least partially inside Asia range (intention to return)
b_body_overlaps_range = (b_body_top > asia_low AND b_body_bottom < asia_high)

# 4. Candle C closes inside
c_inside = (candle_C.close > asia_low AND candle_C.close < asia_high)

# Valid bearish FVG
valid_fvg = gap_exists AND untouched_valid AND b_body_overlaps_range AND c_inside

# FVG zone
if valid_fvg:
    fvg_top = candle_A.low       # Wick
    fvg_bottom = candle_C.high   # Wick
```

### FVG Validation Rules

**Minimum Gap:**
- Fixed pip requirement: ≥0.5 pip untouched (v1.3, walk-forward validated)
- Measured in actual price units (0.00005 for EUR/USD)
- High quality threshold: ≥2.0 pips

**Untouched Area:**
- Partial fill = still valid (as long as ≥0.5 pip remains)
- Full fill = invalid
- Any continuous price segment ≥0.5 pip = valid

**Candle B Position (Intention to Return):**
- Candle B body (open-to-close) must at least partially overlap with Asia range
- Test: `b_body_top > asia_low AND b_body_bottom < asia_high`
- If Candle B body is entirely above asia_high or entirely below asia_low → reject FVG
- Rationale: Candle B must show price is returning toward the range, not extending away

**Candle C Position:**
- MUST close STRICTLY inside Asia range
- NOT on boundary: `asia_low < close < asia_high`
- Boundary closes rejected (could be spread effects)

**FVG Gap Location:**
- Gap itself need not be entirely inside Asia range
- Requirements: Candle B overlaps range, Candle C closes inside

---

## 5. ENTRY LOGIC

### Entry Timing
```python
# Enter IMMEDIATELY when Candle C closes

if valid_fvg:
    # Submit market order at candle close
    submit_market_order()

    # Entry price = next available fill
    entry_price = next_available_tick()  # NOT candle close price
```

**Rules:**
- No waiting for retrace into FVG zone
- Fast scalps = immediate execution
- Entry ≈ Candle C close ± spread

### One Trade Per Session
```python
session_trade_taken = False

for candle in sweep_window:
    if session_trade_taken:
        break  # Stop scanning entirely

    if valid_sweep and valid_fvg and valid_rr:
        enter_trade()
        session_trade_taken = True
```

**Rules:**
- Maximum 1 trade per session (hard cap)
- Once entered, ignore ALL subsequent setups
- Preserves early-session liquidity reversion edge

### First Valid Setup Priority

**"First sweep" = first event satisfying ALL:**
1. Extension 2-20 pips ✓
2. Re-acceptance (5m close strictly inside range) ✓
3. Valid FVG formation (including Candle B overlap) ✓
4. Candle C closes before 03:00 NY ✓
5. Valid R:R (≥1.4R) ✓

**Incomplete probes ignored:**
- Sweep without FVG → continue scanning
- FVG without valid R:R → continue scanning
- Take first COMPLETE valid setup only

---

## 6. STOP LOSS PLACEMENT

### SL Calculation
```python
# SL = Sweep extreme ± 0.5 pip buffer

# HIGH SWEEP (Short entry)
sweep_high_wick = max_price_beyond_asia_high
sl = sweep_high_wick + 0.00005  # +0.5 pip buffer (EUR/USD)

# LOW SWEEP (Long entry)
sweep_low_wick = min_price_beyond_asia_low
sl = sweep_low_wick - 0.00005   # -0.5 pip buffer
```

**Example:**
```
Asia low: 1.1600
Sweep low wick: 1.1592 (-8 pips beyond boundary)
SL: 1.1592 - 0.00005 = 1.15915

Entry: 1.1605
Risk: 1.1605 - 1.15915 = 8.5 pips
```

### Buffer Specification
- Fixed: 0.5 pips
- EUR/USD: 0.00005 price units
- Applied beyond sweep extreme (not Asia boundary)

### Risk Distance
- **NO hard pip limit** on SL distance from Asia boundary
- SL distance = sweep extension + buffer
- Position size adjusts to maintain 1% account risk
- Variable risk pips per trade (geometry-dependent)

---

## 7. TAKE PROFIT TARGET

### TP Calculation
```python
# Target = opposite Asia boundary WICK, adjusted 0.5 pip conservative (inward)
# Rationale: price may wick to boundary but just miss — 0.5 pip cushion ensures fill

# LONG (after low sweep)
tp = asia_high - 0.00005  # Wick minus 0.5 pip (EUR/USD)

# SHORT (after high sweep)
tp = asia_low + 0.00005   # Wick plus 0.5 pip (EUR/USD)
```

**Example:**
```
Asia high wick: 1.1630

LONG TP = 1.1630 - 0.00005 = 1.16295 ✓
NOT 1.1630 (might just miss) ✗
```

**Rationale:**
- Liquidity rests at wick extremes, not closes
- Price may wick to boundary but reverse just short of touching
- 0.5 pip inward cushion improves fill probability
- Conservative: sacrifices ~0.5 pip reward for higher execution certainty

---

## 8. RISK:REWARD VALIDATION

### Pre-Entry R:R Check
```python
# BEFORE entering, validate R:R

# Estimate entry
estimated_entry = candle_C.close  # Or bid/ask adjusted

# Calculate SL
sl = sweep_extreme ± 0.00005

# Calculate TP (with 0.5 pip conservative adjustment)
# LONG: tp = asia_high - 0.00005
# SHORT: tp = asia_low + 0.00005

# Calculate R:R
estimated_risk = abs(estimated_entry - sl)
estimated_reward = abs(tp - estimated_entry)
estimated_rr = estimated_reward / estimated_risk

# Validation
if estimated_rr < 1.4:
    reject_setup()  # Do not enter
    continue_scanning()

# If valid, proceed
if estimated_rr >= 1.4:
    submit_market_order()
```

**Rules:**
- Minimum 1.4R required
- Validation BEFORE order submission
- Based on estimated entry ≈ Candle C close
- TP used in R:R calculation includes the 0.5 pip conservative adjustment
- Reject setup if insufficient R:R
- Continue scanning for next valid setup

---

## 9. POSITION SIZING

**Risk per trade:** 1% account equity

```python
# Formula (deferred to implementation phase)

# General principle:
position_size = (account_equity × 0.01) / (risk_pips × pip_value)

# Where:
# - account_equity = current account balance
# - risk_pips = abs(entry - sl) in pips
# - pip_value = varies by pair, lot size, account currency

# EUR/USD specifics and exact implementation: FLAGGED
```

**Rules:**
- 1% risk maintained regardless of SL distance
- Position size adjusts based on actual sweep geometry
- Larger sweeps = smaller position size
- Smaller sweeps = larger position size

---

## 10. RISK MANAGEMENT

### Session Limits
```python
# CONFIRMED:
max_trades_per_session = 1  # Hard cap

# CONFIRMED:
max_daily_loss = 1.0  # 1R = -1% account equity
# If hit, stop trading for the day
```

### Weekly/Consecutive Limits
**FLAGGED - Deferred to refinement phase**

Considerations:
- Max consecutive losses before review
- Max weekly drawdown threshold
- Balance between taking all valid setups vs capital preservation

### Trade Management
**FLAGGED - Deferred to backtest phase**

To be tested:
- Breakeven moves (e.g., at 1R)
- Partial exits
- Trailing stops

**Current:** Fixed SL/TP only (set-and-forget, no time-based exit)

---

## 11. COMPLETE EXECUTION FLOW

### Trade Lifecycle
```python
# PHASE 1: Session Setup
# 1. Measure Asia range (7 PM - 12 AM NY)
# 2. Validate: range ≤ 30 pips
# 3. If invalid → reject session, wait for next day

# PHASE 2: Sweep Detection (12 AM - 4 AM NY)
# 4. Monitor for sweep (2-20 pips beyond boundary)
# 5. Track max extension per direction PROGRESSIVELY (temporal ordering)
# 6. If extension >20 pips → invalidate that direction
# 6a. If extension <2 pips → no valid sweep in that direction
# 7. Require re-acceptance (5m close strictly inside range)
# NOTE: Sweep MUST occur before FVG — extensions tracked progressively

# PHASE 3: FVG Detection (entry must be before 03:00 NY)
# 8. Scan for 3-candle FVG pattern (5m candles)
# 9. Validate: gap exists, ≥0.5 pip untouched
# 9a. Validate: Candle B body at least partially inside Asia range
# 9b. Validate: Candle C closes strictly inside Asia range
# 9c. Validate: Candle C closes before 03:00 NY
# 10. Calculate FVG zone boundaries

# PHASE 4: Pre-Entry Validation
# 11. Estimate entry price ≈ Candle C close
# 12. Calculate SL = sweep extreme ± 0.5 pip
# 13. Calculate TP = opposite boundary wick - 0.5 pip (inward)
# 14. Validate R:R ≥ 1.4
# 15. If R:R insufficient → reject setup, continue scanning

# PHASE 5: Entry Execution
# 16. Submit market order at Candle C close
# 17. Entry fill = next available tick
# 18. Set session_trade_taken = True

# PHASE 6: Order Management
# 19. Place SL order at sweep extreme ± 0.5 pip (outward)
# 20. Place TP order at opposite boundary wick - 0.5 pip (inward)
# 21. Position size for 1% risk
# 22. Set-and-forget: no timeout, no time-based exit
# 23. Trade resolves ONLY when SL or TP is hit

# PHASE 7: Session Completion
# 24. Ignore all subsequent sweeps/setups
# 25. One trade maximum per session
```

---

## 12. INVALIDATION RULES

### Session Invalidation
```python
# Asia range too wide
if asia_range > 30:  # pips
    reject_session()

# No sweep occurs
if no_sweep_in_window:
    no_trade_today()

# Sweep extension too large (per direction)
if max_high_extension > 20:
    invalidate_high_sweep_setups()

if max_low_extension > 20:
    invalidate_low_sweep_setups()

# Sweep extension too small (per direction)
if max_high_extension < 2:
    no_valid_high_sweep()  # Noise, not a genuine sweep

if max_low_extension < 2:
    no_valid_low_sweep()   # Noise, not a genuine sweep
```

### Setup Invalidation
```python
# No re-acceptance
if sweep_occurred and not close_back_inside:
    invalid_sweep = True

# Candle B body entirely outside Asia range
b_body_top = max(candle_B.open, candle_B.close)
b_body_bottom = min(candle_B.open, candle_B.close)
if b_body_top <= asia_low or b_body_bottom >= asia_high:
    invalid_fvg = True  # No intention to return

# Candle C closes on boundary
if candle_C.close == asia_high or candle_C.close == asia_low:
    invalid_fvg = True

# Insufficient R:R
if estimated_rr < 1.4:
    reject_setup()

# Entry cap: no FVG entry after 03:00 NY (v1.3, walk-forward validated)
if candle_C.close_time > "03:00 AM NY":
    reject_setup()
```

---

## 13. EDGE CASE HANDLING

### Multiple Sweeps - Same Direction
```python
# Example: Multiple low sweeps (all within 2-20 pips)
# 1:00 AM: -8 pips, no FVG
# 2:00 AM: -15 pips, no FVG
# 3:00 AM: -11 pips, FVG forms

# Action: Take first valid FVG (3:00 AM) ✓
```

### Multiple Sweeps - Opposite Directions
```python
# Example:
# 1:00 AM: Low swept (-10 pips), FVG forms, entered ✓
# 2:00 AM: High swept (+12 pips)

# Action: Ignore high sweep (already in trade) ✓
# One trade per session rule applies
```

### Candle C on Boundary
```python
# Asia range: 1.1600 - 1.1630
# Candle C closes at exactly 1.1630

# Invalid: NOT strictly inside
valid = False  # Reject setup
```

### Candle B Entirely Outside Range
```python
# Asia range: 1.1600 - 1.1630
# After low sweep, Candle B body: 1.1590 - 1.1595

# Invalid: body entirely below asia_low, no intention to return
valid = False  # Reject FVG

# But if Candle B body: 1.1595 - 1.1605
# Valid: body partially overlaps range (1.1600 - 1.1605 inside) ✓
```

### Partial FVG Fill
```python
# FVG zone: 1.1625 - 1.1630 (5 pip gap)
# Candle A violates 3 pips
# Candle C violates 1 pip
# Untouched: 1 pip remains

# Valid: untouched ≥ 0.5 pip ✓
```

### Marginal Sweep Extension
```python
# Asia low: 1.1600
# Price dips to 1.15985 (1.5 pips beyond)

# Invalid: extension < 2 pips (noise, not genuine sweep)
valid_sweep = False
```

---

## 14. MACHINE LOGIC SUMMARY

### Complete Algorithm
```python
# INITIALIZATION
session_trade_taken = False
max_high_extension = 0
max_low_extension = 0

# PHASE 1: Asia Range
asia_range = measure_range("19:00", "00:00", "NY")
if asia_range > 30:
    exit("Session invalid - range too wide")

# PHASE 2: Sweep Window
for candle in time_range("00:00", "04:00", "NY"):

    if session_trade_taken:
        break

    # Track sweeps
    if candle.high > asia_high:
        extension = candle.high - asia_high
        max_high_extension = max(max_high_extension, extension)

    if candle.low < asia_low:
        extension = asia_low - candle.low
        max_low_extension = max(max_low_extension, extension)

    # Validate extensions (too large)
    if max_high_extension > 20:
        high_sweep_invalid = True
    if max_low_extension > 20:
        low_sweep_invalid = True

    # Detect FVG (3 consecutive 5m candles)
    # NOTE: Sweep extensions tracked PROGRESSIVELY — FVG can only
    # use sweeps that occurred BEFORE it in time (no look-ahead)
    fvg = detect_fvg(candle, candle-1, candle-2)

    if not fvg.valid:
        continue

    # Entry cap: Candle C must close before 03:00 NY
    if candle.close_time >= "03:00 AM NY":
        continue

    # Check Candle B body overlaps Asia range (intention to return)
    b_body_top = max(fvg.candle_B.open, fvg.candle_B.close)
    b_body_bottom = min(fvg.candle_B.open, fvg.candle_B.close)
    if b_body_top <= asia_low or b_body_bottom >= asia_high:
        continue  # Candle B entirely outside range — no intention to return

    # Check Candle C re-acceptance (close strictly inside range)
    if not (asia_low < candle.close < asia_high):
        continue

    # Calculate trade parameters
    if fvg.direction == "bullish":
        if max_low_extension < 2 or low_sweep_invalid:
            continue  # No valid low sweep
        sweep_extreme = get_min_price_below(asia_low)
        sl = sweep_extreme - 0.00005
        tp = asia_high - 0.00005    # 0.5 pip conservative (inward)
        direction = "BUY"
    else:
        if max_high_extension < 2 or high_sweep_invalid:
            continue  # No valid high sweep
        sweep_extreme = get_max_price_above(asia_high)
        sl = sweep_extreme + 0.00005
        tp = asia_low + 0.00005     # 0.5 pip conservative (inward)
        direction = "SELL"

    # Pre-entry R:R validation
    estimated_entry = candle.close
    risk = abs(estimated_entry - sl)
    reward = abs(tp - estimated_entry)
    rr = reward / risk

    if rr < 1.4:
        continue  # Insufficient R:R, keep scanning

    # Execute trade
    entry = submit_market_order(direction)
    position_size = calculate_position(account_equity, risk)

    place_sl(sl)
    place_tp(tp)

    session_trade_taken = True

    log_trade({
        'entry': entry,
        'sl': sl,
        'tp': tp,
        'risk': risk,
        'rr': rr,
        'direction': direction
    })
```

---

## 15. PERFORMANCE (5-Year Backtest, v1.3 Locked Parameters)

```yaml
period: 2021-01-04 to 2026-03-27 (5.25 years)
total_trades: 159
win_rate: 42.1%
avg_r_winners: +2.28R
avg_r_losers: -1.00R
expectancy: +0.383R per trade
total_r: +60.87R
annualized_return: ~11.8% (compounded at 1% risk)
trades_per_month: 2.6
positive_years: 5/5 (every year positive)
```

**Annual breakdown:**
- 2021: +10.41R (32 trades, 38% WR)
- 2022: +2.65R (24 trades, 38% WR)
- 2023: +21.96R (32 trades, 53% WR)
- 2024: +2.22R (25 trades, 36% WR)
- 2025: +18.90R (36 trades, 44% WR)
- 2026 Q1: +4.73R (10 trades, 40% WR)

---

## 16. FLAGGED ITEMS FOR FUTURE DEFINITION

See separate document: `asia_range_scalp_strategy_FLAGGED.md`

1. Position sizing formula (pair-specific, account currency handling)
2. Risk limits (consecutive losses, weekly drawdown)
3. Performance metrics (backtest-derived)
4. Trade management (breakeven, partials, trailing)
5. Setup completion deadline grace period

---

## 17. DECISION LOG

| Decision Point | Chosen Approach | Rationale |
|----------------|-----------------|-----------|
| FVG minimum gap | Fixed pips (≥0.5, v1.3) | Walk-forward validated — 1.0p too restrictive, filtered profitable setups |
| FVG untouched area | Continuous segment ≥0.5 pip | Partial fill valid, full fill invalid |
| FVG Candle B position | Body must overlap Asia range | Intention to return — filters FVGs forming entirely outside range |
| Entry timing | Immediate at Candle C close | Fast scalps, no retrace wait |
| Entry price | Next available tick | Realistic execution |
| Candle C boundary | Strictly inside only | Boundary = liquidity, not acceptance |
| Asia range measurement | Wick-to-wick | Standard range definition |
| Sweep extension minimum | 2 pips (v1.3, walk-forward validated) | Sub-2-pip extensions are noise; 3p was too restrictive per Olya review |
| Sweep extension maximum | 20 pips | Beyond 20 = breakout, not sweep |
| Extension tracking | Per direction (separate) | High/low independent validation |
| Re-acceptance | Required before FVG entry | Confirms sweep rejection |
| SL placement | Sweep extreme ± 0.5 pip buffer | Logical invalidation point |
| TP target | Opposite boundary wick - 0.5 pip inward | Conservative fill — price may wick near but miss exact boundary |
| R:R validation | Pre-entry check, ≥1.4R (was 1.5R in v1.0) | Slightly wider net while maintaining positive expectancy filter |
| Max trades | 1 per session | Preserve edge, avoid overtrading |
| First setup priority | First complete valid setup | Early-session liquidity edge |
| Timeout | Removed (v1.2) — purely mechanical SL/TP | Set-and-forget; risk removal deferred to future refinement |
| Entry cap | 03:00 NY (v1.3) — no FVG entry after 03:00 | 03:xx hour is only negative hour (-1.05R); walk-forward validated |
| Temporal ordering | Sweep must precede FVG (v1.3) | Progressive sweep tracking prevents look-ahead bias |
| iFVG | Removed from strategy | Complexity reduction |

---

## DOCUMENT STATUS

**Version:** 1.3
**Status:** LOCKED (walk-forward validated, 5-year backtested)
**Machine executable:** Yes (pending implementation of flagged items)
**Last updated:** March 28, 2026
**Supersedes:** asia_range_scalp_strategy_FINAL v1.0 (January 20, 2026)

**Core logic:** 100% defined ✓
**Edge cases:** Resolved ✓
**Walk-forward validated:** ✓ (Apr-Sep 2025 train / Oct-Mar 2026 val)
**5-year backtested:** ✓ (+60.87R, positive every year)
**Gaps:** None (core strategy)
**Flagged items:** 5 (see separate document)

---

**END OF STRATEGY DOCUMENTATION**
