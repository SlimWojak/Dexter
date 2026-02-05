# LAYER 0 — HTF CONTEXT (WEEKLY → DAILY)
## D15MB Strategy - Machine-Executable Specification
## Version: 4.1 FINAL (With 9 Gaps Resolved)
## Date: January 23, 2026

---

## ARCHITECTURE POSITION

```
LAYER 0: HTF Context (Weekly update + Daily update)
         ↓ provides environment constraints
LAYER 1: Daily State Engine (Daily update)
         ↓ classifies current market phase
LAYER 2: Operating Range Selection (Session start)
         ↓ determines tradeable space
LAYER 3: Intraday Execution (Real-time)
         ↓ executes when conditions align
```

**Layer 0 Purpose:** Define the environment the machine is allowed to operate in.

---

## GLOBAL RULE (NON-NEGOTIABLE)

```python
# STRUCTURE EXISTENCE HIERARCHY

Structure exists ONLY after MSS.
Swings are created BY MSS.
Ranges are created BY MSS.  # ✅ UPDATED (GAP 2: BOS = MSS)

If any step is missing → system WAITS.
```

**Consequence:** Some periods will have NO STRUCTURE = NO TRADING. This is CORRECT behavior.

---

## EXECUTION TIMING

| Component | Frequency | Run Time | Purpose |
|---|---|---|---|
| **Weekly Context** | Once per week | Sunday 17:00 NY | Macro permission, objectives, limits |
| **Daily Analysis** | Once per day | 00:00 NY (midnight) | Component detection (ranges, PDAs, liquidity) |
| **Daily Bias** | Once per day | 00:00 NY (after analysis) | Answer 3 questions, set trade bias |

**Data Required:**

- Weekly candles: 52+ weeks
- Daily candles: 90+ days

---

## A. WEEKLY CONTEXT (MACRO PERMISSION ONLY)

### A1 — Weekly MSS Detection

**✅ UPDATED (GAP 1: Bootstrap, GAP 3: Displacement, GAP 4: FVG)**

```python
def detect_weekly_mss(weekly_df):
    """
    MSS Requirements (ALL must be true):
    1. Close beyond prior MSS-defined swing
    2. Displacement occurred (QUALITATIVE - no pip thresholds)
    3. FVG created OR respected (UNIVERSAL definition)
    
    Returns:
        weekly_mss: {
            'exists': bool,
            'direction': 'bullish' | 'bearish' | None,
            'swing_high': float,
            'swing_low': float,
            'date': datetime
        }
    """
    
    # ✅ GAP 1: BOOTSTRAP LOGIC
    # For FIRST MSS: Use PDH/PDL/PWH/PWL as initial boundaries ONLY
    if no_prior_mss_exists():
        return detect_first_weekly_mss(weekly_df)
    
    # Normal MSS detection (after bootstrap)
    prior_swing = get_swing_from_last_mss()
    current_candle = weekly_df.iloc[-1]
    
    # Condition 1: Close beyond swing
    bullish = current_candle.close > prior_swing['swing_high']
    bearish = current_candle.close < prior_swing['swing_low']
    
    if not (bullish or bearish):
        return {'exists': False, 'direction': None}
    
    # ✅ GAP 3: DISPLACEMENT (QUALITATIVE - NO PIP THRESHOLDS)
    recent_candles = weekly_df.iloc[-10:]
    displacement = check_displacement_qualitative(
        candles=recent_candles,
        balance_level=prior_swing['swing_high'] if bullish else prior_swing['swing_low']
    )
    
    if not displacement:
        return {'exists': False, 'direction': None}
    
    # ✅ GAP 4: FVG (UNIVERSAL - SAME FOR ALL TIMEFRAMES)
    fvg_created = check_fvg_created_universal(recent_candles[-3:])
    fvg_respected = check_fvg_respected_universal(recent_candles, existing_fvgs)
    
    if not (fvg_created or fvg_respected):
        return {'exists': False, 'direction': None}
    
    # MSS CONFIRMED ✅
    return {
        'exists': True,
        'direction': 'bullish' if bullish else 'bearish',
        'swing_high': current_candle.high if bullish else prior_swing['swing_high'],
        'swing_low': prior_swing['swing_low'] if bullish else current_candle.low,
        'date': current_candle.date
    }
```

### A1.1 — Bootstrap Logic (First MSS)

**✅ NEW SECTION (GAP 1)**

```python
def detect_first_weekly_mss(weekly_df):
    """
    Bootstrap: Detect FIRST MSS when NO_STRUCTURE state.
    
    CRITICAL: Initial boundaries = PDH/PDL/PWH/PWL ONLY
    NO arbitrary levels, NO recent swings, NO other reference points.
    """
    
    # ✅ GAP 1: ONLY THESE 4 BOUNDARIES VALID FOR BOOTSTRAP
    boundaries = {
        'pdh': get_previous_day_high(weekly_df),
        'pdl': get_previous_day_low(weekly_df),
        'pwh': get_previous_week_high(weekly_df),
        'pwl': get_previous_week_low(weekly_df)
    }
    
    current_candle = weekly_df.iloc[-1]
    recent_candles = weekly_df.iloc[-10:]
    
    # Check if price closed beyond any boundary
    boundary_broken = None
    direction = None
    
    if current_candle.close > boundaries['pdh']:
        boundary_broken = boundaries['pdh']
        direction = 'bullish'
    elif current_candle.close > boundaries['pwh']:
        boundary_broken = boundaries['pwh']
        direction = 'bullish'
    elif current_candle.close < boundaries['pdl']:
        boundary_broken = boundaries['pdl']
        direction = 'bearish'
    elif current_candle.close < boundaries['pwl']:
        boundary_broken = boundaries['pwl']
        direction = 'bearish'
    else:
        return {'exists': False, 'direction': None}
    
    # ✅ GAP 3: Check displacement (QUALITATIVE)
    displacement = check_displacement_qualitative(
        candles=recent_candles,
        balance_level=boundary_broken
    )
    
    if not displacement:
        return {'exists': False, 'direction': None}
    
    # ✅ GAP 4: Check FVG (UNIVERSAL)
    fvg_created = check_fvg_created_universal(recent_candles[-3:])
    fvg_respected = check_fvg_respected_universal(recent_candles, [])
    
    if not (fvg_created or fvg_respected):
        return {'exists': False, 'direction': None}
    
    # FIRST MSS CONFIRMED ✅
    return {
        'exists': True,
        'first_mss': True,
        'direction': direction,
        'swing_high': current_candle.high if direction == 'bullish' else boundary_broken,
        'swing_low': boundary_broken if direction == 'bullish' else current_candle.low,
        'date': current_candle.date,
        'bootstrap_boundary': boundary_broken
    }
```

### A1.2 — Displacement Definition (Qualitative)

**✅ NEW SECTION (GAP 3)**

```python
def check_displacement_qualitative(candles, balance_level):
    """
    ✅ GAP 3 RESOLUTION: Displacement is QUALITATIVE (NO pip thresholds)
    
    Displacement confirmed when ALL of:
    1. Price forcefully EXITS prior balance
    2. Removes structure of that timeframe
    3. Leaves imbalance (FVG created OR respected)
    4. One-sided intent (strong bodies, no hesitation)
    5. No rotation back into balance
    
    CRITICAL: NO pip thresholds. NO fixed distances.
    Universal across ALL timeframes (Weekly, Daily, H4, H1, 15m, 5m).
    """
    
    # 1. Forceful exit from balance
    exited_balance = check_forceful_exit(candles, balance_level)
    
    if not exited_balance:
        return False
    
    # 2. Removed structure
    broke_structure = check_structure_removal(candles)
    
    if not broke_structure:
        return False
    
    # 3. Left imbalance
    fvg_created = check_fvg_created_universal(candles[-3:])
    fvg_respected = check_fvg_respected_universal(candles, existing_fvgs=[])
    left_imbalance = (fvg_created or fvg_respected)
    
    if not left_imbalance:
        return False
    
    # 4. One-sided intent
    avg_body_pct = calculate_avg_body_percentage(candles)
    strong_bodies = (avg_body_pct > 0.70)
    
    one_directional = check_no_opposing_candles(candles)
    
    one_sided = (strong_bodies and one_directional)
    
    if not one_sided:
        return False
    
    # 5. No rotation back into balance
    no_rotation = not check_price_returned_to_balance(candles, balance_level)
    
    if not no_rotation:
        return False
    
    # ALL CONDITIONS MET ✅
    return True
```

### A1.3 — FVG Detection (Universal)

**✅ NEW SECTION (GAP 4)**

```python
def check_fvg_created_universal(candles):
    """
    ✅ GAP 4 RESOLUTION: FVG detection is UNIVERSAL across all timeframes
    
    Bullish FVG: Candle A high < Candle C low
    Bearish FVG: Candle A low > Candle C high
    
    That's it. NO pip thresholds. NO body checks. NO timeframe scaling.
    """
    
    if len(candles) < 3:
        return False
    
    candle_A = candles.iloc[-3]  # First
    candle_B = candles.iloc[-2]  # Middle (not checked)
    candle_C = candles.iloc[-1]  # Third (current)
    
    # Bullish FVG
    if candle_A.high < candle_C.low:
        return {
            'exists': True,
            'direction': 'bullish',
            'top': candle_C.low,
            'bottom': candle_A.high,
            'mid': (candle_C.low + candle_A.high) / 2
        }
    
    # Bearish FVG
    if candle_A.low > candle_C.high:
        return {
            'exists': True,
            'direction': 'bearish',
            'top': candle_A.low,
            'bottom': candle_C.high,
            'mid': (candle_A.low + candle_C.high) / 2
        }
    
    return False


def check_fvg_respected_universal(candles, existing_fvgs):
    """
    ✅ GAP 4 RESOLUTION: FVG respect is UNIVERSAL across all timeframes
    
    Same 5 conditions for Weekly, Daily, H4, H1, 15m, 5m:
    1. Shallow return (≤50% of FVG depth)
    2. Corrective character (not impulsive)
    3. No acceptance (no rotation)
    4. Continuation (resumes direction)
    5. Structure intact
    
    ONLY difference by timeframe: Impact/Weight (macro → execution)
    """
    
    if not existing_fvgs:
        return False
    
    for fvg in existing_fvgs:
        shallow = check_shallow_return(candles, fvg)
        corrective = check_corrective_character(candles, fvg)
        no_rotation = check_no_acceptance(candles, fvg)
        continuation = check_continuation(candles, fvg)
        intact = check_structure_intact(candles, fvg)
        
        if shallow and corrective and no_rotation and continuation and intact:
            return True
    
    return False
```

### A2 — Weekly Range (IF MSS EXISTS)

**✅ UPDATED (GAP 2: BOS → MSS terminology)**

```python
def define_weekly_range(weekly_mss_history):
    """
    ✅ GAP 2 RESOLUTION: BOS = MSS (same thing)
    Use "MSS" terminology ONLY. Delete all "BOS" references.
    
    Weekly range defined FROM MSS boundaries.
    Range = last bullish MSS low → last bearish MSS high
    """
    
    if not weekly_mss_history:
        return None  # NO_STRUCTURE state
    
    # Find last bullish MSS (provides low boundary)
    last_bullish_mss = get_last_mss(weekly_mss_history, direction='bullish')
    
    # Find last bearish MSS (provides high boundary)
    last_bearish_mss = get_last_mss(weekly_mss_history, direction='bearish')
    
    if last_bullish_mss and last_bearish_mss:
        return {
            'high': last_bearish_mss['swing_high'],
            'low': last_bullish_mss['swing_low'],
            'equilibrium': (last_bearish_mss['swing_high'] + 
                           last_bullish_mss['swing_low']) / 2,
            'method': 'mss_boundaries',
            'created_by': [last_bullish_mss['date'], last_bearish_mss['date']]
        }
    
    if last_bullish_mss:
        return {
            'high': last_bullish_mss['swing_high'],
            'low': last_bullish_mss['swing_low'],
            'equilibrium': (last_bullish_mss['swing_high'] + 
                           last_bullish_mss['swing_low']) / 2,
            'method': 'single_mss'
        }
    
    if last_bearish_mss:
        return {
            'high': last_bearish_mss['swing_high'],
            'low': last_bearish_mss['swing_low'],
            'equilibrium': (last_bearish_mss['swing_high'] + 
                           last_bearish_mss['swing_low']) / 2,
            'method': 'single_mss'
        }
    
    return None
```

### A3 — Weekly Role (STRICT LIMITATIONS)

**Weekly is used ONLY for:**

1. Define major external objectives (PWH / PWL)
2. Define macro PDAs (Weekly FVG / OB)
3. Define expansion limits

**Weekly is NOT used for:**

- ❌ Execution ranges
- ❌ Daily bias overrides
- ❌ Premium/discount decisions for entries
- ❌ Intraday trading decisions

```python
weekly_context = {
    'pwh': previous_week_high,
    'pwl': previous_week_low,
    'weekly_fvgs': [...],
    'weekly_obs': [...],
    'expansion_limits': {
        'max_high': weekly_range_high,
        'max_low': weekly_range_low
    }
}
```

---

## B. DAILY CONTEXT (ANCHOR & DIRECTION)

### B1 — Daily MSS Detection

**✅ UPDATED (ALL 4 GAPS)**

```python
def detect_daily_mss(daily_df):
    """
    Same MSS logic as Weekly:
    1. Close beyond prior MSS-defined swing
    2. Displacement (QUALITATIVE - no pip thresholds)
    3. FVG created OR respected (UNIVERSAL definition)
    
    ✅ GAP 1: Bootstrap uses PDH/PDL/PWH/PWL only
    ✅ GAP 3: Displacement is qualitative (same as Weekly)
    ✅ GAP 4: FVG detection is universal (same as Weekly)
    """
    
    if no_prior_daily_mss():
        return detect_first_daily_mss(daily_df)
    
    prior_swing = get_swing_from_last_daily_mss()
    current_candle = daily_df.iloc[-1]
    recent_candles = daily_df.iloc[-10:]
    
    bullish = current_candle.close > prior_swing['swing_high']
    bearish = current_candle.close < prior_swing['swing_low']
    
    if not (bullish or bearish):
        return {'exists': False, 'direction': None}
    
    displacement = check_displacement_qualitative(
        candles=recent_candles,
        balance_level=prior_swing['swing_high'] if bullish else prior_swing['swing_low']
    )
    
    if not displacement:
        return {'exists': False, 'direction': None}
    
    fvg_created = check_fvg_created_universal(recent_candles[-3:])
    fvg_respected = check_fvg_respected_universal(recent_candles, existing_fvgs)
    
    if not (fvg_created or fvg_respected):
        return {'exists': False, 'direction': None}
    
    return {
        'exists': True,
        'direction': 'bullish' if bullish else 'bearish',
        'swing_high': current_candle.high if bullish else prior_swing['swing_high'],
        'swing_low': prior_swing['swing_low'] if bullish else current_candle.low,
        'date': current_candle.date
    }
```

### B2 — Daily Structure (Order Flow)

```python
def determine_daily_order_flow(daily_swings):
    """
    Order Flow = HH/HL/LH/LL pattern
    
    Bullish: Higher High + Higher Low (HH + HL)
    Bearish: Lower High + Lower Low (LH + LL)
    Mixed: Conflicting (HH + LL or LH + HL)
    Neutral: Not enough swings
    
    Swings ONLY from MSS events (NOT arbitrary peaks/troughs)
    """
    
    if len(daily_swings) < 2:
        return 'neutral'
    
    last_swing = daily_swings[-1]
    prev_swing = daily_swings[-2]
    
    is_hh = last_swing.high > prev_swing.high
    is_lh = last_swing.high < prev_swing.high
    is_hl = last_swing.low > prev_swing.low
    is_ll = last_swing.low < prev_swing.low
    
    if is_hh and is_hl:
        return 'bullish'
    elif is_lh and is_ll:
        return 'bearish'
    else:
        return 'mixed'
```

### B3 — Daily Dealing Range (ANCHOR RANGE)

**✅ UPDATED (GAP 2: MSS terminology, GAP 5: Validated swings)**

```python
def define_daily_dealing_range(daily_mss_history, daily_df):
    """
    ✅ GAP 2 RESOLUTION: Range from MSS boundaries (NOT "BOS")
    ✅ GAP 5 RESOLUTION: Priority hierarchy updated
    
    Priority:
    1. Equal Highs/Lows (Liquidity) - HIGHEST
    2. External PDH/PDL/PWH/PWL (Liquidity)
    3. MSS Swings (Directional intent)
    4. Validated Swings (Local reaction) - LOWEST
    5. NEVER: Arbitrary time windows
    """
    
    # Priority 1: Equal Highs/Lows
    equal_highs = detect_equal_highs(daily_df, tolerance_pips=10, min_touches=3)
    equal_lows = detect_equal_lows(daily_df, tolerance_pips=10, min_touches=3)
    
    if equal_highs and equal_lows:
        return {
            'high': max(equal_highs),
            'low': min(equal_lows),
            'equilibrium': (max(equal_highs) + min(equal_lows)) / 2,
            'method': 'liquidity_pools',
            'priority': 1
        }
    
    # Priority 2: External PDH/PDL/PWH/PWL
    pdh = get_pdh(daily_df)
    pdl = get_pdl(daily_df)
    pwh = get_pwh(daily_df)
    pwl = get_pwl(daily_df)
    
    ipda = get_ipda_ranges(daily_df)
    
    if pdh and pdl:
        return {
            'high': pdh,
            'low': pdl,
            'equilibrium': (pdh + pdl) / 2,
            'method': 'external_liquidity_pdh_pdl',
            'priority': 2
        }
    
    if pwh and pwl:
        return {
            'high': pwh,
            'low': pwl,
            'equilibrium': (pwh + pwl) / 2,
            'method': 'external_liquidity_pwh_pwl',
            'priority': 2
        }
    
    # Priority 3: MSS Swings
    range_from_mss = define_range_from_mss_history(daily_mss_history)
    
    if range_from_mss:
        range_from_mss['priority'] = 3
        return range_from_mss
    
    # Priority 4: Validated Swings
    validated_swings = find_validated_swings(daily_df)
    
    if validated_swings:
        return {
            'high': validated_swings['high'],
            'low': validated_swings['low'],
            'equilibrium': (validated_swings['high'] + validated_swings['low']) / 2,
            'method': 'validated_swings',
            'priority': 4
        }
    
    return None
```

### B3.1 — Validated Swings Definition

**✅ NEW SECTION (GAP 5)**

```python
def find_validated_swings(daily_df):
    """
    ✅ GAP 5 RESOLUTION: Validated swings definition
    
    Process:
    1. Identify swing candidates (local pivots, lookback=3)
    2. Check if price touched each candidate
    3. Check for IMMEDIATE displacement reaction (1-3 candles max)
    4. Return highest validated high + lowest validated low
    
    CRITICAL: 
    - "If a level matters, algorithms respond instantly"
    - Delayed reactions = balance, not intent
    - Validation uses SAME displacement logic as MSS
    """
    
    swing_highs, swing_lows = identify_swing_candidates(daily_df, lookback=3)
    
    validated_highs = []
    validated_lows = []
    
    for swing_high in swing_highs:
        subsequent = daily_df.iloc[swing_high['index']+1:]
        
        if validate_swing_immediate(swing_high, subsequent):
            validated_highs.append(swing_high['price'])
    
    for swing_low in swing_lows:
        subsequent = daily_df.iloc[swing_low['index']+1:]
        
        if validate_swing_immediate(swing_low, subsequent):
            validated_lows.append(swing_low['price'])
    
    if validated_highs and validated_lows:
        return {
            'high': max(validated_highs),
            'low': min(validated_lows)
        }
    
    return None


def identify_swing_candidates(df, lookback=3):
    """
    Swing candidates = local pivots ONLY.
    
    Swing High: high[i] > all highs in [i-lookback, i+lookback]
    Swing Low: low[i] < all lows in [i-lookback, i+lookback]
    
    UNVALIDATED until price reacts with displacement.
    """
    
    swing_highs = []
    swing_lows = []
    
    for i in range(lookback, len(df) - lookback):
        if df['high'].iloc[i] == df['high'].iloc[i-lookback:i+lookback+1].max():
            swing_highs.append({
                'price': df['high'].iloc[i],
                'index': i,
                'date': df.index[i],
                'validated': False
            })
        
        if df['low'].iloc[i] == df['low'].iloc[i-lookback:i+lookback+1].min():
            swing_lows.append({
                'price': df['low'].iloc[i],
                'index': i,
                'date': df.index[i],
                'validated': False
            })
    
    return swing_highs, swing_lows


def validate_swing_immediate(swing_candidate, subsequent_candles):
    """
    Swing validated when price reacts from it with:
    1. Displacement (qualitative, no pips)
    2. Removes structure
    3. Leaves imbalance (FVG created)
    
    CRITICAL: Reaction must be IMMEDIATE (1-3 candles after touch)
    """
    
    touched = False
    touch_index = None
    
    for i, candle in enumerate(subsequent_candles.itertuples()):
        if swing_candidate['type'] == 'high':
            if candle.high >= swing_candidate['price']:
                touched = True
                touch_index = i
                break
        else:
            if candle.low <= swing_candidate['price']:
                touched = True
                touch_index = i
                break
    
    if not touched:
        return False
    
    max_reaction_window = 3
    reaction_candles = subsequent_candles.iloc[touch_index:touch_index+max_reaction_window+5]
    
    for start in range(min(max_reaction_window, len(reaction_candles))):
        if start + 5 <= len(reaction_candles):
            displacement_candles = reaction_candles.iloc[start:start+5]
            
            if check_displacement_qualitative(displacement_candles, swing_candidate['price']):
                return True
    
    return False


### B3.2 — PDH/PDL/PWH/PWL Definition

**✅ NEW SECTION (GAP 9)**

```python
def get_pdh_pdl_forex_day():
    """
    ✅ GAP 9 RESOLUTION: PDH/PDL uses Forex Trading Day (17:00 NY)
    
    CRITICAL: Do NOT use midnight (00:00) boundaries.
    
    Forex Day: 17:00 NY → 17:00 NY next day (local time, DST-adjusted)
    PDH: Highest WICK in prior completed Forex day
    PDL: Lowest WICK in prior completed Forex day
    
    DST Handling: Always use NY local time (America/New_York)
    - EDT in summer (UTC-4)
    - EST in winter (UTC-5)
    - ⛔ Do NOT hardcode UTC offsets
    """
    
    # Get current time in NY timezone
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.now(ny_tz)
    
    # Identify last completed Forex day
    # Forex day starts at 17:00 NY
    forex_day_start_hour = 17
    
    if now_ny.hour < forex_day_start_hour:
        # Before 17:00 - previous day's 17:00 to today's 17:00 not complete
        # Use the day before that
        end_time = now_ny.replace(hour=forex_day_start_hour, minute=0, second=0)
        start_time = end_time - timedelta(days=1)
    else:
        # After 17:00 - today's 17:00 to tomorrow's 17:00 is current
        # Use yesterday's 17:00 to today's 17:00
        start_time = now_ny.replace(hour=forex_day_start_hour, minute=0, second=0) - timedelta(days=1)
        end_time = now_ny.replace(hour=forex_day_start_hour, minute=0, second=0)
    
    # Get candles in that period
    day_candles = get_candles_in_range(start_time, end_time)
    
    # PDH = highest wick (high) in that period
    pdh = day_candles['high'].max()
    
    # PDL = lowest wick (low) in that period
    pdl = day_candles['low'].min()
    
    return {
        'pdh': pdh,
        'pdl': pdl,
        'forex_day_start': start_time,
        'forex_day_end': end_time
    }


def get_pwh_pwl_forex_week():
    """
    ✅ GAP 9 RESOLUTION: PWH/PWL uses Forex Trading Week
    
    Forex Week: Sunday 17:00 NY → Sunday 17:00 NY next week
    PWH: Highest WICK in prior completed Forex week
    PWL: Lowest WICK in prior completed Forex week
    
    Same DST handling as daily.
    """
    
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.now(ny_tz)
    
    # Find last completed Forex week
    # Forex week starts Sunday 17:00 NY
    days_since_sunday = now_ny.weekday() + 1  # Monday=0, so +1 to get days since Sunday
    if days_since_sunday == 7:
        days_since_sunday = 0
    
    this_sunday = now_ny - timedelta(days=days_since_sunday)
    this_sunday = this_sunday.replace(hour=17, minute=0, second=0)
    
    if now_ny < this_sunday:
        # Current week not complete
        end_time = this_sunday
        start_time = this_sunday - timedelta(days=7)
    else:
        # Current week started
        end_time = this_sunday
        start_time = this_sunday - timedelta(days=7)
    
    # Get candles in that period
    week_candles = get_candles_in_range(start_time, end_time)
    
    # PWH = highest wick in that period
    pwh = week_candles['high'].max()
    
    # PWL = lowest wick in that period
    pwl = week_candles['low'].min()
    
    return {
        'pwh': pwh,
        'pwl': pwl,
        'forex_week_start': start_time,
        'forex_week_end': end_time
    }
```

**PDH/PDL Critical Rules:**
- ⛔ Do NOT use midnight (00:00) boundaries
- ⛔ Do NOT use candle closes (only wicks)
- ⛔ Do NOT hardcode UTC offsets
- ✅ Always use 17:00 NY boundaries
- ✅ Always use wicks (extremes) — liquidity sits at wick extremes
- ✅ Always use NY local time (auto DST)


def get_ipda_ranges(df):
    """
    ✅ GAP 5: IPDA (Interbank Price Delivery Algorithm) data ranges
    
    ICT-defined ranges where institutional algorithms reference data:
    - 20 bars (short-term)
    - 40 bars (medium-term)
    - 60 bars (long-term)
    
    USED ONLY FOR:
    1. Bootstrap context (NO_STRUCTURE state)
    2. Locating external liquidity (PDH/PDL, PWH/PWL)
    3. Bounding where structure may form
    """
    
    return {
        'ipda_20': {
            'high': df['high'].iloc[-20:].max(),
            'low': df['low'].iloc[-20:].min(),
            'range': 'short_term'
        },
        'ipda_40': {
            'high': df['high'].iloc[-40:].max(),
            'low': df['low'].iloc[-40:].min(),
            'range': 'medium_term'
        },
        'ipda_60': {
            'high': df['high'].iloc[-60:].max(),
            'low': df['low'].iloc[-60:].min(),
            'range': 'long_term'
        }
    }
```

### B4 — Premium / Discount State

```python
def calculate_premium_discount(current_price, daily_range):
    """
    Premium = above 50% of STRUCTURAL range
    Discount = below 50% of STRUCTURAL range
    Equilibrium = at 50% (NO TRADE)
    """
    
    if daily_range is None:
        return 'unknown'
    
    eq = daily_range['equilibrium']
    
    if current_price > eq:
        return 'premium'
    elif current_price < eq:
        return 'discount'
    else:
        return 'equilibrium'
```

### B4.5 — MMXM Identification (Manipulation Market Maker Move)

**✅ NEW SECTION (GAP 6)**

#### Core Principle

```python
# MMXM = Failed auction structure (NOT rigid 3-phase template)
# Recognition: contextual and structural
# Pattern: Consolidation → Manipulation → Rejection → Reversal
```

#### Timeframe Priority (Weighted Hierarchy)

```python
MMXM_PRIORITY = {
    'daily': {'weight': 1, 'role': 'macro_intent', 'usage': 'primary_targets'},
    'h4':    {'weight': 2, 'role': 'htf_rebalance', 'usage': 'secondary_targets'},
    'h1':    {'weight': 3, 'role': 'execution_only', 'usage': 'entry_timing'}
}

# CRITICAL: Higher TF ALWAYS overrides lower TF
```

#### Lookback Window (STRICT)

```python
def get_mmxm_lookback_start(daily_mss_history):
    """
    MMXM valid ONLY after last Daily MSS.
    
    CRITICAL:
    - Ignore ALL MMXM before last MSS
    - MSS resets narrative
    """
    last_mss = get_last_mss(daily_mss_history)
    return last_mss['date'] if last_mss else None
```

#### Two MMXM Roles (CRITICAL DISTINCTION)

**TYPE 1: MMXM as MANIPULATION (Origin)**

```python
def detect_mmxm_manipulation(df):
    """
    Trading AWAY from MMXM.
    
    ALL REQUIRED:
    1. Liquidity sweep (PDH/PDL, swing, equal H/L)
    2. Failed auction (no acceptance beyond level)
    3. Displacement away from sweep
    4. FVG present
    5. Structural consequence (MSS or rejection)
    """
    
    sweep = detect_liquidity_sweep(df)
    if not sweep: return None
    
    failed_auction = not price_accepted_beyond(df, sweep['level'])
    if not failed_auction: return None
    
    displacement = check_displacement_qualitative(df, sweep['level'])
    if not displacement: return None
    
    fvg = check_fvg_created_universal(df[-3:])
    if not fvg: return None
    
    structural = check_structural_consequence(df)
    if not structural: return None
    
    return {
        'type': 'manipulation',
        'mmxm_extreme': sweep['extreme'],
        'trade_direction': 'away_from_mmxm',
        'role': 'origin'
    }
```

**TYPE 2: MMXM as TARGET (Objective)**

```python
def validate_mmxm_target(mmxm, context):
    """
    Trading TOWARDS MMXM (original consolidation).
    
    KEY RULE:
    👉 MMXM does NOT need liquidity sweep on its boundary when TARGET.
    WHY: MMXM itself IS the liquidity pool.
    
    REQUIRED:
    1. MMXM exists post-Daily MSS
    2. Price in premium (shorts) OR discount (longs)
    3. HTF direction aligned
    4. Separate liquidity event occurred (NOT at MMXM)
    5. Displacement towards MMXM
    6. FVG supports move towards MMXM
    """
    
    if mmxm['date'] < context['last_mss_date']:
        return False
    
    if context['htf_direction'] == 'bearish':
        if context['current_price'] <= context['equilibrium']:
            return False
    else:
        if context['current_price'] >= context['equilibrium']:
            return False
    
    if mmxm['target_type'] == 'high' and context['htf_direction'] != 'bearish':
        return False
    if mmxm['target_type'] == 'low' and context['htf_direction'] != 'bullish':
        return False
    
    recent_sweep = context['recent_sweep']
    if not recent_sweep:
        return False
    if abs(recent_sweep['price'] - mmxm['price']) < 10:
        return False
    
    displacement_dir = context['displacement_direction']
    if mmxm['target_type'] == 'high' and displacement_dir != 'up':
        return False
    if mmxm['target_type'] == 'low' and displacement_dir != 'down':
        return False
    
    fvg = context['recent_fvg']
    if not fvg:
        return False
    if mmxm['target_type'] == 'high' and fvg['direction'] != 'bearish':
        return False
    if mmxm['target_type'] == 'low' and fvg['direction'] != 'bullish':
        return False
    
    return True
```

#### MMXM High/Low Definition

```python
def identify_mmxm_consolidation(df):
    """
    MMXM High/Low = ORIGINAL CONSOLIDATION boundaries.
    
    NOT manipulation extreme.
    NOT post-reversal extreme.
    
    The consolidation range IS the target.
    """
    
    for i in range(len(df) - 20):
        window = df.iloc[i:i+20]
        
        range_size = window['high'].max() - window['low'].min()
        atr = get_atr(df.iloc[:i+20])
        
        if range_size < (atr * 0.5):
            
            high_level = window['high'].max()
            low_level = window['low'].min()
            
            touches_high = count_level_touches(window, high_level, tolerance=5)
            touches_low = count_level_touches(window, low_level, tolerance=5)
            
            if touches_high >= 3 and touches_low >= 3:
                return {
                    'mmxm_high': high_level,
                    'mmxm_low': low_level,
                    'consolidation_start': i,
                    'consolidation_end': i + 20,
                    'range_size': range_size,
                    'type': 'original_consolidation'
                }
    
    return None
```

#### Complete MMXM Detection

```python
def detect_all_mmxm(daily_df, daily_mss_history):
    """
    Detect both MMXM types post-MSS only.
    """
    
    lookback_start = get_mmxm_lookback_start(daily_mss_history)
    if not lookback_start:
        return {'manipulation': [], 'targets': []}
    
    valid_df = daily_df[daily_df.index >= lookback_start]
    
    manipulation = []
    for i in range(len(valid_df)):
        pattern = detect_mmxm_manipulation(valid_df.iloc[:i+1])
        if pattern:
            pattern['date'] = valid_df.index[i]
            pattern['timeframe'] = 'daily'
            manipulation.append(pattern)
    
    targets = []
    for i in range(len(valid_df) - 20):
        consolidation = identify_mmxm_consolidation(valid_df.iloc[i:i+20])
        if consolidation:
            consolidation['date'] = valid_df.index[i]
            consolidation['timeframe'] = 'daily'
            targets.append(consolidation)
    
    return {'manipulation': manipulation, 'targets': targets}


def select_mmxm_target(mmxm_patterns, htf_direction, current_price, daily_range):
    """
    Select valid MMXM for trading.
    
    Priority:
    1. Daily MMXM (highest weight)
    2. Undelivered (price hasn't reached)
    3. HTF aligned
    4. Premium/Discount correct
    """
    
    context = {
        'htf_direction': htf_direction,
        'current_price': current_price,
        'equilibrium': daily_range['equilibrium'],
        'last_mss_date': get_last_mss_date(),
        'recent_sweep': get_recent_sweep(),
        'displacement_direction': get_displacement_direction(),
        'recent_fvg': get_recent_fvg()
    }
    
    valid = []
    
    for mmxm in mmxm_patterns['targets']:
        
        if htf_direction == 'bullish':
            if current_price >= mmxm['mmxm_high']:
                continue
        else:
            if current_price <= mmxm['mmxm_low']:
                continue
        
        if validate_mmxm_target(mmxm, context):
            valid.append(mmxm)
    
    if not valid:
        return None
    
    daily_mmxm = [m for m in valid if m.get('timeframe') == 'daily']
    if daily_mmxm:
        return daily_mmxm[0]
    
    valid.sort(key=lambda x: x['date'], reverse=True)
    return valid[0]
```

### B5 — Daily Objective Check (UPDATED WITH MMXM & LIQUIDITY STATUS)

**✅ UPDATED (GAP 6: MMXM as Priority 1, GAP 7: Liquidity status filtering)**

```python
def identify_daily_objectives(daily_mss, mmxm_patterns, liquidity_pools, pdas,
                              price_history, structural_events):
    """
    ✅ GAP 6: MMXM as Priority 1 target
    ✅ GAP 7: Filter by liquidity level status
    
    Valid objectives (in priority order):
    1. MMXM High / Low (original consolidation)
    2. PDH / PDL
    3. PWH / PWL
    4. Daily / Weekly FVG
    
    All targets filtered by delivery status:
    - NOT_DELIVERED (highest priority)
    - LIQUIDITY_RUN (valid)
    - DELIVERED_WITH_CONSEQUENCE (excluded)
    """
    
    if not daily_mss['exists']:
        return None
    
    direction = daily_mss['direction']
    current_price = get_current_price()
    daily_range = get_daily_range()
    
    all_liquidity_levels = []
    
    # PRIORITY 1: MMXM
    mmxm_target = select_mmxm_target(mmxm_patterns, direction, current_price, daily_range)
    
    if mmxm_target:
        if direction == 'bullish':
            all_liquidity_levels.append({
                'price': mmxm_target['mmxm_high'],
                'type': 'resistance',
                'category': 'mmxm_high',
                'priority': 1,
                'consolidation': mmxm_target
            })
        else:
            all_liquidity_levels.append({
                'price': mmxm_target['mmxm_low'],
                'type': 'support',
                'category': 'mmxm_low',
                'priority': 1,
                'consolidation': mmxm_target
            })
    
    # PRIORITY 2: PDH/PDL
    if direction == 'bullish':
        pdh = get_pdh()
        if current_price < pdh:
            all_liquidity_levels.append({
                'price': pdh,
                'type': 'resistance',
                'category': 'pdh',
                'priority': 2
            })
    else:
        pdl = get_pdl()
        if current_price > pdl:
            all_liquidity_levels.append({
                'price': pdl,
                'type': 'support',
                'category': 'pdl',
                'priority': 2
            })
    
    # PRIORITY 3: PWH/PWL
    if direction == 'bullish':
        pwh = get_pwh()
        if current_price < pwh:
            all_liquidity_levels.append({
                'price': pwh,
                'type': 'resistance',
                'category': 'pwh',
                'priority': 3
            })
    else:
        pwl = get_pwl()
        if current_price > pwl:
            all_liquidity_levels.append({
                'price': pwl,
                'type': 'support',
                'category': 'pwl',
                'priority': 3
            })
    
    # PRIORITY 4: Daily/Weekly FVG
    if direction == 'bullish':
        for fvg in daily_fvgs_up:
            if fvg['low'] > current_price:
                all_liquidity_levels.append({
                    'price': fvg['mid'],
                    'type': 'resistance',
                    'category': 'daily_fvg',
                    'priority': 4
                })
    else:
        for fvg in daily_fvgs_down:
            if fvg['high'] < current_price:
                all_liquidity_levels.append({
                    'price': fvg['mid'],
                    'type': 'support',
                    'category': 'daily_fvg',
                    'priority': 4
                })
    
    # ✅ GAP 7: Filter by delivery status
    valid_targets = filter_valid_liquidity_targets(
        all_liquidity_levels,
        price_history,
        structural_events
    )
    
    if not valid_targets:
        return None
    
    return valid_targets[0]
```

### B5.1 — Liquidity Level Status Classification

**✅ NEW SECTION (GAP 7)**

```python
def classify_liquidity_level_status(level, price_history, structural_events):
    """
    ✅ GAP 7 RESOLUTION: Three-state liquidity classification
    
    Returns: 'NOT_DELIVERED' | 'LIQUIDITY_RUN' | 'DELIVERED_WITH_CONSEQUENCE'
    """
    
    # STATE 1: NOT DELIVERED (Highest quality)
    if never_touched(level, price_history):
        return {
            'status': 'NOT_DELIVERED',
            'quality': 'highest',
            'valid_target': True,
            'reason': 'Liquidity fully intact, no information revealed'
        }
    
    # Check for structural consequences AT or FROM the level
    consequence = check_structural_consequence_at_level(level, structural_events)
    
    # STATE 3: DELIVERED WITH CONSEQUENCE (Invalid)
    if consequence['exists']:
        return {
            'status': 'DELIVERED_WITH_CONSEQUENCE',
            'quality': 'invalid',
            'valid_target': False,
            'reason': f"Liquidity fulfilled with consequence: {consequence['type']}",
            'consequence_details': consequence
        }
    
    # STATE 2: LIQUIDITY RUN (Valid target, delivery mode)
    return {
        'status': 'LIQUIDITY_RUN',
        'quality': 'valid',
        'valid_target': True,
        'reason': 'Approached/probed but no structural consequence, delivery incomplete'
    }


def never_touched(level, price_history):
    """
    Check if price has EVER traded at the level.
    """
    
    level_type = level['type']
    level_price = level['price']
    
    if level_type == 'resistance':
        for candle in price_history:
            if candle.high >= level_price:
                return False
        return True
    else:
        for candle in price_history:
            if candle.low <= level_price:
                return False
        return True


def check_structural_consequence_at_level(level, structural_events):
    """
    Check if ANY of these occurred AT or FROM the liquidity level:
    1. Displacement originates from the level
    2. MSS forms from the level
    3. FVG prints from the level
    4. Structure changes from that point
    """
    
    level_price = level['price']
    tolerance = 5  # pips
    
    # Check 1: Displacement from level
    for displacement_event in structural_events['displacements']:
        if price_near_level(displacement_event['origin'], level_price, tolerance):
            return {
                'exists': True,
                'type': 'displacement',
                'details': displacement_event
            }
    
    # Check 2: MSS from level
    for mss_event in structural_events['mss']:
        if price_near_level(mss_event['origin'], level_price, tolerance):
            return {
                'exists': True,
                'type': 'mss',
                'details': mss_event
            }
    
    # Check 3: FVG printed from level
    for fvg in structural_events['fvgs']:
        if level['type'] == 'resistance':
            if fvg['direction'] == 'bearish':
                if price_near_level(fvg['top'], level_price, tolerance):
                    return {
                        'exists': True,
                        'type': 'fvg',
                        'details': fvg
                    }
        else:
            if fvg['direction'] == 'bullish':
                if price_near_level(fvg['bottom'], level_price, tolerance):
                    return {
                        'exists': True,
                        'type': 'fvg',
                        'details': fvg
                    }
    
    # Check 4: Structure change from level
    for structure_change in structural_events['structure_changes']:
        if price_near_level(structure_change['price'], level_price, tolerance):
            return {
                'exists': True,
                'type': 'structure_change',
                'details': structure_change
            }
    
    return {'exists': False, 'type': None, 'details': None}


def filter_valid_liquidity_targets(all_liquidity_levels, price_history, structural_events):
    """
    Filter liquidity levels by delivery status.
    
    Priority:
    1. NOT_DELIVERED (highest quality)
    2. LIQUIDITY_RUN (valid, delivery ongoing)
    3. DELIVERED_WITH_CONSEQUENCE (invalid, removed)
    """
    
    valid_targets = []
    
    for level in all_liquidity_levels:
        status = classify_liquidity_level_status(level, price_history, structural_events)
        
        if status['valid_target']:
            level['status'] = status['status']
            level['quality'] = status['quality']
            valid_targets.append(level)
    
    valid_targets.sort(key=lambda x: 0 if x['status'] == 'NOT_DELIVERED' else 1)
    
    return valid_targets
```

### B6 — Daily PDAs (Price Delivery Arrays)

```python
def track_daily_pdas(daily_df):
    """
    Track all PDAs and their respect/broken status
    
    PDA types:
    - FVG (Fair Value Gap) - ✅ Universal definition (GAP 4)
    - OB (Order Block)
    - iFVG (Inversion FVG)
    - BPR (Balanced Price Range)
    """
    
    pdas = {
        'fvg_up': [],
        'fvg_down': [],
        'ob_bull': [],
        'ob_bear': [],
        'ifvg': [],
        'bpr': []
    }
    
    for i in range(3, len(daily_df)):
        candles = daily_df.iloc[i-2:i+1]
        fvg = check_fvg_created_universal(candles)
        
        if fvg:
            if fvg['direction'] == 'bullish':
                pdas['fvg_up'].append(fvg)
            else:
                pdas['fvg_down'].append(fvg)
    
    return pdas
```

### B7 — Daily Structure State

**✅ UPDATED (GAP 8: Post-expansion trigger)**

```python
def determine_daily_structure_state(daily_mss, daily_objective, price_history, structural_events):
    """
    ✅ GAP 8: Post-expansion triggered when objective delivered WITH displacement
    
    PRE_EXPANSION:
    - Daily objective not delivered (or delivered via grind)
    - System uses Daily range for premium/discount
    - Operating range = Daily
    
    POST_EXPANSION (REBALANCE MODE):
    - Daily objective delivered WITH displacement
    - System shifts to H4/H1 for rebalance opportunities
    - Daily used ONLY as direction filter
    - Operating range = H4/H1
    
    State is PERMANENT until new Daily MSS.
    """
    
    if not daily_mss or not daily_objective:
        return {
            'status': 'PRE_EXPANSION',
            'operating_range': 'use_daily',
            'reason': 'No MSS or objective defined'
        }
    
    post_expansion = check_post_expansion_status(
        daily_objective,
        price_history,
        structural_events
    )
    
    if post_expansion['is_post_expansion']:
        return {
            'status': 'POST_EXPANSION',
            'operating_range': 'shift_to_h4_h1',
            'delivery_timestamp': post_expansion['delivery_timestamp'],
            'delivery_type': 'impulsive',
            'reason': 'Daily objective delivered with displacement - REBALANCE MODE'
        }
    else:
        return {
            'status': 'PRE_EXPANSION',
            'operating_range': 'use_daily',
            'reason': post_expansion['reason']
        }
```

### B7.1 — Post-Expansion Detection

**✅ NEW SECTION (GAP 8)**

```python
def check_post_expansion_status(daily_objective, price_history, structural_events):
    """
    ✅ GAP 8 RESOLUTION: Post-expansion trigger
    
    Daily is POST-EXPANSION when:
    1. Daily external objective is delivered (price reached level)
    2. Delivery occurred WITH displacement (not grind)
    
    Once triggered, state is PERMANENT for that Daily MSS cycle.
    """
    
    if not daily_objective:
        return {
            'is_post_expansion': False,
            'reason': 'No Daily objective defined'
        }
    
    delivered = check_objective_delivered(daily_objective, price_history)
    
    if not delivered['status']:
        return {
            'is_post_expansion': False,
            'reason': 'Objective not yet delivered'
        }
    
    displacement = check_delivery_displacement(
        daily_objective,
        delivered['delivery_candles'],
        structural_events
    )
    
    if not displacement['valid']:
        return {
            'is_post_expansion': False,
            'reason': 'Objective delivered but without displacement (grind rejected)',
            'delivery_type': 'grind'
        }
    
    return {
        'is_post_expansion': True,
        'reason': 'Objective delivered with displacement',
        'delivery_timestamp': delivered['timestamp'],
        'delivery_type': 'impulsive',
        'displacement_details': displacement
    }


def check_objective_delivered(daily_objective, price_history):
    """
    Simple price check: has price traded at/beyond the objective level?
    """
    
    objective_price = daily_objective['price']
    objective_type = daily_objective['type']
    
    for i, candle in enumerate(price_history):
        
        if objective_type == 'resistance':
            if candle.high >= objective_price:
                return {
                    'status': True,
                    'timestamp': candle.timestamp,
                    'delivery_candle_index': i,
                    'delivery_candles': price_history[i:i+5]
                }
        
        else:
            if candle.low <= objective_price:
                return {
                    'status': True,
                    'timestamp': candle.timestamp,
                    'delivery_candle_index': i,
                    'delivery_candles': price_history[i:i+5]
                }
    
    return {
        'status': False,
        'timestamp': None,
        'delivery_candles': []
    }


def check_delivery_displacement(daily_objective, delivery_candles, structural_events):
    """
    Check if objective delivery occurred WITH displacement (impulsive move).
    
    VALID (Impulsive Delivery):
    ✅ Clear directional push
    ✅ Strong candle bodies (>70% of range)
    ✅ No slow overlap
    ✅ No balanced auction at the level
    ✅ FVG created during approach
    ✅ One-sided intent
    
    INVALID (Grind - Reject):
    ❌ Slow creep to level
    ❌ Multiple touches with hesitation
    ❌ Overlapping candles (>60% overlap)
    ❌ Balanced auction (equal bulls/bears)
    ❌ No FVG during approach
    """
    
    objective_price = daily_objective['price']
    
    displacement = check_displacement_qualitative(
        candles=delivery_candles,
        balance_level=objective_price
    )
    
    if displacement:
        return {
            'valid': True,
            'type': 'impulsive',
            'reason': 'Objective delivered with displacement'
        }
    
    grind_detected = check_grind_to_level(delivery_candles, objective_price)
    
    if grind_detected:
        return {
            'valid': False,
            'type': 'grind',
            'reason': 'Objective delivered via grind (slow overlap, no displacement)'
        }
    
    return {
        'valid': False,
        'type': 'unclear',
        'reason': 'Delivery type unclear'
    }


def check_grind_to_level(candles, level):
    """
    Detect if price ground slowly to the level (invalid delivery).
    
    Grind characteristics:
    - Small candle bodies (<50% of range)
    - Overlapping candles (>60% overlap)
    - Multiple touches with no strong push
    - No FVG created
    """
    
    total_body_pct = 0
    for candle in candles:
        body = abs(candle.close - candle.open)
        range_ = candle.high - candle.low
        body_pct = body / range_ if range_ > 0 else 0
        total_body_pct += body_pct
    
    avg_body_pct = total_body_pct / len(candles)
    
    if avg_body_pct < 0.50:
        return True
    
    overlaps = 0
    for i in range(len(candles) - 1):
        current = candles[i]
        next_ = candles[i + 1]
        
        overlap_high = min(current.high, next_.high)
        overlap_low = max(current.low, next_.low)
        
        if overlap_high > overlap_low:
            overlap_size = overlap_high - overlap_low
            current_size = current.high - current.low
            overlap_pct = overlap_size / current_size if current_size > 0 else 0
            
            if overlap_pct > 0.60:
                overlaps += 1
    
    if overlaps >= 2:
        return True
    
    fvg = check_fvg_created_universal(candles[-3:])
    if not fvg:
        return True
    
    return False
```

---

## C. DAILY BIAS (3 QUESTIONS FRAMEWORK)

### Question 1: WHERE IS PRICE RIGHT NOW? (Location)

```python
def answer_q1_location(current_price, daily_range, daily_pdas):
    """
    Determine current price position in context:
    - Premium / Discount / Equilibrium (from structural range)
    - Distance from nearest PDA
    - In PDA yes/no
    """
    
    zone = calculate_premium_discount(current_price, daily_range)
    
    if zone == 'unknown':
        return {
            'position_pct': None,
            'zone': 'unknown',
            'nearest_pda': None,
            'in_pda': False
        }
    
    position_pct = (current_price - daily_range['low']) / \
                   (daily_range['high'] - daily_range['low']) * 100
    
    nearest_pda = find_nearest_pda(current_price, daily_pdas)
    in_pda = check_inside_pda(current_price, daily_pdas)
    
    return {
        'position_pct': position_pct,
        'zone': zone,
        'nearest_pda': nearest_pda,
        'in_pda': in_pda
    }
```

### Question 2: WHERE IS PRICE LIKELY TO GO? (Objective)

```python
def answer_q2_objective(daily_mss, liquidity_pools, current_price):
    """
    Identify clear external draw on liquidity (DoL).
    """
    
    if not daily_mss['exists']:
        return {
            'dol_primary': None,
            'dol_secondary': None,
            'expected_path': None
        }
    
    direction = daily_mss['direction']
    
    objectives = identify_daily_objectives(daily_mss, liquidity_pools, daily_pdas)
    
    if not objectives:
        return {
            'dol_primary': None,
            'dol_secondary': None,
            'expected_path': None
        }
    
    primary = objectives[0] if len(objectives) > 0 else None
    secondary = objectives[1] if len(objectives) > 1 else None
    
    expected_path = f"Price expected to move from {current_price:.5f} to {primary['type']} at {primary['price']:.5f}"
    
    return {
        'dol_primary': primary,
        'dol_secondary': secondary,
        'expected_path': expected_path
    }
```

### Question 3: WHERE IS PRICE COMING FROM? (Respect)

```python
def answer_q3_respect(daily_structure, daily_pdas_respected):
    """
    Determine HTF directional intent from:
    - Order flow (HH/HL or LH/LL)
    - PDA respect (holding bullish or bearish PDAs)
    """
    
    structure_bias = daily_structure
    
    bullish_pdas_held = count_respected(daily_pdas_respected, direction='bullish')
    bearish_pdas_held = count_respected(daily_pdas_respected, direction='bearish')
    
    if bullish_pdas_held > bearish_pdas_held:
        pda_bias = 'bullish'
    elif bearish_pdas_held > bullish_pdas_held:
        pda_bias = 'bearish'
    else:
        pda_bias = 'neutral'
    
    if structure_bias == pda_bias:
        direction = structure_bias
        confidence = 'high'
    elif structure_bias == 'ranging':
        direction = pda_bias
        confidence = 'medium'
    else:
        direction = 'neutral'
        confidence = 'low'
    
    return {
        'htf_direction': direction,
        'confidence': confidence,
        'structure_bias': structure_bias,
        'pda_bias': pda_bias
    }
```

### Bias Synthesis

```python
def synthesize_daily_bias(q1, q2, q3):
    """
    Combine 3 questions into final trade bias
    
    Returns: 'long_only' / 'short_only' / 'both' / 'none'
    """
    
    htf_direction = q3['htf_direction']
    
    if htf_direction == 'neutral':
        return 'none'
    
    if q1['zone'] == 'equilibrium':
        return 'none'
    
    if q2['dol_primary'] is None:
        return 'none'
    
    if htf_direction == 'bullish':
        trade_bias = 'long_only'
    elif htf_direction == 'bearish':
        trade_bias = 'short_only'
    else:
        trade_bias = 'none'
    
    return trade_bias
```

---

## D. ABSOLUTE PROHIBITIONS

```python
# ❌ No swing without MSS
if not mss_exists:
    swings = None

# ❌ No range without MSS
if not mss_exists:
    dealing_range = None

# ❌ No Daily re-biasing intraday
daily_bias_locked = True

# ❌ No trading from equilibrium
if price_zone == 'equilibrium':
    tradeable = False

# ❌ No using Weekly for execution
# Weekly ONLY for macro context

# ❌ No H4/H1 ranges unless Daily allows it
if daily_status != 'post_expansion':
    operating_range = daily_range
else:
    operating_range = h4_h1_range  # REBALANCE mode
```

---

## E. LAYER 0 OUTPUT FORMAT

```python
layer_0_context = {
    'weekly': {
        'mss_exists': bool,
        'mss_direction': 'bullish' | 'bearish' | None,
        'range': {
            'high': float,
            'low': float,
            'equilibrium': float
        } if mss_exists else None,
        'pwh': float,
        'pwl': float,
        'weekly_fvgs': [...],
        'weekly_obs': [...]
    },
    
    'daily': {
        'mss_exists': bool,
        'mss_direction': 'bullish' | 'bearish' | None,
        'order_flow': 'bullish' | 'bearish' | 'mixed' | 'neutral',
        'dealing_range': {
            'high': float,
            'low': float,
            'equilibrium': float,
            'method': 'mss_boundaries' | 'liquidity_pools' | 'external_liquidity' | 'validated_swings',
            'priority': int
        } if range_exists else None,
        'structure_state': {
            'status': 'PRE_EXPANSION' | 'POST_EXPANSION',
            'operating_range': 'use_daily' | 'shift_to_h4_h1'
        },
        'pdas': {
            'fvg_up_zones': [...],
            'fvg_down_zones': [...],
            'ob_bull_zones': [...],
            'ob_bear_zones': [...],
            'ifvg_zones': [...],
            'bpr_zones': [...]
        },
        'liquidity_pools': {
            'bsl': [...],
            'ssl': [...]
        },
        'objective': {
            'price': float,
            'type': 'pdh' | 'pdl' | 'pwh' | 'pwl' | 'daily_fvg' | 'mmxm',
            'priority': int,
            'status': 'NOT_DELIVERED' | 'LIQUIDITY_RUN' | 'DELIVERED_WITH_CONSEQUENCE'
        } if objective_exists else None
    },
    
    'bias': {
        'q1_location': {
            'position_pct': float,
            'zone': 'premium' | 'discount' | 'equilibrium',
            'nearest_pda': {...},
            'in_pda': bool
        },
        'q2_objective': {
            'dol_primary': {...},
            'dol_secondary': {...},
            'expected_path': str
        },
        'q3_respect': {
            'htf_direction': 'bullish' | 'bearish' | 'neutral',
            'confidence': 'high' | 'medium' | 'low',
            'structure_bias': str,
            'pda_bias': str
        },
        'trade_bias': 'long_only' | 'short_only' | 'both' | 'none',
        'bias_note': str
    },
    
    'analysis_timestamp': datetime,
    'analysis_date': date,
    'tradeable': bool
}
```

---

## F. STATE MACHINE LOGIC

```python
def layer_0_state_machine():
    """
    State determines what Layer 0 can provide to lower layers
    """
    
    # STATE 1: NO_STRUCTURE
    if not weekly_mss and not daily_mss:
        return {
            'state': 'NO_STRUCTURE',
            'tradeable': False,
            'reason': 'Waiting for first MSS on Weekly or Daily',
            'context': None
        }
    
    # STATE 2: WEEKLY_ONLY
    if weekly_mss and not daily_mss:
        return {
            'state': 'WEEKLY_ONLY',
            'tradeable': False,
            'reason': 'Weekly structure exists, waiting for Daily MSS',
            'context': {
                'weekly': weekly_context,
                'daily': None,
                'bias': None
            }
        }
    
    # STATE 3: NO_RANGE
    if daily_mss and not daily_range:
        return {
            'state': 'NO_RANGE',
            'tradeable': False,
            'reason': 'Daily MSS exists but no range defined yet',
            'context': {
                'weekly': weekly_context,
                'daily': {
                    'mss_exists': True,
                    'dealing_range': None
                },
                'bias': None
            }
        }
    
    # STATE 4: NO_OBJECTIVE
    if daily_range and not daily_objective:
        return {
            'state': 'NO_OBJECTIVE',
            'tradeable': False,
            'reason': 'Range exists but no clear external draw',
            'context': build_partial_context()
        }
    
    # STATE 5: EQUILIBRIUM
    if price_zone == 'equilibrium':
        return {
            'state': 'EQUILIBRIUM',
            'tradeable': False,
            'reason': 'Price at equilibrium - no directional edge',
            'context': build_full_context()
        }
    
    # STATE 6: FULL_CONTEXT (TRADEABLE)
    if all_components_valid():
        return {
            'state': 'FULL_CONTEXT',
            'tradeable': True,
            'reason': 'All HTF components valid',
            'context': build_full_context()
        }
```

---

## G. INTEGRATION WITH LOWER LAYERS

### Layer 1 (Daily State Engine) Dependencies

```python
# Layer 1 REQUIRES from Layer 0:
- daily_mss (to classify expansion vs pullback)
- daily_objective (to check if delivered)
- daily_structure_state (to know if post-expansion)
```

### Layer 2 (Operating Range Selection) Dependencies

```python
# Layer 2 REQUIRES from Layer 0:
- daily_dealing_range (for primary operating range)
- daily_structure_state (to know if need H4/H1 instead)
- trade_bias (to validate alignment)
```

### Layer 3 (Intraday Execution) Dependencies

```python
# Layer 3 REQUIRES from Layer 0:
- trade_bias ('long_only' / 'short_only' / 'none')
- daily_objective (for TP target)
- daily_pdas (for PDA alignment checks)
```

---

## H. VALIDATION CHECKLIST

**Before Layer 0 can output tradeable=True:**

- [ ] Weekly MSS detected (or confirmed none needed)
- [ ] Daily MSS detected and confirmed
- [ ] Daily range defined (structure-based)
- [ ] Daily objective identified and aligned
- [ ] Objective status = NOT_DELIVERED or LIQUIDITY_RUN (✅ GAP 7)
- [ ] Premium/Discount zone determined (NOT equilibrium)
- [ ] Trade bias synthesized from 3 questions
- [ ] All PDAs tracked (respected/broken/untested)
- [ ] Liquidity pools identified
- [ ] State machine in FULL_CONTEXT state

---

## I. KEY PRINCIPLES SUMMARY

1. **Weekly sets limits.** Daily proves intent and defines direction.
2. **After Daily expansion,** execution shifts to H4/H1 rebalance mode (✅ GAP 8).
3. **Without MSS** → no structure.
4. **Without MSS** → no range. (UPDATED from "Without BOS")
5. **Without objective** → no trade.
6. **Objective must be valid:** NOT_DELIVERED or LIQUIDITY_RUN status (✅ GAP 7).
7. **Post-expansion = impulsive delivery:** Grind rejected (✅ GAP 8).
8. **Structure > Time:** Ranges from MSS, NOT PDH/PDL.
9. **Bias = 3 Questions:** Location + Objective + Respect.
10. **One bias per day:** Set at 00:00 NY, frozen until next day.

---

## J. WHAT'S NOT IN LAYER 0

**Layer 0 does NOT:**
- ❌ Define H4/H1 ranges (that's Layer 2 if post-expansion)
- ❌ Detect intraday FVGs (that's Layer 5)
- ❌ Detect displacement (that's Layer 6)
- ❌ Detect sweeps (that's Layer 3)
- ❌ Make entry decisions (that's Layer 3)
- ❌ Calculate position sizing (that's Layer 3)

**Layer 0 ONLY:**
- ✅ Provides HTF context (Weekly + Daily)
- ✅ Sets daily trade bias
- ✅ Defines structural dealing range
- ✅ Identifies objectives (with liquidity status)
- ✅ Gates lower layers (tradeable yes/no)
- ✅ Detects post-expansion state (rebalance mode)

---

## K. GAPS RESOLUTION SUMMARY (9 LOCKED)

**✅ GAP 1: Bootstrap - First MSS Detection**
- Initial boundaries = **PDH/PDL/PWH/PWL ONLY**
- Nothing else valid for bootstrap (no arbitrary levels, no recent swings)
- Once first MSS confirmed → normal MSS detection starts

**✅ GAP 2: BOS vs MSS Distinction**
- **BOS = MSS** (exactly the same thing)
- Use **"MSS" terminology ONLY**
- Delete all "BOS" references throughout
- Ranges created FROM MSS boundaries (derived, not separately detected)

**✅ GAP 3: Displacement Definition (All Timeframes)**
- **QUALITATIVE** (NO pip thresholds)
- 5 components: forceful exit + removes structure + FVG + one-sided + no rotation
- **Universal** across ALL timeframes (Weekly → 15m)
- Same logic, only context scales with timeframe

**✅ GAP 4: FVG Detection (Universal)**
- **Simple check**: `Candle A high < Candle C low` (bullish) OR `Candle A low > Candle C high` (bearish)
- **NO pip thresholds, NO body checks, NO timeframe scaling**
- FVG respect: Same 5 conditions for all timeframes
- Only difference by timeframe: **Impact/Weight** (macro → execution)

**✅ GAP 5: Validated Swings Definition**
- Swing candidates = **local pivots only** (lookback=3)
- Validated when price reacts with **IMMEDIATE displacement** (1-3 candles max)
- "If a level matters, algorithms respond instantly"
- **IPDA ranges** (20/40/60) for bootstrap context only
- **Priority**: Equal highs/lows > External liquidity > MSS swings > Validated swings

**✅ GAP 6: MMXM Identification**
- **MMXM = Failed auction** (NOT rigid 3-phase template)
- **Timeframe priority:** Daily (1) > H4 (2) > H1 (3 - execution only)
- **Lookback:** Since last Daily MSS ONLY (MSS resets narrative)
- **Two roles:**
  - TYPE 1: MMXM as manipulation (origin) - trade AWAY from MMXM
  - TYPE 2: MMXM as target (objective) - trade TOWARDS MMXM
- **MMXM High/Low = Original consolidation boundaries** (NOT manipulation extreme)
- **As target:** NO liquidity sweep required at MMXM (MMXM IS the liquidity pool)
- **As manipulation:** ALL conditions required (sweep + fail + displacement + FVG + structure)
- **Priority 1 target** in objective hierarchy (above PDH/PDL/PWH/PWL)
- **Higher TF ALWAYS overrides lower TF**

**✅ GAP 7: Liquidity Level Status Classification**
- **Three states:** NOT_DELIVERED, LIQUIDITY_RUN, DELIVERED_WITH_CONSEQUENCE
- **Removed terms:** "defended", "weakly defended", "unreached"
- **NOT_DELIVERED:** Never touched (highest quality target)
- **LIQUIDITY_RUN:** Touched but no structural consequence (valid target, delivery ongoing)
- **DELIVERED_WITH_CONSEQUENCE:** Consequence occurred AT level (invalid, exclude from targets)
- **Consequences:** Displacement, MSS, FVG, or structure change FROM the level
- **Target filtering:** Only NOT_DELIVERED and LIQUIDITY_RUN are valid objectives

**✅ GAP 8: Post-Expansion Threshold**
- **Simple trigger:** Objective delivered WITH displacement
- **Displacement required:** Impulsive move (strong bodies, FVG, one-sided, no grind)
- **Grind rejected:** Slow overlap, small bodies, balanced auction = invalid delivery
- **State is PERMANENT:** Until new Daily MSS occurs (current price after delivery irrelevant)
- **System behavior change:**
  - PRE-EXPANSION: Use Daily range for premium/discount, target Daily objectives
  - POST-EXPANSION: Shift to H4/H1 **REBALANCE mode**, Daily = direction filter only
- **Terminology:** "REBALANCE" (correct ICT term), NOT "reload"

**✅ GAP 9: PDH/PDL/PWH/PWL Definition**
- **Forex Trading Day:** 17:00 NY → 17:00 NY next day (NOT midnight)
- **PDH:** Highest WICK in prior completed Forex day
- **PDL:** Lowest WICK in prior completed Forex day
- **PWH:** Highest WICK in prior completed Forex week (Sunday 17:00 → Sunday 17:00)
- **PWL:** Lowest WICK in prior completed Forex week
- **DST Handling:** Always use NY local time (America/New_York), auto-adjusts EDT/EST
- **Critical Rules:**
  - ⛔ Do NOT use midnight (00:00) boundaries
  - ⛔ Do NOT use candle closes (only wicks)
  - ⛔ Do NOT hardcode UTC offsets
  - ✅ Wicks show liquidity, closes show acceptance

---

**Version:** 4.1 FINAL (With 9 Gaps Integrated)  
**Status:** LOCKED — LAYER 0 COMPLETE  
**Date:** January 30, 2026  
**Updates:** 
- GAP 1: Bootstrap logic (PDH/PDL/PWH/PWL only)
- GAP 2: BOS → MSS terminology (all references updated)
- GAP 3: Displacement qualitative definition (no pip thresholds)
- GAP 4: Universal FVG detection (all timeframes)
- GAP 5: Validated swings + IPDA ranges + priority hierarchy
- GAP 6: MMXM identification (failed auction, two roles, original consolidation)
- GAP 7: Liquidity level status (3-state classification, consequence detection)
- GAP 8: Post-expansion threshold (delivery + displacement trigger, rebalance mode)
- GAP 9: PDH/PDL/PWH/PWL definition (Forex day 17:00 NY, wicks only)

**Layer 0 Status:** ALL 9 GAPS RESOLVED

**Next:** Layer 1 - Daily State Engine

---

**END OF LAYER 0 SPECIFICATION**
