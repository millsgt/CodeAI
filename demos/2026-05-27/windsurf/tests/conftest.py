from __future__ import annotations

from io import BytesIO

import pytest

from app import DATASETS, app as flask_app


@pytest.fixture
def app():
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret",
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    )
    DATASETS.clear()
    yield flask_app
    DATASETS.clear()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_csv_bytes():
    return b"name,age,salary,department\nAlice,30,75000,Engineering\nBob,35,85000,Engineering\nCharlie,28,65000,Marketing\nDiana,32,72000,Marketing\nEve,29,78000,Engineering\n"


@pytest.fixture
def upload_sample_csv(client, sample_csv_bytes):
    def _upload(filename="sample.csv", follow_redirects=True):
        return client.post(
            "/",
            data={"csv_file": (BytesIO(sample_csv_bytes), filename)},
            content_type="multipart/form-data",
            follow_redirects=follow_redirects,
        )

    return _upload
