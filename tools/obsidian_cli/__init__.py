"""obsidian_cli — Read/write structured documents in the Lab vault.

Vault structure:
    ~/lab/vault/
        hypotheses/     Active research questions
        experiments/    Experiment logs + results
        findings/       Validated discoveries
        dead_ends/      Tested and rejected
        proposals/      Ready for human review
        weekly_reviews/ Weekly synthesis

Usage:
    from tools.obsidian_cli import vault_write, vault_read, vault_list

    vault_write("hypotheses", "SILVER_BULLET", {
        "track": "TRACK_1_STRATEGY_SCOUTING",
        "question": "Can Silver Bullet be expressed as a Map config?",
        "status": "ACTIVE",
    }, body="## Method\n1. Research ICT Silver Bullet...")

    doc = vault_read("hypotheses", "SILVER_BULLET")
    docs = vault_list("hypotheses")
"""

from tools.obsidian_cli.vault import vault_write, vault_read, vault_list, vault_list_all

__all__ = ["vault_write", "vault_read", "vault_list", "vault_list_all"]
