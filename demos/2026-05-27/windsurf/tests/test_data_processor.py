from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from utils.data_processor import (
    DataProcessingError,
    apply_filters,
    dataframe_preview,
    get_column_groups,
    get_filter_options,
    get_statistics,
    read_csv,
)


def test_read_csv_returns_dataframe_for_valid_csv():
    dataframe = read_csv(BytesIO(b"name,age\nAlice,30\nBob,35\n"))

    assert dataframe.shape == (2, 2)
    assert dataframe["name"].tolist() == ["Alice", "Bob"]
    assert dataframe["age"].tolist() == [30, 35]


def test_read_csv_raises_for_empty_file():
    with pytest.raises(DataProcessingError, match="empty"):
        read_csv(BytesIO(b""))


def test_read_csv_raises_for_header_only_file():
    with pytest.raises(DataProcessingError, match="does not contain any data"):
        read_csv(BytesIO(b"name,age\n"))


def test_get_column_groups_splits_numeric_and_categorical_columns():
    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "age": [30, 35],
            "salary": [75000.0, 85000.0],
            "department": ["Engineering", "Marketing"],
        }
    )

    numeric_columns, categorical_columns = get_column_groups(dataframe)

    assert numeric_columns == ["age", "salary"]
    assert categorical_columns == ["name", "department"]


def test_get_statistics_calculates_expected_metrics():
    dataframe = pd.DataFrame({"age": [30, 35, 25], "department": ["A", "A", "B"]})

    statistics = get_statistics(dataframe)

    assert statistics["age"]["count"] == 3
    assert statistics["age"]["mean"] == 30
    assert statistics["age"]["median"] == 30
    assert statistics["age"]["min"] == 25
    assert statistics["age"]["max"] == 35
    assert "department" not in statistics


def test_get_statistics_returns_empty_dict_without_numeric_columns():
    dataframe = pd.DataFrame({"department": ["Engineering", "Marketing"]})

    assert get_statistics(dataframe) == {}


def test_get_filter_options_sorts_deduplicates_and_limits_values():
    dataframe = pd.DataFrame({"department": ["Marketing", "Engineering", "Engineering", None, "Sales"]})

    options = get_filter_options(dataframe, max_values=2)

    assert options == {"department": ["Engineering", "Marketing"]}


def test_apply_filters_matches_values_as_strings_and_ignores_unknown_columns():
    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 35, 30],
            "department": ["Engineering", "Engineering", "Marketing"],
        }
    )

    filtered = apply_filters(dataframe, {"age": "30", "missing": "value", "department": ""})

    assert filtered["name"].tolist() == ["Alice", "Charlie"]


def test_dataframe_preview_limits_rows_and_replaces_missing_values():
    dataframe = pd.DataFrame({"name": ["Alice", None, "Charlie"], "age": [30, 35, None]})

    preview = dataframe_preview(dataframe, rows=2)

    assert preview["columns"] == ["name", "age"]
    assert preview["total_rows"] == 3
    assert preview["shown_rows"] == 2
    assert preview["rows"][1][0] is None
