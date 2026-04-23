from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app


class PrototypeScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_healthz(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_seeded_item_detail(self) -> None:
        response = self.client.get("/items/demo-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")

    def test_missing_item_returns_404(self) -> None:
        response = self.client.get("/items/missing")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()