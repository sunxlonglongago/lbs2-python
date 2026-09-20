"""Shared helpers for the API end to end scenarios."""

from __future__ import annotations

import json
from typing import Any


class Context:
    """Thin wrapper around Flask's test client, one client per identity."""

    def __init__(self, app_module, data_dir):
        self.module = app_module
        self.app = app_module.app
        # Local http: keep the session cookie usable inside the test client.
        self.app.config["SESSION_COOKIE_SECURE"] = False
        self.data_dir = data_dir
        self._clients: dict[str, Any] = {}
        self.checks = 0
        self.failures: list[str] = []
        self.case_log: list[str] = []

    def client(self, identity: str = "anonymous"):
        if identity not in self._clients:
            self._clients[identity] = self.app.test_client()
        return self._clients[identity]

    def request(self, identity: str, method: str, path: str, **kwargs):
        client = self.client(identity)
        if "json" in kwargs:
            kwargs.setdefault("content_type", "application/json")
        response = getattr(client, method)(path, **kwargs)
        payload = None
        if response.content_type and "json" in response.content_type:
            try:
                payload = response.get_json()
            except Exception:  # pragma: no cover - defensive
                payload = None
        return response, payload

    def get(self, identity, path, **kwargs):
        return self.request(identity, "get", path, **kwargs)

    def post(self, identity, path, **kwargs):
        return self.request(identity, "post", path, **kwargs)

    def patch(self, identity, path, **kwargs):
        return self.request(identity, "patch", path, **kwargs)

    def delete(self, identity, path, **kwargs):
        return self.request(identity, "delete", path, **kwargs)

    def login(self, identity: str, username: str, password: str, remember: bool = False):
        return self.post(
            identity,
            "/api/auth/login",
            json={"username": username, "password": password, "remember": remember},
        )

    def admin_login(self, identity: str = "admin", password: str = "comeon"):
        return self.post(identity, "/api/admin/login", json={"password": password})

    def check(self, condition: bool, message: str) -> bool:
        self.checks += 1
        if not condition:
            self.failures.append(message)
        return bool(condition)

    def check_status(self, response, expected: int, message: str) -> bool:
        return self.check(
            response.status_code == expected,
            f"{message} (expected {expected}, got {response.status_code})",
        )

    def check_equal(self, actual, expected, message: str) -> bool:
        return self.check(
            actual == expected,
            f"{message} (expected {expected!r}, got {actual!r})",
        )

    def case(self, name: str) -> None:
        self.case_log.append(name)

    def dump(self, payload) -> str:
        return json.dumps(payload, ensure_ascii=False, default=str)[:400]
