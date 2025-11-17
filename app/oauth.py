# app/oauth.py
import uuid
import time
import base64
import hashlib
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse

from .config import BASE_URL, RESOURCE_ID

# Kayıt olan client'lar (client_id → client_info)
CLIENTS: Dict[str, Dict[str, Any]] = {}

# Authorization kodları (code → auth_data)
AUTH_CODES: Dict[str, Dict[str, Any]] = {}

# Access token store (token → token_data)
TOKENS: Dict[str, Dict[str, Any]] = {}


# ============================================================
# Yardımcı fonksiyonlar
# ============================================================

def _b64url_random() -> str:
    """Base64 URL-safe random string üretir (token ve code için)."""
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().rstrip("=")


def _pkce_s256(verifier: str) -> str:
    """PKCE S256 code_challenge hesaplaması."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def _now() -> float:
    return time.time()


# ============================================================
# Token doğrulayıcı (MCP tarafında kullanılacak)
# ============================================================

class CustomTokenVerifier:
    """
    FastMCP gibi bir MCP server'ın kullanacağı token doğrulayıcı.

    verify(token) metodu:
    - Geçerli bir access_token bulunursa, token metadata döner
    - Geçersiz veya süresi dolmuşsa None döner
    """

    async def verify(self, token: str) -> Optional[Dict[str, Any]]:
        token_data = TOKENS.get(token)
        if not token_data:
            return None

        if token_data.get("expires_at", 0) < _now():
            # Süresi dolmuş ise
            return None

        # MCP tarafında ihtiyaç duyulabilecek tipik alanlar
        return {
            "client_id": token_data.get("client_id"),
            "scope": token_data.get("scope", "mcp"),
            "resource": token_data.get("resource", RESOURCE_ID),
        }


# ============================================================
# OAuth endpoint'lerini FastAPI app'ine register eden fonksiyon
# ============================================================

def register_oauth_routes(app: FastAPI) -> None:
    """
    OAuth 2.0 / OIDC / Protected Resource endpoint'lerini FastAPI app'ine ekler.
    ChatGPT Connector OAuth akışı ile uyumlu olacak şekilde tasarlanmıştır.
    """

    # --------------------------------------------------------
    # 0) Protected Resource Metadata
    # --------------------------------------------------------
    @app.get("/.well-known/oauth-protected-resource")
    async def protected_resource_metadata():
        return JSONResponse(
            {
                "resource": RESOURCE_ID,
                "authorization_servers": [BASE_URL],
                "scopes_supported": ["mcp"],
                "resource_documentation": f"{BASE_URL}/docs",
            }
        )

    # --------------------------------------------------------
    # 1) Authorization Server Metadata / OIDC Metadata
    # --------------------------------------------------------
    def _oauth_metadata_body():
        return {
            "issuer": BASE_URL,
            "authorization_endpoint": f"{BASE_URL}/oauth/authorize",
            "token_endpoint": f"{BASE_URL}/oauth/token",
            "registration_endpoint": f"{BASE_URL}/register",
            "jwks_uri": f"{BASE_URL}/oauth/jwks.json",
            "code_challenge_methods_supported": ["S256"],
            "scopes_supported": ["mcp"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "client_credentials"],
            "token_endpoint_auth_methods_supported": ["client_secret_post"],
        }

    @app.get("/.well-known/oauth-authorization-server")
    async def oauth_server_metadata():
        return JSONResponse(_oauth_metadata_body())

    @app.get("/.well-known/openid-configuration")
    async def oidc_config():
        return JSONResponse(_oauth_metadata_body())

    @app.get("/oauth/jwks.json")
    async def jwks():
        # Opaque token kullandığımız için burada gerçek key yok.
        return JSONResponse({"keys": []})

    # --------------------------------------------------------
    # 2) Dynamic Client Registration (RFC 7591)
    # --------------------------------------------------------
    @app.post("/register")
    async def register_client(request: Request):
        """
        ChatGPT Connector'ın ilk bağlantıda çağırdığı endpoint.
        Gelen JSON tipik olarak:
        {
            "redirect_uris": ["https://chatgpt.com/connector_platform_oauth_redirect"],
            "client_name": "...",
            ...
        }
        """
        payload = await request.json()
        redirect_uris = payload.get("redirect_uris") or []
        client_name = payload.get("client_name") or "ChatGPT Connector Client"

        if not redirect_uris:
            return JSONResponse(
                {"error": "invalid_client_metadata", "error_description": "redirect_uris required"},
                status_code=400,
            )

        client_id = uuid.uuid4().hex
        client_secret = uuid.uuid4().hex

        CLIENTS[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
            "client_name": client_name,
        }

        return JSONResponse(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": redirect_uris,
                "client_name": client_name,
                "token_endpoint_auth_method": "client_secret_post",
                "grant_types": ["authorization_code", "client_credentials"],
                "response_types": ["code"],
                "scope": "mcp",
            }
        )

    # --------------------------------------------------------
    # 3) Authorization Endpoint (Authorization Code + PKCE)
    # --------------------------------------------------------
    @app.get("/oauth/authorize")
    async def oauth_authorize(request: Request):
        """
        ChatGPT, kullanıcı adına authorization code almak için buraya gelir.
        Biz prototip olduğu için kullanıcı ekranı göstermeden otomatik onay veriyoruz.
        """
        qp = request.query_params

        client_id = qp.get("client_id")
        redirect_uri = qp.get("redirect_uri")
        state = qp.get("state")
        scope = qp.get("scope", "mcp")
        resource = qp.get("resource")
        code_challenge = qp.get("code_challenge")
        code_challenge_method = qp.get("code_challenge_method")

        # 1) client id kontrolü
        client_info = CLIENTS.get(client_id or "")
        if not client_id or not client_info:
            return PlainTextResponse("invalid client_id", status_code=400)

        # 2) redirect_uri doğrulaması
        registered_redirects = client_info.get("redirect_uris") or []
        # ChatGPT connector genellikle tam eşleşme gönderir, ama yine de startswith ile esnek olalım
        if not redirect_uri or not any(redirect_uri.startswith(r) for r in registered_redirects):
            return PlainTextResponse("invalid redirect_uri", status_code=400)

        # 3) Authorization code üret ve sakla
        code = _b64url_random()
        AUTH_CODES[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "resource": resource or RESOURCE_ID,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "created_at": _now(),
            "expires_at": _now() + 300,  # 5 dakika
        }

        # 4) Kullanıcı onayı simüle: direkt redirect ile code döndür
        redirect_with_code = f"{redirect_uri}?code={code}"
        if state:
            redirect_with_code += f"&state={state}"

        return RedirectResponse(redirect_with_code)

    # --------------------------------------------------------
    # 4) Token Endpoint (Authorization Code + Client Credentials)
    # --------------------------------------------------------
    @app.post("/oauth/token")
    async def oauth_token(
        grant_type: str = Form(...),
        code: str = Form(None),
        client_id: str = Form(None),
        client_secret: str = Form(None),
        redirect_uri: str = Form(None),
        resource: str = Form(None),
        code_verifier: str = Form(None),
    ):
        """
        Token endpoint:
        - grant_type=authorization_code
        - grant_type=client_credentials
        """

        # ----------------------------------------------------
        # Authorization Code Flow
        # ----------------------------------------------------
        if grant_type == "authorization_code":
            # Client doğrulaması
            client_info = CLIENTS.get(client_id or "")
            if not client_info or client_info.get("client_secret") != client_secret:
                return JSONResponse({"error": "invalid_client"}, status_code=401)

            # Code doğrulaması
            auth_data = AUTH_CODES.pop(code, None)
            if not auth_data:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)

            # Code süresi geçmiş mi?
            if auth_data["expires_at"] < _now():
                return JSONResponse({"error": "expired_code"}, status_code=400)

            # Client ve redirect_uri eşleşiyor mu?
            if auth_data["client_id"] != client_id:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)

            if redirect_uri != auth_data["redirect_uri"]:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)

            # PKCE doğrulaması (S256)
            if auth_data.get("code_challenge"):
                if not code_verifier:
                    return JSONResponse({"error": "invalid_grant", "error_description": "code_verifier required"}, status_code=400)

                expected_challenge = auth_data["code_challenge"]
                method = auth_data.get("code_challenge_method", "S256")

                if method != "S256":
                    return JSONResponse({"error": "invalid_grant", "error_description": "unsupported code_challenge_method"}, status_code=400)

                calculated = _pkce_s256(code_verifier)
                if calculated != expected_challenge:
                    return JSONResponse({"error": "invalid_grant", "error_description": "PKCE verification failed"}, status_code=400)

            # Access token üret
            access_token = _b64url_random()
            expires_in = 3600

            token_data = {
                "client_id": client_id,
                "scope": auth_data.get("scope", "mcp"),
                "resource": auth_data.get("resource") or resource or RESOURCE_ID,
                "created_at": _now(),
                "expires_at": _now() + expires_in,
            }
            TOKENS[access_token] = token_data

            return JSONResponse(
                {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": expires_in,
                    "scope": token_data["scope"],
                }
            )

        # ----------------------------------------------------
        # Client Credentials Flow (isteğe bağlı)
        # ----------------------------------------------------
        elif grant_type == "client_credentials":
            client_info = CLIENTS.get(client_id or "")
            if not client_info or client_info.get("client_secret") != client_secret:
                return JSONResponse({"error": "invalid_client"}, status_code=401)

            access_token = _b64url_random()
            expires_in = 3600

            token_data = {
                "client_id": client_id,
                "scope": "mcp",
                "resource": resource or RESOURCE_ID,
                "created_at": _now(),
                "expires_at": _now() + expires_in,
            }
            TOKENS[access_token] = token_data

            return JSONResponse(
                {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": expires_in,
                    "scope": "mcp",
                }
            )

        # ----------------------------------------------------
        # Desteklenmeyen grant_type
        # ----------------------------------------------------
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)
