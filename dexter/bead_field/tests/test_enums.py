"""Test enum completeness and correctness (Phase A)."""

from bead_field.schema.enums import (
    BeadType, TemporalClass, BeadStatus, SourceType, Direction,
    ProposalAction, RejectionSource, RejectionCategory,
    SkillType, SkillValidation, DeploymentStatus, PolicyType,
    Drawer, PositionSizeUnit, DataQuality,
)


class TestBeadType:
    def test_has_all_8_types(self):
        assert len(BeadType) == 8

    def test_values_are_strings(self):
        for bt in BeadType:
            assert isinstance(bt.value, str)

    def test_expected_members(self):
        expected = {"FACT", "CLAIM", "SIGNAL", "PROPOSAL", "PROPOSAL_REJECTED",
                    "SKILL", "MODEL_VERSION", "POLICY"}
        assert {bt.value for bt in BeadType} == expected


class TestTemporalClass:
    def test_has_3_classes(self):
        assert len(TemporalClass) == 3

    def test_expected_members(self):
        assert {tc.value for tc in TemporalClass} == {"OBSERVATION", "PATTERN", "DERIVED"}


class TestBeadStatus:
    def test_has_3_statuses(self):
        assert len(BeadStatus) == 3

    def test_expected_members(self):
        assert {bs.value for bs in BeadStatus} == {"ACTIVE", "SUPERSEDED", "RETRACTED"}


class TestSourceType:
    def test_has_6_types(self):
        assert len(SourceType) == 6

    def test_includes_open_source(self):
        assert SourceType.OPEN_SOURCE.value == "OPEN_SOURCE"


class TestDirection:
    def test_has_3_directions(self):
        assert len(Direction) == 3


class TestProposalAction:
    def test_has_5_actions(self):
        assert len(ProposalAction) == 5


class TestRejectionSource:
    def test_has_4_sources(self):
        assert len(RejectionSource) == 4


class TestRejectionCategory:
    def test_has_8_categories(self):
        assert len(RejectionCategory) == 8

    def test_risk_breach_present(self):
        assert RejectionCategory.RISK_BREACH.value == "RISK_BREACH"

    def test_human_override_present(self):
        assert RejectionCategory.HUMAN_OVERRIDE.value == "HUMAN_OVERRIDE"


class TestSkillType:
    def test_has_5_types(self):
        assert len(SkillType) == 5


class TestSkillValidation:
    def test_has_4_statuses(self):
        assert len(SkillValidation) == 4

    def test_expected_progression(self):
        vals = [sv.value for sv in SkillValidation]
        assert vals == ["CANDIDATE", "VALIDATED", "PROMOTED", "DEPRECATED"]


class TestDeploymentStatus:
    def test_has_4_statuses(self):
        assert len(DeploymentStatus) == 4


class TestPolicyType:
    def test_has_4_types(self):
        assert len(PolicyType) == 4


class TestDrawer:
    def test_has_5_drawers(self):
        assert len(Drawer) == 5

    def test_five_drawer_system(self):
        expected = {"HTF_BIAS", "MARKET_STRUCTURE", "PREMIUM_DISCOUNT",
                    "ENTRY_MODEL", "CONFIRMATION"}
        assert {d.value for d in Drawer} == expected


class TestPositionSizeUnit:
    def test_has_4_units(self):
        assert len(PositionSizeUnit) == 4


class TestDataQuality:
    def test_has_4_levels(self):
        assert len(DataQuality) == 4

    def test_expected_members(self):
        assert {dq.value for dq in DataQuality} == {"NOMINAL", "DEGRADED", "PARTIAL", "ERROR"}


class TestAllEnums:
    def test_total_enum_count(self):
        """Verify we have all 15 enums defined."""
        all_enums = [
            BeadType, TemporalClass, BeadStatus, SourceType, Direction,
            ProposalAction, RejectionSource, RejectionCategory,
            SkillType, SkillValidation, DeploymentStatus, PolicyType,
            Drawer, PositionSizeUnit, DataQuality,
        ]
        assert len(all_enums) == 15

    def test_all_enums_are_str_enums(self):
        """Every enum value must be a plain string for JSON serialization."""
        all_enums = [
            BeadType, TemporalClass, BeadStatus, SourceType, Direction,
            ProposalAction, RejectionSource, RejectionCategory,
            SkillType, SkillValidation, DeploymentStatus, PolicyType,
            Drawer, PositionSizeUnit, DataQuality,
        ]
        for enum_cls in all_enums:
            for member in enum_cls:
                assert isinstance(member.value, str), (
                    f"{enum_cls.__name__}.{member.name} value is not str"
                )
