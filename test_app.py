from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pathlib import Path
import os
import requests_mock
import pytest

load_dotenv("tests/.env.test")

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_file_path():
    return Path(__file__).parent / "tests/test_file.pdf"


@pytest.fixture(autouse=True)
# @pytest.fixture()
def teardown():
    # file = Path(__file__).parent / f"{os.getenv("OUTPUT_FOLDER")}/test_page.txt"
    # file.unlink()
    print("test")


def test_upload_file_with_arguments(client, test_file_path):
    with requests_mock.Mocker() as m:
        m.get(
            "http://localhost/api.php",
            json={
                "batchcomplete": "",
                "query": {
                    "tokens": {
                        "logintoken": "1a033b71d2973e4110448f69d65591ef691d95c8+\\",
                        "csrftoken": "1a033b71d2973e4",
                    }
                },
            },
        )
        m.post(
            "http://localhost/api.php",
            json={
                "login": {"result": "Success"},
                "upload": {"result": "Success"},
                "edit": {"result": "Success", "new": "", "title": "Test page"},
            },
            status_code=200,
        )

        with open(test_file_path, "rb") as f:
            response = client.post(
                "/pdf-to-wikitext",
                files={"file": ("test_file.pdf", f, "application/pdf")},
                data={
                    "footer": "Test document",
                    "ignore_pages": "",
                    "page_name": "Test page",
                    "generate_page": "true",
                },
            )
            assert response.status_code == 200

    file = Path(__file__).parent / f"{os.getenv("OUTPUT_FOLDER")}/test_page.md"
    content = file.read_text()
    assert file.exists(), f"File {file} not exist"
    assert "Test document **0**" in content
    assert "|Test1|Description 1||" in content
    assert "**1.2** **Menu for table**" in content
    assert "![](./tests/images/test_file/test_page.pdf-1-0.png)" in content

    file = Path(__file__).parent / f"{os.getenv("OUTPUT_FOLDER")}/test_page.txt"
    content = file.read_text()
    assert file.exists(), f"File {file} not exist"
    assert "Test document **0**" not in content
    assert "|Test1|Description 1||" not in content
    assert "**1.2** **Menu for table**" not in content
    assert "'''First page title'''" in content
    assert "=== 1.1 Menu level 2 ===" in content
    assert "| Test1 || Description 1" in content
    assert "[[File:test_page 0.png|center|thumb]]" in content

    dir_path = Path(__file__).parent / f"{os.getenv("OUTPUT_FOLDER")}"
    log_files = list(dir_path.glob("test_page_pdf_to_wikitext*.log"))
    if log_files:
        latest_log_file = max(log_files, key=lambda f: f.stat().st_mtime)
        content = latest_log_file.read_text()
        assert ": Init application" in content
        assert ": Create temporary file" in content
        assert ": Transform Pdf content to md text and store image" in content
        assert ": Remove temporary file" in content
        assert ": Create md file" in content
        assert ": Transform MD to wikitext and create image on Mediawiki" in content
        assert "Connection as adminUser..." in content
        assert "Connection done" in content
        assert "Upload of test_page 0.png..." in content
        assert "test_page 0.png uploaded with success" in content
        assert ": Remove image folder" in content
        assert ": Create wikitext file" in content
        assert ": Annotate wikitext with ontology" in content
        assert ": Create Mediawiki page" in content
        assert "Connection as adminUser..." in content
        assert "Connection done" in content
        assert "Page 'test_page' created/modified successfully" in content
        assert "New page created" in content
        assert (
            "Page generation result: http://localhost/index.php?title=Test page"
            in content
        )
