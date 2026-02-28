"""Tests for timestamp normalization — T2 gate."""

import pytest
from bead_field.query.timestamps import normalize_timestamp, normalize_params


class TestNormalizeTimestamp:
    def test_naive_iso_appends_utc(self):
        assert normalize_timestamp("2024-01-15T14:30:00") == "2024-01-15T14:30:00+00:00"

    def test_z_suffix_replaced(self):
        assert normalize_timestamp("2024-01-15T14:30:00Z") == "2024-01-15T14:30:00+00:00"

    def test_utc_offset_passthrough(self):
        assert normalize_timestamp("2024-01-15T14:30:00+00:00") == "2024-01-15T14:30:00+00:00"

    def test_positive_offset_converted_to_utc(self):
        result = normalize_timestamp("2024-01-15T21:30:00+07:00")
        assert result == "2024-01-15T14:30:00+00:00"

    def test_negative_offset_converted_to_utc(self):
        result = normalize_timestamp("2024-01-15T09:30:00-05:00")
        assert result == "2024-01-15T14:30:00+00:00"

    def test_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_timestamp("not-a-date")

    def test_none_raises_type_error(self):
        with pytest.raises(TypeError):
            normalize_timestamp(None)

    def test_non_string_raises_type_error(self):
        with pytest.raises(TypeError):
            normalize_timestamp(12345)

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_timestamp("")

    def test_midnight_boundary(self):
        result = normalize_timestamp("2024-01-16T02:00:00+09:00")
        assert result == "2024-01-15T17:00:00+00:00"

    def test_day_rollback_from_offset(self):
        result = normalize_timestamp("2024-01-15T01:00:00+05:00")
        assert result == "2024-01-14T20:00:00+00:00"

    def test_whitespace_stripped(self):
        assert normalize_timestamp("  2024-01-15T14:30:00Z  ") == "2024-01-15T14:30:00+00:00"


class TestNormalizeParams:
    def test_tuple_params_normalized(self):
        result = normalize_params(("2024-01-15T14:30:00", "2024-01-16T00:00:00"))
        assert result == ("2024-01-15T14:30:00+00:00", "2024-01-16T00:00:00+00:00")

    def test_list_params_normalized(self):
        result = normalize_params(["2024-01-15T14:30:00Z"])
        assert result == ["2024-01-15T14:30:00+00:00"]

    def test_dict_params_normalized(self):
        result = normalize_params({"ts": "2024-01-15T14:30:00"})
        assert result == {"ts": "2024-01-15T14:30:00+00:00"}

    def test_non_timestamp_strings_passthrough(self):
        result = normalize_params(("hello", 42, None))
        assert result == ("hello", 42, None)

    def test_mixed_params(self):
        result = normalize_params(("2024-01-15T14:30:00", "EURUSD", 100))
        assert result == ("2024-01-15T14:30:00+00:00", "EURUSD", 100)
