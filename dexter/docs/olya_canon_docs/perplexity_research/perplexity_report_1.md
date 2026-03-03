Professional systematic desks that trade “price action” tend to use a *small, purpose‑built feature layer* over OHLCV, deterministic but carefully‑specified structure state machines, and a lot of discipline about what they refuse to automate. That’s very close to what you’re aiming for; the main architectural risks are feature bloat, under‑modeled ambiguity, and forgetting that OHLCV alone has a ceiling for microstructure‑driven ideas. [alphascientist](https://alphascientist.com/feature_engineering.html)

I’ll keep this tight and synthesis‑heavy, aligned with your questions.

***

## 1. Feature Engineering Architecture for Price‑Action Systems

### Push vs pull enrichment

In rule‑based, price‑action‑like systems, there are two broad patterns:

- **Push (big feature matrix)**  
  - Common in ML pipelines: precompute dozens–hundreds of generic transforms (returns at multiple horizons, range measures, classic indicators, time features) and let downstream models or rules pick. [luxalgo](https://www.luxalgo.com/blog/feature-engineering-in-trading-turning-data-into-insights/)
  - This is convenient for experimentation but creates maintenance and governance overhead; most production strategies end up consuming a small, stable subset. [actingintelligent](https://actingintelligent.com/practical-feature-selection-for-algorithmic-trading/)

- **Pull (gate‑driven)**  
  - More common when the underlying logic comes from a human methodology: start from the rules, then implement the *minimal* set of features each rule needs. [robotwealth](https://robotwealth.com/quant-systematic-trading-vs-discretionary/)
  - Practitioners who systematize discretionary approaches explicitly warn against “feature explosion,” and advocate implementing only features that are tied to a well‑defined hypothesis or rule. [quantpedia](https://quantpedia.com/combining-discretionary-and-algorithmic-trading/)

In a governance‑first, boolean‑gate system mirroring a specific expert, the **pull/gate‑driven model is closer to industry best practice** than precomputing hundreds of columns. You can still keep an “experimental” enrichment area, but it should be clearly separated from the constitutional feature set.

### Feature granularity for visual patterns

When translating visual chart patterns into machine‑readable terms, the common pattern is **“atoms + composed detectors”**:

- **Atomic features**  
  - Local shape descriptors: swing‑high/low flags (based on lookback/forward windows), bar range, body vs wick ratios, gap flags, volatility and volume z‑scores. [jetwi](http://www.jetwi.us/uploadfile/2014/1223/20141223120018209.pdf)
  - Context: trend state at higher TF, distance from recent high/low, time‑of‑day/session. [finage.co](https://finage.co.uk/blog/how-to-use-ohlcv-data-to-improve-technical-analysis-in-trading--684007623458598454e3dd10)

- **Composite pattern detectors**  
  - Implemented as functions or state machines that consume atoms and output higher‑level booleans or small enums, e.g.:
    - “BOS_up”, “BOS_down”, “CHoCH_up”, “CHoCH_down”. [tradingfinder](https://tradingfinder.com/education/forex/ict-higher-highs-higher-lows/)
    - “FVG_present_here”, “displacement_bar_here”, “sweep_of_level_X_occurred”.  
  - Systematic trend‑following papers and practitioner guides follow this pattern: they define HH/HL structure, then trend filters, then patterns like “break above N‑bar high with rising volatility.” [blog.traderspost](https://blog.traderspost.io/article/trend-following-strategies-guide)

This has an important architectural implication: **you keep the column count low at the bar level**, and move complexity into *functions over sequences*, not more columns. For example, you don’t store “BOS_up” as a permanent feature for every bar; you have a structure engine that can answer “did a BOS_up occur here?” when a gate asks.

### Maintenance burden and feature staleness

Practitioner discussions on feature selection for trading systems highlight several pain points once feature sets get large: [alphascientist](https://alphascientist.com/feature_engineering.html)

- **Drift and silent breakage**  
  - Any change in data vendor, corporate action handling, or calendar rules can silently alter feature values, making reproducibility and audits harder.  
- **Entanglement**  
  - Rules eventually refer to features whose definitions no one fully understands, making it risky to refactor.  
- **Overfitting by construction**  
  - Large feature sets encourage cherry‑picked backtests and rules tuned to narrow regimes.

A common mitigation pattern:

- Maintain a **versioned “feature registry”** where each feature has:
  - A human‑readable definition tied to the methodology.  
  - A code implementation and tests.  
  - A last‑used timestamp and list of consumers (rules/models).  
- Periodically prune:
  - Features unused in any active gate for N months.  
  - Features whose empirical predictive power or filtering value has decayed in recent data. [actingintelligent](https://actingintelligent.com/practical-feature-selection-for-algorithmic-trading/)

In rule‑based (non‑ML) systems, you almost never see hundreds of *active* features per bar. More typical for price‑action/trend systems is on the order of **20–60 well‑maintained features** (plus some temporary analytics). [jetwi](http://www.jetwi.us/uploadfile/2014/1223/20141223120018209.pdf)

### Gate‑driven (“backwards”) design

There is clear precedent for your approach:

- Work on combining discretionary and systematic trading explicitly frames the algorithm as “codified filters” and “setup detectors” that a discretionary trader can override. [quantpedia](https://quantpedia.com/combining-discretionary-and-algorithmic-trading/)
- Quant practitioners writing about discretion vs quant emphasize that both camps exploit the same underlying phenomena; the difference is that one is discovered via screen time, the other via data analysis. [robotwealth](https://robotwealth.com/quant-systematic-trading-vs-discretionary/)

In this context, the standard pattern is:

1. Take each human rule/gate and translate it into a **formal natural‑language spec**: which parts of the chart does the expert inspect and what do they look for?  
2. Define the smallest set of **atomic** OHLCV‑derived features that let you implement that rule unambiguously.  
3. Build a **testable composite detector** (function or state machine) that uses those features.  
4. Only then decide whether any of those atomic features deserve persistent columns or should remain internal to the detector.

Against “compute everything, query what you need”, gate‑driven design tends to yield **simpler, more maintainable systems** with clearer ownership and fewer accidental dependencies. The trade‑off is less flexibility for ad‑hoc exploratory analysis, which you can address with a separate research‑only enrichment stack.

***

## 2. Market Structure State Machines

### Deterministic vs probabilistic structure

In practice you see a **hybrid**:

- **Deterministic structure engines**  
  - Trend‑following and technical‑rule systems almost always implement HH/HL, LH/LL logic deterministically (with explicit lookback rules, filters on minimum swing size, etc.). [thebull.com](https://thebull.com.au/trading-guides/developing-a-trend-following-system/)
  - This typically looks like a state machine that tracks:
    - Current trend state (up, down, range).  
    - Last confirmed swing high/low.  
    - Whether a new break has occurred relative to those swings.

- **Probabilistic/regime models as context**  
  - Separate regime models (e.g., volatility regimes, trending vs mean‑reverting, bull vs bear) are often built with Hidden Markov Models or other regime‑switching frameworks. [papers.ssrn](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3406068_code3576909.pdf?abstractid=3406068&mirid=1)
  - These produce probabilities over macro states that can *modulate* how you interpret price action, but they usually don’t replace the deterministic notion of “higher high/higher low”.

So the industry pattern is: **explicit, deterministic market structure; probabilistic macro regimes layered on top.** That dovetails with your HTF Bias drawer: a regime model could be one of the inputs, while structure remains a transparent state machine.

### Handling ambiguity

Ambiguity arises because:

- What counts as a “significant” swing depends on volatility and timeframe.  
- Context (e.g. HTF trend) changes the interpretation of the same pattern.

Systematic approaches handle this mainly by **tightening the definitions and conditioning, not by adding probabilistic fuzziness inside the structure engine**:

- Define swings with:
  - Minimum price move thresholds (e.g., percentage or ATR times a factor). [jetwi](http://www.jetwi.us/uploadfile/2014/1223/20141223120018209.pdf)
  - Minimum bar counts between pivots.  
- Define structure breaks with:
  - Closes beyond prior swings rather than wicks only.  
  - Confirmation rules (e.g., require N bars of acceptance beyond a level).  
- Condition interpretation on:
  - Higher‑TF trend state: e.g., classify a lower‑TF LL as a “pullback” vs “reversal attempt” depending on daily trend. [thebull.com](https://thebull.com.au/trading-guides/developing-a-trend-following-system/)

Where probabilistic modeling appears is at the **decision layer**: instead of saying “structure is bullish” you might say “structure is bullish by our deterministic definition, but the probability we are in a trending regime is only 30%, so gates that require strong trend are inactive.”

### Multi‑timeframe coherence

Common architectures for multi‑TF structure:

- **Independent per‑TF engines + confluence logic**  
  - Each timeframe (e.g., daily, 4H, 1H, 15m) has its own deterministic structure state machine. [thebull.com](https://thebull.com.au/trading-guides/developing-a-trend-following-system/)
  - A confluence layer defines allowable combinations (e.g., only trade long when daily is up and 1H has just turned up from a pullback).

- **Explicit hierarchical state machines**  
  - Some practitioners design HTF structure as a “super‑state” that governs what lower‑TF states are even considered meaningful, e.g.:
    - If daily trend is down, a 5‑minute HH/HL sequence is tagged “counter‑trend” and either ignored or given smaller weight.  
  - This is conceptually just a more disciplined version of the independent‑plus‑confluence approach.

For your architecture, a clean pattern is:

- One **Structure Engine per TF**, each emitting:
  - Current trend state (enum).  
  - Current valid swing points.  
  - Last structure event (BOS_up, BOS_down, CHoCH, etc.).  
- A **Confluence Drawer** that consumes these and implements your theory of “alignment” (e.g., HTF must be up, LTF must have just formed an HL + BOS_up, etc.).

This keeps each state machine simple while housing your ICT‑style confluence logic separately.

***

## 3. Industry Patterns & Anti‑Patterns

### What kills these systems?

From practitioner write‑ups and experience reports on systematizing discretionary trading, several recurring failure modes show up: [quantpedia](https://quantpedia.com/combining-discretionary-and-algorithmic-trading/)

- **Feature explosion & rule creep**  
  - Teams keep adding indicators, pattern checks, and exceptions to match the guru’s last hundred anecdotes, until the system is essentially curve‑fit to a small historical sample.  
- **Trying to code “vibe”**  
  - Discretionary experts often use holistic, context‑heavy judgment; trying to encode every nuance results in brittle rules that overfit local structures and break in new regimes. [robotwealth](https://robotwealth.com/quant-systematic-trading-vs-discretionary/)
- **Ignoring sample size**  
  - Many visually compelling patterns (specific variations of sweeps, mitigations, inducements) have very few independent occurrences when defined tightly; overfitting is almost guaranteed.  
- **No separation between research and constitution**  
  - Features used only for exploration quietly leak into production rules without rigorous validation, making the system fragile and opaque.

Architecturally, the anti‑patterns look like: **monolithic rule files tightly coupled to a huge feature matrix**, no versioning of rules vs methodology, and no explicit “retirement” process for features.

### What tends to survive?

Documented successes and positive case studies share patterns: [quantpedia](https://quantpedia.com/combining-discretionary-and-algorithmic-trading/)

- **Narrow scope for automation**  
  - Systems handle: screening, basic setup detection, risk and trade management; the human decides *which* setups to act on.  
  - Quantpedia’s case of combining a discretionary trader with a systematic strategy shows the system providing consistent, rule‑based setups (e.g., gap events) while the trader filters and manages them, yielding better results than either alone. [quantpedia](https://quantpedia.com/combining-discretionary-and-algorithmic-trading/)

- **Simple, robust rules around well‑understood edges**  
  - Trend‑following on processed price series (moving averages, breakouts, structure breaks), volatility timing, session‑based filters. [blog.traderspost](https://blog.traderspost.io/article/trend-following-strategies-guide)
  - These don’t try to reproduce every nuance of a guru’s reading, just the core repeatable mechanics.

- **Clear abstraction boundaries**  
  - A “structure” module, a “regime” module, a “session/seasonality” module, and a “setup detector” module, each with limited responsibilities.  
  - A hybrid workflow in which discretionary traders know exactly what the system is doing, and the system is designed to be *overridden*, not obeyed blindly. [robotwealth](https://robotwealth.com/quant-systematic-trading-vs-discretionary/)

Your human‑in‑the‑loop, gate‑based design is extremely consistent with these survivors; the main challenge is avoiding over‑modeling.

### OHLCV limitations

There’s a broad consensus across academic and practitioner sources:

- OHLCV is enough for:
  - Daily/HTF trend‑following, swing trading, momentum and basic mean‑reversion strategies. [jetwi](http://www.jetwi.us/uploadfile/2014/1223/20141223120018209.pdf)
  - Many structurally simple intraday systems that rely on ranges, breakouts, and time‑of‑day seasonality. [sciencedirect](https://www.sciencedirect.com/science/article/abs/pii/S0889158306000463)

- OHLCV becomes limiting for:
  - Microstructure‑dependent ideas: detailed understanding of liquidity sweeps, stop runs, iceberg behavior, and absorption around key levels. [litefinance](https://www.litefinance.org/blog/for-beginners/trading-strategies/order-flow-trading-with-footprint-charts/)
  - Anything whose explanation fundamentally depends on *who* traded where (aggressive vs passive) rather than simply “price printed here.” [bestorderflow](https://bestorderflow.com/footprint)

Robust order‑flow and footprint traders do rely on per‑price bid/ask volumes, deltas, and imbalance metrics, not just OHLCV. For a constitutional system emulating ICT: [litefinance](https://www.litefinance.org/blog/for-beginners/trading-strategies/order-flow-trading-with-footprint-charts/)

- Your **HTF Bias, basic structure, and time‑of‑day gates** are well within OHLCV’s capabilities.  
- **Liquidity and imbalance ideas** can be approximated, but will remain approximations until you incorporate richer microstructure data.

***

## Concrete Architectural Takeaways for Your System

Given your constraints and goals, a professional‑grade but maintainable design might look like this:

1. **Gate‑first feature registry**  
   - For each gate (HTF bias, structure, PD arrays, entry model, confirmation), catalogue:
     - The human rule in natural language.  
     - The minimal OHLCV‑derived primitives required.  
   - Only these primitives become first‑class features; others go into a separate research sandbox.

2. **Thin, versioned feature layer**  
   - On the order of 30–60 core features:
     - Returns/volatility at several horizons, range measures, volume z‑scores. [alphascientist](https://alphascientist.com/feature_engineering.html)
     - Structure primitives (swing flags, bar‑shape measures).  
     - Time‑/session‑of‑day indicators. [finage.co](https://finage.co.uk/blog/how-to-use-ohlcv-data-to-improve-technical-analysis-in-trading--684007623458598454e3dd10)
   - Everything else is a **function over sequences** (pattern detector) that doesn’t explode your column count.

3. **Deterministic structure engines per TF + confluence**  
   - Explicit, tested state machines that implement your BOS/CHoCH/HH/HL rules per timeframe. [tradingfinder](https://tradingfinder.com/education/forex/ict-higher-highs-higher-lows/)
   - A separate confluence module that encodes how TFs interact, plus optional regime labels (volatility/trend) from a simple or HMM‑style model. [questdb](https://questdb.com/glossary/market-regime-detection-using-hidden-markov-models/)

4. **Strict separation of roles**  
   - “Constitutional” layer: only rules that the expert signs off as representing their methodology.  
   - “Analytics/Research” layer: additional features, metrics, and pattern tests that never directly decide trades without a promotion process.

5. **Explicit acknowledgement of OHLCV’s ceiling**  
   - Accept that some ICT concepts (especially detailed liquidity behavior) are only approximate from bars; design gates accordingly and consider an evolutionary path toward order‑flow data for those drawers.  

If you’d like, next step I can help you blueprint an explicit feature registry for your existing drawers (HTF Bias, Structure, PD, Entry, Confirmation) and mark which of your current ~400 columns are likely constitutional vs experimental vs redundant.