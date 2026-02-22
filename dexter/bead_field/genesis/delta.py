"""METHODOLOGY_DELTA bead builder — records v0.1 -> v0.3 corrections.

Each of Olya's 13 corrections as structured entries.
bead_type: POLICY (methodology change record)
temporal_class: PATTERN (timeless — methodology, not market observation)
"""

from bead_field.schema.enums import PolicyType

OLYA_CORRECTIONS_V03 = [
    {"id": 1, "concept": "Equilibrium", "change": "Can still enter with full confluence (not automatic wait)", "action": "MODIFIED"},
    {"id": 2, "concept": "CBDR", "change": "Removed entirely (not used)", "action": "REMOVED"},
    {"id": 3, "concept": "Asia Range", "change": "Locked to 19:00-00:00 NY, must be under 30 pips", "action": "MODIFIED"},
    {"id": 4, "concept": "Misalignment", "change": "Can still take scalps on LTF, 1% risk", "action": "MODIFIED"},
    {"id": 5, "concept": "Judas Swing", "change": "= Liquidity Sweep — same concept, 30-40 pip max", "action": "CLARIFIED"},
    {"id": 6, "concept": "FVG Respected", "change": "Bodies must stay inside, wicks can break", "action": "MODIFIED"},
    {"id": 7, "concept": "SMT", "change": "Removed entirely for now", "action": "REMOVED"},
    {"id": 8, "concept": "Position Sizing", "change": "Removed calculation formula (system handles)", "action": "REMOVED"},
    {"id": 9, "concept": "Stop Loss", "change": "By swings not pips", "action": "MODIFIED"},
    {"id": 10, "concept": "Time Stop", "change": "Removed entirely (not used)", "action": "REMOVED"},
    {"id": 11, "concept": "Structure Break Exit", "change": "Removed entirely (not used now)", "action": "REMOVED"},
    {"id": 12, "concept": "Session Close", "change": "No new entries after NYOKZ, overnight holds OK if structure intact", "action": "MODIFIED"},
    {"id": 13, "concept": "Chart Setup / Sessions / News", "change": "Full update with correct times and rules", "action": "MODIFIED"},
]


def build_delta_content() -> dict:
    """Build the METHODOLOGY_DELTA POLICY bead content."""
    return {
        "policy_name": "METHODOLOGY_DELTA_v0.1_to_v0.3",
        "policy_type": PolicyType.OPERATIONAL.value,
        "rules": {
            "description": "Records all methodology corrections from Olya validation (v0.1 -> v0.3)",
            "validated_by": "Olya",
            "validation_date": "2026-02-12",
            "total_corrections": len(OLYA_CORRECTIONS_V03),
            "corrections": OLYA_CORRECTIONS_V03,
            "removed_concepts": ["CBDR", "SMT", "Time Stop", "Structure Break Exit", "Position Sizing Formula"],
        },
        "effective_from": "2026-02-12T00:00:00+00:00",
        "effective_to": None,
        "supersedes": None,
        "authority": "Olya",
    }
