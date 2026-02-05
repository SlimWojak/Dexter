# core — Stable micro-kernel (nanobot-derived)
from core.context import append_bead, read_beads, count_beads, needs_compression
from core.injection_guard import scan as injection_scan, InjectionDetected
from core.chronicler import compress_beads, compute_similarity, needs_compression_check
