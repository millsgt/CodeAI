from __future__ import annotations

import pandas as pd


class DataProcessingError(ValueError):
    pass


def read_csv(file_storage) -> pd.DataFrame:
    try:
        dataframe = pd.read_csv(file_storage)
    except pd.errors.EmptyDataError as exc:
        raise DataProcessingError("The uploaded CSV file is empty.") from exc
    except UnicodeDecodeError as exc:
        raise DataProcessingError("The CSV file encoding could not be read.") from exc
    except Exception as exc:
        raise DataProcessingError("The uploaded file could not be parsed as CSV.") from exc

    if dataframe.empty or len(dataframe.columns) == 0:
        raise DataProcessingError("The uploaded CSV file does not contain any data.")

    return dataframe


def get_column_groups(dataframe: pd.DataFrame) -> tuple[list[str], list[str]]:
    numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()
    categorical_columns = [column for column in dataframe.columns if column not in numeric_columns]
    return numeric_columns, categorical_columns


def get_statistics(dataframe: pd.DataFrame) -> dict[str, dict[str, float | int | None]]:
    numeric_dataframe = dataframe.select_dtypes(include="number")
    if numeric_dataframe.empty:
        return {}

    stats = numeric_dataframe.agg(["count", "mean", "median", "std", "min", "max"]).transpose()
    stats = stats.where(pd.notnull(stats), None)
    return stats.round(4).to_dict(orient="index")


def get_filter_options(dataframe: pd.DataFrame, max_values: int = 100) -> dict[str, list[str]]:
    options = {}
    for column in dataframe.columns:
        values = dataframe[column].dropna().astype(str).sort_values().unique().tolist()
        options[column] = values[:max_values]
    return options


def apply_filters(dataframe: pd.DataFrame, filters: dict[str, str]) -> pd.DataFrame:
    filtered = dataframe.copy()
    for column, value in filters.items():
        if not value or column not in filtered.columns:
            continue
        filtered = filtered[filtered[column].astype(str) == value]
    return filtered


def dataframe_preview(dataframe: pd.DataFrame, rows: int = 100) -> dict[str, object]:
    preview = dataframe.head(rows).astype(object).where(pd.notnull(dataframe.head(rows)), None)
    return {
        "columns": preview.columns.tolist(),
        "rows": preview.values.tolist(),
        "total_rows": int(len(dataframe)),
        "shown_rows": int(min(len(dataframe), rows)),
    }
