from __future__ import annotations

from io import BytesIO

import pandas as pd

from app import DATASETS, build_charts, is_allowed_file


def test_index_get_renders_upload_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Upload a CSV file" in response.data
    assert b"Create Dashboard" in response.data


def test_upload_valid_csv_redirects_to_dashboard_and_stores_dataset(client, sample_csv_bytes):
    response = client.post(
        "/",
        data={"csv_file": (BytesIO(sample_csv_bytes), "sample.csv")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert len(DATASETS) == 1


def test_upload_valid_csv_renders_dashboard_content(upload_sample_csv):
    response = upload_sample_csv()

    assert response.status_code == 200
    assert b"Data Preview" in response.data
    assert b"Numeric Statistics" in response.data
    assert b"Histogram" in response.data
    assert b"Categorical Bar Chart" in response.data
    assert b"Correlation Heatmap" in response.data
    assert b"Alice" in response.data
    assert b"Engineering" in response.data


def test_dashboard_without_uploaded_dataset_redirects_to_index(client):
    response = client.get("/dashboard", follow_redirects=True)

    assert response.status_code == 200
    assert b"Upload a CSV file to view the dashboard." in response.data
    assert b"Create Dashboard" in response.data


def test_download_without_uploaded_dataset_redirects_to_index(client):
    response = client.get("/download", follow_redirects=True)

    assert response.status_code == 200
    assert b"Upload a CSV file before downloading results." in response.data


def test_upload_rejects_missing_file(client):
    response = client.post("/", data={}, content_type="multipart/form-data", follow_redirects=True)

    assert response.status_code == 200
    assert b"Please choose a CSV file to upload." in response.data


def test_upload_rejects_invalid_extension(client):
    response = client.post(
        "/",
        data={"csv_file": (BytesIO(b"name,age\nAlice,30\n"), "sample.txt")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid file type. Only CSV files are supported." in response.data
    assert DATASETS == {}


def test_upload_rejects_empty_csv(client):
    response = client.post(
        "/",
        data={"csv_file": (BytesIO(b""), "empty.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"The uploaded CSV file is empty." in response.data
    assert DATASETS == {}


def test_upload_rejects_header_only_csv(client):
    response = client.post(
        "/",
        data={"csv_file": (BytesIO(b"name,age\n"), "header.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"The uploaded CSV file does not contain any data." in response.data
    assert DATASETS == {}


def test_file_too_large_error_redirects_to_index(client, app):
    app.config["MAX_CONTENT_LENGTH"] = 12

    response = client.post(
        "/",
        data={"csv_file": (BytesIO(b"name,age\nAlice,30\n"), "sample.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"File is too large. Maximum upload size is 10MB." in response.data


def test_dashboard_filtering_updates_preview(upload_sample_csv, client):
    upload_sample_csv()

    response = client.get("/dashboard?filter_department=Marketing")

    assert response.status_code == 200
    assert b"Charlie" in response.data
    assert b"Diana" in response.data
    assert b'option value="Marketing" selected' in response.data
    assert b'<div class="h3 mb-0">2</div>' in response.data


def test_dashboard_preserves_selected_chart_columns(upload_sample_csv, client):
    upload_sample_csv()

    response = client.get("/dashboard?histogram_column=salary&bar_column=department")

    assert response.status_code == 200
    assert b'option value="salary" selected' in response.data
    assert b'option value="department" selected' in response.data
    assert b"Histogram: salary" in response.data
    assert b"Top Categories: department" in response.data


def test_download_returns_filtered_csv(upload_sample_csv, client):
    upload_sample_csv()

    response = client.get("/download?filter_department=Engineering")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment; filename=filtered_results.csv" in response.headers["Content-Disposition"]
    assert b"Alice,30,75000,Engineering" in response.data
    assert b"Bob,35,85000,Engineering" in response.data
    assert b"Eve,29,78000,Engineering" in response.data
    assert b"Charlie,28,65000,Marketing" not in response.data


def test_is_allowed_file_accepts_csv_case_insensitively():
    assert is_allowed_file("data.csv")
    assert is_allowed_file("DATA.CSV")
    assert not is_allowed_file("data.xlsx")
    assert not is_allowed_file("csv")


def test_build_charts_with_numeric_and_categorical_data():
    dataframe = pd.DataFrame(
        {
            "department": ["Engineering", "Engineering", "Marketing"],
            "age": [30, 35, 28],
            "salary": [75000, 85000, 65000],
        }
    )

    charts = build_charts(dataframe, "salary", "department")

    assert "Histogram: salary" in charts["histogram"]
    assert "Top Categories: department" in charts["bar"]
    assert "Correlation Heatmap" in charts["heatmap"]


def test_build_charts_handles_non_numeric_data_without_numeric_charts():
    dataframe = pd.DataFrame({"department": ["Engineering", "Marketing"], "name": ["Alice", "Bob"]})

    charts = build_charts(dataframe, None, "department")

    assert charts["histogram"] is None
    assert "Top Categories: department" in charts["bar"]
    assert charts["heatmap"] is None
