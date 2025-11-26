from http import HTTPStatus
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from api import app


class MoviesEndpointsTest(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    async def test_add_movie_ok(self):
        headers = {"Authorization": "Bearer token"}
        query = "title=Test&description=Desc&year=2020&genre=Drama&price=9.99"
        with patch("api.get_user_id", new=AsyncMock(return_value="admin")), \
             patch("api.user.comprobar_token_admin", new=AsyncMock(return_value=True)), \
             patch("api.add_movie", new=AsyncMock(return_value=(True, "OK"))):
            resp = await self.client.put(f"/movies?{query}", headers=headers)
        data = await resp.get_json()
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(data.get("status"), "OK")

    async def test_update_movie_missing_id(self):
        headers = {"Authorization": "Bearer token"}
        with patch("api.get_user_id", new=AsyncMock(return_value="admin")), \
             patch("api.user.comprobar_token_admin", new=AsyncMock(return_value=True)):
            resp = await self.client.post("/movies", headers=headers)
        data = await resp.get_json()
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(data.get("status"), "ERROR")

    async def test_update_movie_not_found(self):
        headers = {"Authorization": "Bearer token"}
        with patch("api.get_user_id", new=AsyncMock(return_value="admin")), \
             patch("api.user.comprobar_token_admin", new=AsyncMock(return_value=True)), \
             patch("api.update_movie", new=AsyncMock(return_value=(False, "NOT_FOUND"))):
            resp = await self.client.post("/movies?movieid=10&title=New", headers=headers)
        data = await resp.get_json()
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(data.get("message"), "Película no encontrada.")

    async def test_delete_movie_ok(self):
        headers = {"Authorization": "Bearer token"}
        with patch("api.get_user_id", new=AsyncMock(return_value="admin")), \
             patch("api.user.comprobar_token_admin", new=AsyncMock(return_value=True)), \
             patch("api.remove_movie", new=AsyncMock(return_value=(True, "OK"))):
            resp = await self.client.delete("/movies?movieid=5", headers=headers)
        data = await resp.get_json()
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(data.get("status"), "OK")
