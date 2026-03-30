"""detect_runner — Run ICT structure detection on RiverWriter data.

Vendored from en1gma/phoenix cso/structure_detector.py.
Do NOT modify the vendored code — only vary config parameters.

Usage:
    from tools.detect_runner import run_detection, run_multi_tf

    # Single timeframe detection
    result = run_detection("EURUSD", "15m")
    print(result.to_dict())

    # Multi-timeframe detection
    results = run_multi_tf("EURUSD", ["15m", "1h", "4h"])
"""

from tools.detect_runner.runner import run_detection, run_multi_tf

__all__ = ["run_detection", "run_multi_tf"]
