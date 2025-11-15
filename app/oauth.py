# app/oauth.py
import uuid
import time
import base64

from starlette.responses import JSONResponse, RedirectResponse, PlainTextResponse
from starlette.requests import Request

from .config import BASE_URL, RESOURCE_ID

# Kayıt olan clientlar (client_id → client_info)
CLIENTS: dict[str, dict] = {}

# Authorization kodları (code → client_id, redirect_uri, resource, ...)
AUTH_CODES: dict[str, dict] = {}

# Access token store (token → client_id, resource, scopes, expires_at)
TOKENS: dict[str, dict] = {}


def _b64url_random() -> str:
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().rstrip("=")


def register_oauth_routes(app):
    """
    Tüm OAuth/MCP auth endpointlerini tek fonksiyonda FastAPI/Starlette app'ine ekler.
    OpenAI Apps SDK 'Authentication' dokümanındaki MCP authorization spec'e göre hazırlanmıştır.
    """

    # -----------------------------------------------------
    # 0) Protected Resource Metadata
    #    GET /.well-known/oauth-protected-resource
    # -----------------------------------------------------
    @app.route("/.well-known/oauth-protected-resource", methods=["GET"])
    async def protected_resource_metadata(request: Request):
        """
        ChatGPT, MCP server'ının hangi authorization server'ları kullandığını
        ve hangi scopes'ları desteklediğini buradan öğrenir.
        """
        return JSONResponse(
            {
                "resource": RESOURCE_ID,
                "authorization_servers": [BASE_URL],
                "scopes_supported": ["mcp"],
                # İstersen belgelendirme sayfan varsa:
                "resource_documentation": f"{BASE_URL}/docs",
            }
        )

    # -----------------------------------------------------
    # 1) Authorization Server Metadata
    #    GET /.well-known/oauth-authorization-server
    #    GET /.well-known/openid-configuration
    # -----------------------------------------------------
    def _oauth_metadata_body():
        return {
            "issuer": BASE_URL,
            "authorization_endpoint": f"{BASE_URL}/oauth/authorize",
            "token_endpoint": f"{BASE_URL}/oauth/token",
            "registration_endpoint": f"{BASE_URL}/register",
            # JWT üretmiyoruz ama spec gereği bir jwks_uri göstermek faydalı;
            # ChatGPT bunu doğrulamak zorunda değil, token doğrulama işi MCP server'da.
            "jwks_uri": f"{BASE_URL}/oauth/jwks.json",
            "code_challenge_methods_supported": ["S256"],  # PKCE şart
            "scopes_supported": ["mcp"],
        }

    @app.route("/.well-known/oauth-authorization-server", methods=["GET"])
    async def oauth_server_metadata(request: Request):
        return JSONResponse(_oauth_metadata_body())

    @app.route("/.well-known/openid-configuration", methods=["GET"])
    async def oidc_config(request: Request):
        # Aynı içeriği OIDC discovery için de sunuyoruz.
        return JSONResponse(_oauth_metadata_body())

    # JWKS dummy endpoint (gerekirse gerçek key eklenebilir)
    @app.route("/oauth/jwks.json", methods=["GET"])
    async def jwks(request: Request):
        return JSONResponse({"keys": []})

    # -----------------------------------------------------
    # 2) Dynamic Client Registration (RFC 7591)
    #    POST /register
    # -----------------------------------------------------
    @app.route("/register", methods=["POST"])
    async def register_client(request: Request):
        payload = await request.json()
        redirect_uris = payload.get("redirect_uris", [])

        client_id = uuid.uuid4().hex
        client_secret = uuid.uuid4().hex

        CLIENTS[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
        }

        return JSONResponse(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": redirect_uris,
                "token_endpoint_auth_method": "client_secret_post",
                "grant_types": ["authorization_code", "client_credentials"],
                "response_types": ["code"],
                "scope": "mcp",
            }
        )

    # -----------------------------------------------------
    # 3) Authorization Endpoint (Authorization Code + PKCE)
    #    GET /oauth/authorize
    # -----------------------------------------------------
    @app.route("/oauth/authorize", methods=["GET"])
    async def oauth_authorize(request: Request):
        """
        ChatGPT bu endpoint'e:
          response_type=code
          client_id=...
          redirect_uri=...
          state=...
          scope=...
          resource=...
          code_challenge=...
          code_challenge_method=S256
        ile gelir.

        Biz burada user UI göstermeden otomatik onay veriyoruz ve authorization code üretiyoruz.
        """
        qp = request.query_params

        client_id = qp.get("client_id")
        redirect_uri = qp.get("redirect_uri")
        state = qp.get("state")
        scope = qp.get("scope", "mcp")
        resource = qp.get("resource")  # Örn: https://obasemarket.azurewebsites.net
        code_challenge = qp.get("code_challenge")
        code_challenge_method = qp.get("code_challenge_method")

        if not client_id or client_id not in CLIENTS:
            return PlainTextResponse("invalid client_id", status_code=400)

        registered_redirects = CLIENTS[client_id]["redirect_uris"]
        if redirect_uri not in registered_redirects:
            return PlainTextResponse("invalid redirect_uri", status_code=400)

        # Authorization code üret
        code = _b64url_random()
        AUTH_CODES[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "resource": resource,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "expires_at": time.time() + 300,  # 5 dk
        }

        # Kullanıcı onayı burada mock: otomatik kabul
        redirect_with_code = f"{redirect_uri}?code={code}"
        if state:
            redirect_with_code += f"&state={state}"

        return RedirectResponse(redirect_with_code)

    # -----------------------------------------------------
    # 4) Token Endpoint
    #    POST /oauth/token
    # -----------------------------------------------------
    @app.route("/oauth/token", methods=["POST"])
    async def oauth_token(request: Request):
        form = await request.form()
        grant_type = form.get("grant_type")

        # -----------------------------
        # Authorization Code Flow
        # -----------------------------
        if grant_type == "authorization_code":
            code = form.get("code")
            client_id = form.get("client_id")
            client_secret = form.get("client_secret")
            redirect_uri = form.get("redirect_uri")
            resource = form.get("resource")
            code_verifier = form.get("code_verifier")  # PKCE - şu an doğrulamıyoruz (demo)

            if not client_id or client_id not in CLIENTS:
                return JSONResponse({"error": "invalid_client"}, status_code=401)

            if CLIENTS[client_id]["client_secret"] != client_secret:
                return JSONResponse({"error": "invalid_client"}, status_code=401)

            if code not in AUTH_CODES:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)

            auth_data = AUTH_CODES.pop(code)

            if redirect_uri != auth_data["redirect_uri"]:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)

            if auth_data["client_id"] != client_id:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)

            if time.time() > auth_data["expires_at"]:
                return JSONResponse({"error": "expired_code"}, status_code=400)

            # resource paramının echo’su (isteğe bağlı sıkı doğrulama)
            if resource and auth_data.get("resource") and resource != auth_data["resource"]:
                return JSONResponse({"error": "invalid_target"}, status_code=400)

            # Access token üret
            token = _b64url_random()
            TOKENS[token] = {
                "client_id": client_id,
                "resource": auth_data.get("resource"),
                "scope": auth_data.get("scope", "mcp"),
                "expires_at": time.time() + 3600,
            }

            return JSONResponse(
                {
                    "access_token": token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "scope": auth_data.get("scope", "mcp"),
                }
            )

        # -----------------------------
        # Client Credentials Flow (opsiyonel)
        # -----------------------------
        elif grant_type == "client_credentials":
            client_id = form.get("client_id")
            client_secret = form.get("client_secret")

            if not client_id or client_id not in CLIENTS:
                return JSONResponse({"error": "invalid_client"}, status_code=401)

            if CLIENTS[client_id]["client_secret"] != client_secret:
                return JSONResponse({"error": "invalid_client"}, status_code=401)

            token = _b64url_random()
            TOKENS[token] = {
                "client_id": client_id,
                "resource": RESOURCE_ID,
                "scope": "mcp",
                "expires_at": time.time() + 3600,
            }

            return JSONResponse(
                {
                    "access_token": token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "scope": "mcp",
                }
            )

        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)
