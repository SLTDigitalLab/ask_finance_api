import os
import secrets
from fastapi import HTTPException, Security, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer()

SECRET_TOKEN = os.getenv("API_SECRET_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify the provided token matches our secret token.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required"
        )
    
    if credentials.credentials != SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    
    return credentials.credentials

def verify_api_key(x_api_key: str = Header(..., description="API Key")) -> str:
    """
    Alternative method: Verify API key from custom header.
    """
    if x_api_key != SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key

# Multiple token support
class TokenManager:
    def __init__(self):
        
        self.admin_token = os.getenv("ADMIN_TOKEN") or secrets.token_urlsafe(32)
        self.read_token = os.getenv("READ_TOKEN") or secrets.token_urlsafe(32)
        self.write_token = os.getenv("WRITE_TOKEN") or secrets.token_urlsafe(32)
        self.frontend_token = os.getenv("FRONTEND_TOKEN") or secrets.token_urlsafe(32)
        
        if not os.getenv("ADMIN_TOKEN"):
            print(f"Admin Token: {self.admin_token}")
        if not os.getenv("READ_TOKEN"):
            print(f"Read Token: {self.read_token}")
        if not os.getenv("WRITE_TOKEN"):
            print(f"Write Token: {self.write_token}")
        if not os.getenv("FRONTEND_TOKEN"):
            print(f"Frontend Token: {self.frontend_token}")
    
    def verify_admin_token(self, credentials: HTTPAuthorizationCredentials = Security(security)):
        if credentials.credentials != self.admin_token:
            raise HTTPException(status_code=401, detail="Admin access required")
        return credentials.credentials
    
    def verify_read_token(self, credentials: HTTPAuthorizationCredentials = Security(security)):
        valid_tokens = [self.admin_token, self.read_token, self.write_token]
        if credentials.credentials not in valid_tokens:
            raise HTTPException(status_code=401, detail="Read access required")
        return credentials.credentials
    
    def verify_write_token(self, credentials: HTTPAuthorizationCredentials = Security(security)):
        valid_tokens = [self.admin_token, self.write_token]
        if credentials.credentials not in valid_tokens:
            raise HTTPException(status_code=401, detail="Write access required")
        return credentials.credentials
    
    def verify_frontend_token(self, credentials: HTTPAuthorizationCredentials = Security(security)):
        if credentials.credentials != self.frontend_token:
            raise HTTPException(status_code=401, detail="Frontend access only")
        return credentials.credentials

token_manager = TokenManager()