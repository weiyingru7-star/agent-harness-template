from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_and_get_txt_file() -> None:
    response = client.post(
        "/api/files/upload",
        files={"file": ("notes.txt", b"hello file", "text/plain")},
    )

    assert response.status_code == 201
    uploaded_file = response.json()
    assert uploaded_file["id"].startswith("file_")
    assert uploaded_file["filename"] == "notes.txt"
    assert uploaded_file["extension"] == ".txt"
    assert uploaded_file["text"] == "hello file"
    assert uploaded_file["storage_path"].endswith(f"{uploaded_file['id']}.txt")

    get_response = client.get(f"/api/files/{uploaded_file['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == uploaded_file["id"]


def test_upload_md_file() -> None:
    response = client.post(
        "/api/files/upload",
        files={"file": ("notes.md", b"# hello", "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json()["extension"] == ".md"


def test_reject_unsupported_file_type() -> None:
    response = client.post(
        "/api/files/upload",
        files={"file": ("image.png", b"not supported", "image/png")},
    )

    assert response.status_code == 400
