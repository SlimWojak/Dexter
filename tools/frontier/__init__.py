"""frontier — Call frontier LLMs for judgment, review, and research.

INV-FRONTIER-FOR-JUDGMENT: Opus/GPT/Perplexity are for judgment, not grinding.
Qwen does all iteration. Frontier models are called for:
  - "Is this result genuine or an artefact?" (Claude Opus)
  - "Does this strategy have ICT methodological grounding?" (Perplexity)
  - "What are the overfitting risks?" (GPT)
  - "Pressure test this design" (Claude Opus)
  - Code review or donkey work (DeepSeek)

Usage:
    from tools.frontier import ask_opus, ask_gpt, ask_deepseek, ask_perplexity, ask_gemini

    review = ask_opus("Review this strategy for overfitting risks: ...")
    research = ask_perplexity("What is ICT Silver Bullet methodology?")
    opinion = ask_gpt("Pressure test this experimental design: ...")
    code = ask_deepseek("Write a function to compute FVG fill percentage...")
    summary = ask_gemini("Summarise these 10 experiment results: ...")
"""

from tools.frontier.caller import (
    ask_opus,
    ask_gpt,
    ask_deepseek,
    ask_perplexity,
    ask_gemini,
    ask_frontier,
)

__all__ = [
    "ask_opus",
    "ask_gpt",
    "ask_deepseek",
    "ask_perplexity",
    "ask_gemini",
    "ask_frontier",
]
