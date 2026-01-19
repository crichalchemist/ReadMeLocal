"""Tests for annotation API endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_create_annotation():
    """POST /api/annotations should create an annotation."""
    response = client.post("/api/annotations", json={
        "book_id": "test-book-123",
        "paragraph_index": 5,
        "section_title": "Chapter 1",
        "source_text": "This is the source paragraph.",
        "note_text": "My note about this."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["book_id"] == "test-book-123"
    assert data["note_text"] == "My note about this."
    assert "id" in data


def test_list_annotations():
    """GET /api/annotations/{book_id} should list annotations for a book."""
    # First create one
    client.post("/api/annotations", json={
        "book_id": "list-test-book",
        "paragraph_index": 1,
        "source_text": "Source text.",
        "note_text": "Note text."
    })

    response = client.get("/api/annotations/list-test-book")
    assert response.status_code == 200
    data = response.json()
    assert "annotations" in data
    assert data["total"] >= 1


def test_delete_annotation():
    """DELETE /api/annotations/{id} should delete an annotation."""
    # Create one first
    create_resp = client.post("/api/annotations", json={
        "book_id": "delete-test-book",
        "paragraph_index": 1,
        "source_text": "Source.",
        "note_text": "Note."
    })
    annotation_id = create_resp.json()["id"]

    # Delete it
    delete_resp = client.delete(f"/api/annotations/{annotation_id}")
    assert delete_resp.status_code == 200

    # Verify it's gone
    list_resp = client.get("/api/annotations/delete-test-book")
    ids = [a["id"] for a in list_resp.json()["annotations"]]
    assert annotation_id not in ids


def test_export_annotations():
    """GET /api/annotations/{book_id}/export should return TXT export."""
    # Create an annotation
    client.post("/api/annotations", json={
        "book_id": "export-test-book",
        "paragraph_index": 0,
        "section_title": "Introduction",
        "source_text": "The quick brown fox.",
        "note_text": "This is about a fox."
    })

    response = client.get("/api/annotations/export-test-book/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    content = response.text
    assert "The quick brown fox" in content
    assert "This is about a fox" in content
