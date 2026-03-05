from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from dotenv import dotenv_values
from typing import Dict
from apscheduler.schedulers.background import BackgroundScheduler
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware
from api.v1.chat.base import router as multi_agent_router
from api.v1.chat.document_agent import router as document_router
import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from msal import ConfidentialClientApplication
from starlette.middleware.sessions import SessionMiddleware

IS_LOCAL = False  # Set to False in production

app = FastAPI(title="ASK Finance Agent")
Instrumentator().instrument(app).expose(app)

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="askfinance_session",
    same_site="lax" if IS_LOCAL else "none",
    https_only=not IS_LOCAL,
)

app.include_router(multi_agent_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")

config = dotenv_values(".env")

if IS_LOCAL:
    # LOCALHOST SETTINGS
    # The URL where your React Frontend is running
    FRONTEND_BASE = "http://localhost:5173" 
    # The URL where this Backend is running
    BACKEND_BASE = "http://localhost:8000"
    
    origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
else:
    # PRODUCTION SETTINGS
    FRONTEND_BASE = "https://askfinance.sltdigitallab.lk"
    BACKEND_BASE = "https://askfinance.sltdigitallab.lk"
    
    origins = [
        "https://askfinance.sltdigitallab.lk"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIRECT_URI = f"{BACKEND_BASE}/api/auth/callback"
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

SCOPE = ["User.Read"]

msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/welcome")
def api_welcome(request: Request, domain: str = None):
    # Retrieve the 'user_access' dictionary from the session
    user_access = request.session.get("user_access", {})
    
    # If no domain is provided, or the domain is not in the access list, return unauthenticated
    if not domain or domain not in user_access:
        return JSONResponse({"authenticated": False}, status_code=200) # Returning 200 to avoid console errors, handled by frontend logic

    # Retrieve specific user data for this domain
    user_data = user_access[domain]

    return {
        "authenticated": True,
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "domain": domain
    }


@app.get("/api/login")
def api_login(domain: str = "default"):
    # Build Azure AD auth URL
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
        state=domain
    )
    return RedirectResponse(url=auth_url, status_code=302)


@app.get("/")
def index(request: Request):
    user_access = request.session.get("user_access", {})
    if user_access:
        return {"message": "Welcome back!", "logged_in_domains": list(user_access.keys())}
    return {"message": "Please log in with Microsoft"}


@app.get("/api/auth/callback")
def api_auth_callback(request: Request):
    # Extract "code" from query params
    code = request.query_params.get("code")
    domain_state = request.query_params.get("state")

    if not code:
        return JSONResponse({"error": "Authorization code not found"}, status_code=400)

    # Exchange code for tokens
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
    )

    if "error" in result:
        return JSONResponse({"error": result.get("error_description")}, status_code=400)

    # Get existing access map or create new one
    user_access = request.session.get("user_access", {})
    
    # Add/Update the user data for THIS specific domain
    # We use the domain_state (which is the domain name) as the key
    target_domain = domain_state if domain_state else "default"

    # We extract ONLY essential fields. Storing the full object breaks cookie size limits.
    full_claims = result.get("id_token_claims", {})
    
    optimized_user_data = {
        "name": full_claims.get("name"),
        "email": full_claims.get("preferred_username") or full_claims.get("email"),
        "oid": full_claims.get("oid") # Object ID (unique user ID)
    }
    
    user_access[target_domain] = optimized_user_data

    # Store user info in session
    request.session["user_access"] = user_access

    # Redirect back to the specific domain chat interface
    if target_domain and target_domain != "default":
        redirect_url = f"{FRONTEND_BASE}/{target_domain}/chat"
    else:
        redirect_url = f"{FRONTEND_BASE}/chat"

    return RedirectResponse(
        url=redirect_url,
        status_code=302,
    )


@app.get("/api/logout")
def api_logout(request: Request, domain: str = None):

    if domain:
        user_access = request.session.get("user_access", {})
        if domain in user_access:
            del user_access[domain]
            request.session["user_access"] = user_access
            # Redirect to that domain's chat (which will now show login screen)
            return RedirectResponse(url=f"{FRONTEND_BASE}/{domain}/chat", status_code=302)
    
    # Fallback: Clear everything
    request.session.clear()
    return RedirectResponse(url=f"{FRONTEND_BASE}/", status_code=302)