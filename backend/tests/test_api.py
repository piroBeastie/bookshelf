def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_root_reports_service_name(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "BookShelf API"


def test_metrics_endpoint_is_prometheus_format(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_create_book(client):
    response = client.post(
        "/api/books",
        json={"title": "Clean Code", "author": "Robert Martin", "pages": 464},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Clean Code"
    assert body["shelf"] == "WANT"
    assert body["id"] > 0


def test_create_book_rejects_bad_rating(client):
    response = client.post(
        "/api/books",
        json={"title": "Bad Input", "author": "Nobody", "rating": 9},
    )
    assert response.status_code == 422


def test_list_books_returns_created_book(client, sample_book):
    response = client.get("/api/books")
    assert response.status_code == 200
    titles = [book["title"] for book in response.json()]
    assert sample_book["title"] in titles


def test_list_books_can_filter_by_shelf(client, sample_book):
    assert len(client.get("/api/books?shelf=READING").json()) == 1
    assert client.get("/api/books?shelf=FINISHED").json() == []


def test_get_single_book_and_404(client, sample_book):
    assert client.get(f"/api/books/{sample_book['id']}").status_code == 200
    missing = client.get("/api/books/9999")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Book not found"


def test_update_book(client, sample_book):
    response = client.put(
        f"/api/books/{sample_book['id']}",
        json={"shelf": "FINISHED", "rating": 5},
    )
    assert response.status_code == 200
    assert response.json()["shelf"] == "FINISHED"
    assert response.json()["rating"] == 5


def test_delete_book(client, sample_book):
    assert client.delete(f"/api/books/{sample_book['id']}").status_code == 204
    assert client.get(f"/api/books/{sample_book['id']}").status_code == 404


def test_stats_counts_pages_and_rating(client):
    client.post(
        "/api/books",
        json={"title": "Done One", "author": "A", "pages": 300, "shelf": "FINISHED", "rating": 4},
    )
    client.post(
        "/api/books",
        json={"title": "Done Two", "author": "B", "pages": 200, "shelf": "FINISHED", "rating": 5},
    )
    client.post("/api/books", json={"title": "Later", "author": "C", "pages": 100})

    stats = client.get("/api/books/stats").json()
    assert stats["total"] == 3
    assert stats["finished"] == 2
    assert stats["want"] == 1
    assert stats["pagesRead"] == 500
    assert stats["averageRating"] == 4.5
