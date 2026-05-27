from __future__ import annotations

import io
import json
import uuid
from pathlib import Path

import pandas as pd
import plotly.express as px
from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from utils.data_processor import (
    DataProcessingError,
    apply_filters,
    dataframe_preview,
    get_column_groups,
    get_filter_options,
    get_statistics,
    read_csv,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-change-me"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["UPLOAD_EXTENSIONS"] = {".csv"}

DATASETS: dict[str, pd.DataFrame] = {}


def is_allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in app.config["UPLOAD_EXTENSIONS"]


def build_charts(dataframe: pd.DataFrame, histogram_column: str | None, bar_column: str | None) -> dict[str, str | None]:
    numeric_columns, categorical_columns = get_column_groups(dataframe)
    charts = {"histogram": None, "bar": None, "heatmap": None}

    if numeric_columns:
        selected_histogram = histogram_column if histogram_column in numeric_columns else numeric_columns[0]
        histogram = px.histogram(dataframe, x=selected_histogram, title=f"Histogram: {selected_histogram}")
        charts["histogram"] = histogram.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    if categorical_columns:
        selected_bar = bar_column if bar_column in categorical_columns else categorical_columns[0]
        counts = dataframe[selected_bar].astype(str).value_counts().head(25).reset_index()
        counts.columns = [selected_bar, "count"]
        bar = px.bar(counts, x=selected_bar, y="count", title=f"Top Categories: {selected_bar}")
        charts["bar"] = bar.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    if len(numeric_columns) >= 2:
        correlation = dataframe[numeric_columns].corr(numeric_only=True)
        heatmap = px.imshow(
            correlation,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Correlation Heatmap",
        )
        charts["heatmap"] = heatmap.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    return charts


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    flash("File is too large. Maximum upload size is 10MB.", "danger")
    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("csv_file")

        if not uploaded_file or uploaded_file.filename == "":
            flash("Please choose a CSV file to upload.", "warning")
            return redirect(url_for("index"))

        filename = secure_filename(uploaded_file.filename)
        if not is_allowed_file(filename):
            flash("Invalid file type. Only CSV files are supported.", "danger")
            return redirect(url_for("index"))

        try:
            dataframe = read_csv(uploaded_file)
        except DataProcessingError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("index"))

        dataset_id = uuid.uuid4().hex
        DATASETS[dataset_id] = dataframe
        session["dataset_id"] = dataset_id
        session["filename"] = filename
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    dataset_id = session.get("dataset_id")
    dataframe = DATASETS.get(dataset_id or "")

    if dataframe is None:
        flash("Upload a CSV file to view the dashboard.", "info")
        return redirect(url_for("index"))

    filters = {key.removeprefix("filter_"): value for key, value in request.args.items() if key.startswith("filter_") and value}
    filtered = apply_filters(dataframe, filters)
    numeric_columns, categorical_columns = get_column_groups(filtered)
    histogram_column = request.args.get("histogram_column")
    bar_column = request.args.get("bar_column")

    return render_template(
        "dashboard.html",
        filename=session.get("filename", "dataset.csv"),
        preview=dataframe_preview(filtered),
        statistics=get_statistics(filtered),
        filter_options=get_filter_options(dataframe),
        active_filters=filters,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        selected_histogram=histogram_column if histogram_column in numeric_columns else (numeric_columns[0] if numeric_columns else ""),
        selected_bar=bar_column if bar_column in categorical_columns else (categorical_columns[0] if categorical_columns else ""),
        charts=build_charts(filtered, histogram_column, bar_column),
    )


@app.route("/download")
def download():
    dataset_id = session.get("dataset_id")
    dataframe = DATASETS.get(dataset_id or "")

    if dataframe is None:
        flash("Upload a CSV file before downloading results.", "info")
        return redirect(url_for("index"))

    filters = {key.removeprefix("filter_"): value for key, value in request.args.items() if key.startswith("filter_") and value}
    filtered = apply_filters(dataframe, filters)
    buffer = io.StringIO()
    filtered.to_csv(buffer, index=False)

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=filtered_results.csv"},
    )


@app.template_filter("tojson_safe")
def tojson_safe(value):
    return json.dumps(value)


if __name__ == "__main__":
    app.run(debug=True)
