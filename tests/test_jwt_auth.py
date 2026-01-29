"""Tests for JWT authentication."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import bcrypt
import jwt
import respx
from httpx import ASGITransport, AsyncClient, Response

from weather_api.main import app
from weather_api.services.weather import GEOCODING_URL, WEATHER_URL

TEST_SECRET = "test-secret-key"  # noqa: S105
TEST_ALGORITHM = "HS256"


def _mock_weather_apis() -> None:
    """Set up mocks for geocoding and weather APIs."""
    respx.get(GEOCODING_URL).mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "name": "London",
                        "latitude": 51.5074,
                        "longitude": -0.1278,
                    }
                ]
            },
        )
    )
    respx.get(WEATHER_URL).mock(
        return_value=Response(
            200,
            json={
                "current": {
                    "temperature_2m": 15.5,
                    "relative_humidity_2m": 72,
                    "wind_speed_10m": 12.3,
                    "weather_code": 2,
                }
            },
        )
    )


def _create_token(username: str, expired: bool = False) -> str:
    """Create a test JWT token."""
    if expired:
        exp = datetime.now(UTC) - timedelta(hours=1)
    else:
        exp = datetime.now(UTC) + timedelta(hours=1)
    payload = {"sub": username, "exp": exp}
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@respx.mock
async def test_jwt_enabled_missing_token_returns_401() -> None:
    """When JWT is enabled, missing token returns 401."""
    _mock_weather_apis()

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = True
        mock_settings.api_key_enabled = False
        mock_settings.jwt_secret = TEST_SECRET
        mock_settings.jwt_algorithm = TEST_ALGORITHM

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/forecast/London")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authentication"


@respx.mock
async def test_jwt_enabled_invalid_token_returns_401() -> None:
    """When JWT is enabled, invalid token returns 401."""
    _mock_weather_apis()

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = True
        mock_settings.api_key_enabled = False
        mock_settings.jwt_secret = TEST_SECRET
        mock_settings.jwt_algorithm = TEST_ALGORITHM

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/forecast/London",
                headers={"Authorization": "Bearer invalid-token"},
            )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@respx.mock
async def test_jwt_enabled_expired_token_returns_401() -> None:
    """When JWT is enabled, expired token returns 401."""
    _mock_weather_apis()
    token = _create_token("testuser", expired=True)

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = True
        mock_settings.api_key_enabled = False
        mock_settings.jwt_secret = TEST_SECRET
        mock_settings.jwt_algorithm = TEST_ALGORITHM

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/forecast/London",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


@respx.mock
async def test_jwt_enabled_valid_token_returns_200() -> None:
    """When JWT is enabled, valid token returns 200."""
    _mock_weather_apis()
    token = _create_token("testuser")

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = True
        mock_settings.api_key_enabled = False
        mock_settings.jwt_secret = TEST_SECRET
        mock_settings.jwt_algorithm = TEST_ALGORITHM

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/forecast/London",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"


@respx.mock
async def test_both_auth_methods_jwt_takes_precedence() -> None:
    """When both auth methods enabled, valid JWT works."""
    _mock_weather_apis()
    token = _create_token("testuser")

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = True
        mock_settings.api_key_enabled = True
        mock_settings.jwt_secret = TEST_SECRET
        mock_settings.jwt_algorithm = TEST_ALGORITHM
        mock_settings.api_keys = {"valid-key"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/forecast/London",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200


@respx.mock
async def test_both_auth_methods_api_key_works() -> None:
    """When both auth methods enabled, API key also works."""
    _mock_weather_apis()

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = True
        mock_settings.api_key_enabled = True
        mock_settings.jwt_secret = TEST_SECRET
        mock_settings.jwt_algorithm = TEST_ALGORITHM
        mock_settings.api_keys = {"valid-key"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/forecast/London",
                headers={"X-API-Key": "valid-key"},
            )

    assert response.status_code == 200


async def test_login_jwt_disabled_returns_503() -> None:
    """Login returns 503 when JWT is disabled."""
    with patch("weather_api.routes.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = False

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/auth/login",
                json={"username": "testuser", "password": "testpass"},
            )

    assert response.status_code == 503
    assert response.json()["detail"] == "JWT authentication not enabled"


def _hash_password(password: str) -> str:
    """Hash a password for testing."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def test_login_invalid_credentials_returns_401() -> None:
    """Login with invalid credentials returns 401."""
    with patch("weather_api.routes.auth.settings") as mock_settings:
        mock_settings.jwt_enabled = True
        mock_settings.jwt_users = {"testuser": _hash_password("correctpass")}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/auth/login",
                json={"username": "testuser", "password": "wrongpass"},
            )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_login_valid_credentials_returns_token() -> None:
    """Login with valid credentials returns JWT token."""
    password_hash = _hash_password("testpass")

    with (
        patch("weather_api.routes.auth.settings") as route_settings,
        patch("weather_api.auth.settings") as auth_settings,
    ):
        route_settings.jwt_enabled = True
        route_settings.jwt_users = {"testuser": password_hash}
        auth_settings.jwt_secret = TEST_SECRET
        auth_settings.jwt_algorithm = TEST_ALGORITHM
        auth_settings.jwt_expiration_minutes = 30

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/auth/login",
                json={"username": "testuser", "password": "testpass"},
            )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"  # noqa: S105

    # Verify the token is valid
    payload = jwt.decode(data["access_token"], TEST_SECRET, algorithms=[TEST_ALGORITHM])
    assert payload["sub"] == "testuser"
