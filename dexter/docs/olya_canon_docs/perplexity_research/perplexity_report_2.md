Professional systematic shops do enrich OHLCV into market-structure states, but they do it with a relatively lean, targeted feature set, heavy emphasis on regime/seasonality modeling, and (for serious size) order‑book or footprint data layered on top of bars. Your current architecture (OHLCV → enrichment → deterministic structure → boolean gates → human approval) is directionally sound, but likely over‑engineered at 400+ features and under‑specified around regime/session modeling and explicit empirical validation. [arxiv](https://arxiv.org/html/2509.16137v1)

Below is a concise brief organized around your numbered questions.

***

## 1. OHLCV Enrichment Architecture

Systematic pipelines usually follow a **raw → cleaned → enriched → signal → execution** pattern. For bar‑based systems this often looks like: [alphascientist](https://alphascientist.com/feature_engineering.html)

- Raw: timestamp, O/H/L/C, volume, sometimes trade count and basic condition codes. [onepagecode.substack](https://onepagecode.substack.com/p/engineering-a-stock-prediction-pipeline)
- Cleaned: corporate actions handled, missing bars patched or removed, obvious bad ticks filtered. [onepagecode.substack](https://onepagecode.substack.com/p/engineering-a-stock-prediction-pipeline)
- Enriched core:
  - Normalized returns (close‑to‑close, high‑low ranges, volatility estimates). [arxiv](https://arxiv.org/html/2504.02249v2)
  - Price location in recent range (percentile in N‑bar high/low channel, distance to rolling VWAP/EMA). [alphascientist](https://alphascientist.com/feature_engineering.html)
  - Volume/participation measures (volume z‑scores vs lookback, volume‑weighted volatility). [arxiv](https://arxiv.org/html/2509.16137v1)
  - Time‑of‑day/session dummies and intraday seasonality features. [sciencedirect](https://www.sciencedirect.com/science/article/abs/pii/S0889158306000463)
  - A small number of “micro‑pattern” indicators (e.g., inside/outside bars, gap flags, trend filters). [alphascientist](https://alphascientist.com/feature_engineering.html)

### Typical feature counts

- Academic/retail ML examples using OHLCV often show 20–60 engineered features: a handful of returns, a few volatility measures, 5–10 trend/oscillator indicators, and several time/calendar features. [repository.tudelft](https://repository.tudelft.nl/file/File_f1226238-ebc5-4691-b687-3eb4c5e5663c?preview=1)
- Industrial‑grade alpha platforms may track hundreds of alphas, but any *single* production strategy often relies on a few dozen primary features plus regime/portfolio context. [alphascientist](https://alphascientist.com/feature_engineering.html)
- Studies comparing full OHLCV vs subsets show modest incremental benefit from using the full set vs just close+volume, indicating diminishing returns beyond a compact feature set. [arxiv](https://arxiv.org/html/2504.02249v2)

Your 400‑column enrichment is almost certainly redundant. A practical pattern is:

- Treat “features” as *families*: e.g. returns at several horizons is one family, volatility metrics another.  
- Explicitly separate:
  - “Inputs to structure detection” (swing highs/lows, regime labels, session IDs)  
  - “Trading filters” (volatility regimes, liquidity filters, spread/impact proxies)  
  - “Diagnostics/analytics” (things you log but do not gate on).

### Principled feature selection

Professionals rarely “compute everything then hope.” They:

- Start from a **hypothesis** or rule (e.g., trend‑following, intraday mean reversion, breakout around session overlap) and design **minimal sufficient features** to test it. [onepagecode.substack](https://onepagecode.substack.com/p/engineering-a-stock-prediction-pipeline)
- Run simple univariate tests (predictive IC, t‑tests, conditional distributions) to prune non‑contributing features before plugging into more complex models. [alphascientist](https://alphascientist.com/feature_engineering.html)
- Use regularization (lasso/ridge), tree‑based importance, or embedded methods in ML contexts, but the initial filter is usually domain‑driven rather than purely automated. [repository.tudelft](https://repository.tudelft.nl/file/File_f1226238-ebc5-4691-b687-3eb4c5e5663c?preview=1)

Given your governance‑first setup, a **backward‑from‑gate** design is natural: for each boolean ICT gate, define the smallest observable set of features needed to answer its question, deprecate everything else to “experimental.”

### Multi‑timeframe alignment

Common implementations:

- **Separate enrichment per timeframe, then join:**  
  - Create independent feature sets for, say, daily, 4H, 1H, 5m bars, then align them by timestamp with forward‑fill for higher TF features. [onepagecode.substack](https://onepagecode.substack.com/p/engineering-a-stock-prediction-pipeline)
- **Hierarchical logic:**  
  - Higher TF defines *regime* or *bias* (trend, volatility, risk‑on/off), lower TF defines entries/exits consistent with that regime. [papers.ssrn](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3406068_code3576909.pdf?abstractid=3406068&mirid=1)
- Alignment details:
  - Use explicit “as‑of” joins (e.g., each 5m bar sees the most recent completed 4H and daily bar features) and keep HTF features clearly namespaced (e.g., `HTF_trend_state`, `D_vol_regime`). [onepagecode.substack](https://onepagecode.substack.com/p/engineering-a-stock-prediction-pipeline)

This maps neatly onto your 5‑drawer scheme if each drawer reads from a clear layer (HTF bias features vs LTF structure vs micro entry).

***

## 2. Market Structure Detection Models

### Deterministic state machines

- Rule‑based swing logic (identify local highs/lows with a lookback and classify breaks as BOS/CHoCH) is very close to what many systematic trend/breakout systems do, though they’d phrase it as “swing breakout,” “range breakout,” or “support/resistance regime change” rather than ICT. [luxalgo](https://www.luxalgo.com/blog/counting-systems-trading-metrics-simplified/)
- State machines are standard for:
  - Trend state (up, down, flat).  
  - Volatility regime (low/medium/high).  
  - Trade lifecycle (flat → setup → entry → manage → exit). [luxalgo](https://www.luxalgo.com/blog/counting-systems-trading-metrics-simplified/)
- Advantages: transparency, easy audit, compatible with governance and explainability.  
- Disadvantages: brittle to parameter choice, can miss smooth regime shifts, and can be noisy in choppy environments without additional smoothing.

Your use of a deterministic structure state machine is strongly aligned with professional practice, especially in discretionary‑assisted systematic desks.

### HMMs / regime‑switching

- Hidden Markov Models and other regime‑switching models are widely used in academic and practitioner work for bull/bear/volatility regime detection. [questdb](https://questdb.com/glossary/market-regime-detection-using-hidden-markov-models/)
- Some practitioner sources explicitly note HMMs for 2–4 state “up/flat/down” market regimes and mention rumors of use at major quant firms. [pyquantnews](https://www.pyquantnews.com/the-pyquant-newsletter/use-markov-models-to-detect-regime-changes)
- Strengths: soft, probabilistic regime labels; can incorporate multiple features (returns, volatility, volume, spreads); useful as a *meta‑state* that conditions structure interpretation. [questdb](https://questdb.com/glossary/market-regime-detection-using-hidden-markov-models/)
- Weaknesses: parameter instability, sensitivity to specification (number of states, emission distribution), and “regime overfitting” if not rigorously validated. [pmc.ncbi.nlm.nih](https://pmc.ncbi.nlm.nih.gov/articles/PMC12507299/)

In your architecture, an HMM‑style regime label works well as an additional **HTF Bias** input, not as a replacement for explicit swing/structure rules.

### ML classifiers (CNN/LSTM on price sequences)

- There are academic works that apply CNN/LSTM networks to detect pattern structures (e.g., Wyckoff accumulation/distribution phases, complex price patterns). [arxiv](https://arxiv.org/abs/2403.18839)
- These show that deep models *can* learn structural phases, but they come with:
  - Opaqueness (hard to map back to simple ICT‑style conditions).  
  - Fragility across regimes and asset classes.  
  - More challenging governance/explainability.  
- Practitioner interviews and surveys frequently indicate that deep models are used more for **forecasting returns or volatility** than for replacing interpretable structure logic in production; opaque models are often confined to research or low‑risk contexts. [signalsandthreads](https://signalsandthreads.com/finding-signal-in-the-noise/)

Given your “constitutional” governance and boolean‑gate design, ML structure detection is better as an optional *advisory* overlay, not a primary gatekeeper.

### Order‑flow / footprint models

- Footprint and order‑flow tools compute:
  - Bid‑ask volume at each price, delta (buy minus sell volume), and various imbalance metrics. [th.tradingview](https://th.tradingview.com/scripts/orderflow/)
  - Concepts like absorption, single/stacked imbalances, and thin/low‑volume prints, which correspond to perceived institutional activity and aggressive one‑sided moves. [litefinance](https://www.litefinance.org/blog/for-beginners/trading-strategies/order-flow-trading-with-footprint-charts/)
- These are indeed a different lens than OHLCV alone, with more direct microstructure grounding: you see which side actually traded, not just the bar extremes. [bestorderflow](https://bestorderflow.com/footprint)
- For many intraday futures/FX desks, **order‑flow is the primary micro‑structure signal**, with bar‑based structure for higher‑level context. [litefinance](https://www.litefinance.org/blog/for-beginners/trading-strategies/order-flow-trading-with-footprint-charts/)

If you trade liquid FX indices with access to good tick/quote data, layering simple order‑flow features (delta, footprint imbalances) on top of your OHLCV structure model would align you with institutional practice.

***

## 3. Imbalance / Gap Detection

### ICT FVG vs quant terminology

- “Fair value gap” in ICT/SMC matches several existing notions:
  - Order‑flow imbalances (price moves so fast one side dominates, leaving thin/low‑volume prints). [bestorderflow](https://bestorderflow.com/footprint)
  - “Price voids” or “imbalances” in footprint charts, where price extends with little counter‑trade. [bestorderflow](https://bestorderflow.com/footprint)
  - In market profile/auction theory, “single prints” or “poor structure”—price traded at a level in only one 30‑minute TPO, reflecting a poor auction. [youtube](https://www.youtube.com/watch?v=OpI1ak1wNrI)
- Practitioner education now explicitly labels one type of footprint imbalance as “FVG – Fair Value Gap imbalance,” essentially linking the ICT definition to an order‑flow imbalance where price extended without resistance. [bestorderflow](https://bestorderflow.com/footprint)

So FVG is not alien; it is a rebranding of existing concepts of **unbalanced auction or thin market structure**.

### Computational detection

From OHLCV alone:

- Basic OHLC definition: a “gap” where part of a 3‑bar pattern’s price range (e.g., previous high vs next low) has no overlap, matching ICT’s three‑candle FVG definition. [aquafunded](https://www.aquafunded.com/blogs/what-is-a-fair-value-gap-in-trading)
- Market profile analogue (requires at least per‑price volume or TPOs):
  - Single prints: price levels with only one TPO in a session.  
  - Poor highs/lows: almost straight‑line profile extremities with no tail. [youtube](https://www.youtube.com/watch?v=OpI1ak1wNrI)
- Footprint analogue:
  - Thin/low‑volume zones and imbalances along a bar, indicating one‑sided execution and a “void” in the auction. [youtube](https://www.youtube.com/watch?v=5U-WhaeuOds)

### Empirical evidence on gap “magnets”

- Classical equity studies show that some types of overnight gaps partially close, but the edge depends heavily on context (earnings, news, volatility). [d-nb](https://d-nb.info/1265952744/34)
- In terms of auction theory:
  - “Poor structure” and “single prints” are often treated as areas that might be revisited, but this is more practitioner lore than rigorously quantified in the academic literature. [youtube](https://www.youtube.com/watch?v=OpI1ak1wNrI)
- Some order‑flow practitioners note that strong imbalances/voids are either continuation zones or later test zones, but the specific “price must return” narrative is not strongly backed by broad, peer‑reviewed studies. [litefinance](https://www.litefinance.org/blog/for-beginners/trading-strategies/order-flow-trading-with-footprint-charts/)

For your purposes, treat FVG/imbalance as a **conditional context feature** whose utility must be tested empirically per market, rather than a hard law.

### Tracking significance and fill rates

Professional implementations tend to:

- Track **gap attributes**: size (in ATR/volatility units), age, direction, session of origin, accompanying volume/volatility spike. [bestorderflow](https://bestorderflow.com/footprint)
- Maintain per‑instrument statistics:
  - Fill probability within N bars or N sessions conditional on gap size, volatility regime, and news classification.  
  - Conditional return distribution “through” vs “into” the gap.  
- De‑emphasize old, small, or noise‑driven gaps; treat **large, regime‑casting voids** as more significant. [youtube](https://www.youtube.com/watch?v=OpI1ak1wNrI)

Your boolean gate could be “active FVG candidates” once these empirical filters are applied, dramatically reducing the count vs naive enumeration.

***

## 4. Liquidity Event Detection

### Stop‑loss clustering research

- Microstructure literature documents that order flow, especially near obvious round numbers and recent highs/lows, is often clustered around those price points, and that aggressive orders can trigger cascades. [nber](https://www.nber.org/system/files/working_papers/w12413/w12413.pdf)
- More applied SMC‑style sources explicitly describe “engineered liquidity grabs” at obvious stop pools and report that algorithmic order books test these levels to fill size before reversing. [mindmathmoney](https://www.mindmathmoney.com/articles/liquidity-sweep-trading-strategy-how-smart-money-hunts-stop-losses-for-profit)
- However, rigorous, large‑sample academic evidence directly quantifying “stop hunt → reversal” in ICT terms is sparse; most detailed discussions are practitioner‑oriented.

### Programmatic “equal highs/lows”

From OHLCV only, obvious stop pools approximate to:

- Recent swing high/low clustering:
  - Price making multiple highs within a small tick or percentage band over N bars.  
  - Recent range boundaries touched multiple times.  
- Round number proximity:
  - Levels near 00/25/50/75 pips or large round numbers often act as liquidity magnets in FX. [sciencedirect](https://www.sciencedirect.com/science/article/abs/pii/S0889158306000463)
- You already have structure states; you can augment with:
  - “External liquidity” above/below prior swing structures.  
  - “Internal liquidity” within current consolidation ranges.

### Liquidity sweeps → reversal

- SMC/ICT‑oriented practitioner literature defines a sweep as: price breaking beyond a clear liquidity pool, triggering stops, then sharply reversing back inside the prior range. [alchemymarkets](https://alchemymarkets.com/education/strategies/liquidity-sweep/)
- Many discretionary and semi‑systematic traders use this pattern with added confirmation (volume spike, failure to follow through, lower‑TF structure flip). [internationaltradinginstitute](https://internationaltradinginstitute.com/blog/mastering-stop-loss-placement-liquidity-sweeps-invalidation-cross%E2%80%91asset-exits/)
- But the strict “sweep implies reversal edge” is not well established in broad academic studies; it is largely experiential lore that must be validated per instrument.

### Features from OHLCV to approximate sweeps

Without order book:

- Identify **key levels**: clustered highs/lows, HTF swing points, prior session extremes.  
- Define a sweep event as:
  - Price breaks above/below such a level (intrabar or close), prints a relatively large bar (vs ATR), then closes back inside the previous range within a short horizon (same bar or next few bars).  
- Add contextual features:
  - Volume spike and/or volatility spike relative to local history. [arxiv](https://arxiv.org/html/2509.16137v1)
  - Time‑of‑day and session (sweeps around session open or overlap vs random times). [quanthedge.substack](https://quanthedge.substack.com/p/seasonality-of-intraday-volatility)
  - Post‑sweep structure (e.g., lower‑TF break in opposite direction).

These features map neatly into your **Market Structure** and **Confirmation** drawers and can be expressed as boolean gates with numeric thresholds derived from backtests rather than lore.

***

## 5. Session & Time Context

### Evidence on FX session effects

- Classic work using electronic broking data for USD/JPY and EUR/USD shows strong intraday patterns in trading volume, quote revisions, and volatility tied to regional business hours and overlaps (Tokyo, London, New York). [nber](https://www.nber.org/system/files/working_papers/w12413/w12413.pdf)
- Key findings:
  - Activity and volatility concentrate in London and London–New York overlap, with clear U‑shaped intraday patterns for several centers. [sciencedirect](https://www.sciencedirect.com/science/article/abs/pii/S0889158306000463)
  - Spreads tend to narrow when deal counts are high, and volatility is negatively correlated with spreads, consistent with deeper markets in active sessions. [sciencedirect](https://www.sciencedirect.com/science/article/abs/pii/S0889158306000463)
- Practitioner studies on intraday volatility of many FX pairs confirm that volatility and range behavior differ markedly by session and overlap, and that the “classic” London/NY focus is pair‑dependent. [quanthedge.substack](https://quanthedge.substack.com/p/seasonality-of-intraday-volatility)

So the generic ICT notions of “Asian range,” “London open expansion,” and “NY volatility” do have quantitative backing, though with nuances across pairs.

### Implementation of kill zones / session windows

Systematic implementations:

- Encode:
  - Session dummies (Tokyo, London, New York, overlaps).  
  - Hour‑of‑day, minute‑of‑session, and possibly pre‑/post‑major fixings or news windows. [arxiv](https://arxiv.org/html/2509.16137v1)
- “Kill zones” become explicit time windows during which:
  - Certain setups are allowed/weighted.  
  - Position sizing or filters change (e.g., avoid new trades in illiquid handover periods).  
- Many intraday strategies are explicitly conditioned on time‑of‑day features, which are standard in FX algos. [quanthedge.substack](https://quanthedge.substack.com/p/seasonality-of-intraday-volatility)

Evidence quality: strong for **volatility/volume seasonality**; weaker and more strategy‑specific for pattern‑type effects (e.g., breakout vs mean reversion), which must be tested per signal.

***

## 6. Architecture Patterns

### Pipeline and layers

A common pattern for professional systems is:

1. **Data layer**  
   - Ingestion → cleaning → standardized bar/tick data with minimal fields. [arxiv](https://arxiv.org/html/2509.16137v1)
2. **Feature/enrichment layer**  
   - Deterministic transformations: returns, volatility, regime stats, schedule/session features, selected technicals. [arxiv](https://arxiv.org/html/2509.16137v1)
3. **Signal/alpha layer**  
   - Rule‑based conditions, statistical signals, or ML models that consume a small subset of features and output interpretable states or alpha scores. [luxalgo](https://www.luxalgo.com/blog/counting-systems-trading-metrics-simplified/)
4. **Portfolio and risk layer**  
   - Cross‑asset position sizing, constraints, kill switches.  
5. **Execution layer**  
   - Smart order routing, slippage control, microstructure logic.

Your “constitution” maps well to layer 3 and 4; the main risk is over‑complicating layer 2.

### Feature store vs compute‑on‑demand

- Larger firms often maintain a **feature store**: precomputed, versioned features keyed by instrument, date/time, and model version, to avoid recomputing expensive rolling metrics, ensure reproducibility, and support multiple strategies. [onepagecode.substack](https://onepagecode.substack.com/p/engineering-a-stock-prediction-pipeline)
- Lightweight systematic setups sometimes recompute features on the fly per run if the universe and history window are small, but this becomes unwieldy as you accumulate features.

Given your governance, a feature store that stores only **approved** features and their definitions fits nicely: it gives you a fixed “constitution” of allowed inputs.

### Multi‑timeframe: hierarchical vs flat

- Hierarchical is dominant: higher TF defines bias/regime; lower TF defines entries consistent with that regime. [papers.ssrn](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3406068_code3576909.pdf?abstractid=3406068&mirid=1)
- Some high‑frequency or pure statistical arbitrage strategies effectively treat all horizons more symmetrically, but for discretionary‑adjacent directional trading, **HTF governs LTF** is the norm.

Your five drawers are already hierarchically structured; formalizing that with explicit “HTF bias” state machines and regime models is aligned with institutional design.

### State management: event‑driven vs polling

- Event‑driven systems react to:
  - New bar arrival, price/volume thresholds, or external events.  
- Polling systems check conditions at fixed intervals (every bar), which is effectively event‑driven at bar granularity.  
- For bar‑based FX/indices, event‑driven on bar close is standard; more sophisticated desks mix:
  - Event‑driven order‑book triggers.  
  - Scheduled checks around session opens, closes, and news times. [sciencedirect](https://www.sciencedirect.com/science/article/abs/pii/S0889158306000463)

A hybrid (bar‑close evaluation plus explicit events for session transitions and scheduled risk checks) fits your governance‑first focus.

***

## How Your Approach Stacks Up

- **Sound elements**  
  - Deterministic state machine for structure.  
  - Multi‑drawer decomposition (bias, structure, PD arrays, entries, confirmation).  
  - Human approval and explainable boolean gates.

- **Likely excessive**  
  - 400+ enrichment columns without clear mapping to specific gates or empirical contribution; most production systems rely on perhaps a few dozen active features per signal. [arxiv](https://arxiv.org/html/2504.02249v2)

- **Potential gaps**  
  - Explicit statistical regime detection (e.g., HMM or simpler volatility/state filters) as inputs to HTF Bias. [pyquantnews](https://www.pyquantnews.com/the-pyquant-newsletter/use-markov-models-to-detect-regime-changes)
  - Rigorous empirical vetting of ICT‑style constructs (FVG, sweeps) per instrument and session, instead of treating them as axioms.  
  - Order‑flow / footprint layer if you intend to compete intraday in very liquid products. [litefinance](https://www.litefinance.org/blog/for-beginners/trading-strategies/order-flow-trading-with-footprint-charts/)

A practical next step would be:

1. For each ICT gate in each drawer, write down the **minimal feature set** required to evaluate it.  
2. Reduce your enrichment to that union plus a small set of regime/time features.  
3. Add a separate **regime label** (even a simple volatility/trend state to start), and later evaluate adding an HMM or related model if the governance committee accepts probabilistic states.  
4. Incrementally test whether adding order‑flow features materially improves detection of your “liquidity event” and “imbalance” gates.

If you’d like, I can help you design a concrete minimal feature schema, gate‑by‑gate, together with a small experiment plan to evaluate FVG and sweep behaviors in a couple of your core instruments.