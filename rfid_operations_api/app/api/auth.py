# Authentication API Endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict

from app.models import get_db

router = APIRouter()
security = HTTPBearer()

# Simple API key validation for now
VALID_API_KEYS = {
    "ops_admin_key_2025": {"role": "admin", "user": "admin"},
    "ops_scanner_key_2025": {"role": "scanner", "user": "scanner"},
    "ops_operator_key_2025": {"role": "operator", "user": "operator"},
    "executive_readonly_key": {"role": "readonly", "user": "executive_system"}
}

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify API key and return user info"""

    api_key = credentials.credentials
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return VALID_API_KEYS[api_key]

@router.post("/validate")
async def validate_token(user_info: Dict = Depends(verify_api_key)):
    """Validate API token and return user information"""

    return {
        "valid": True,
        "user": user_info["user"],
        "role": user_info["role"],
        "permissions": {
            "read": True,
            "write": user_info["role"] in ["admin", "operator"],
            "scan": user_info["role"] in ["admin", "operator", "scanner"],
            "admin": user_info["role"] == "admin"
        }
    }

@router.get("/permissions")
async def get_permissions(user_info: Dict = Depends(verify_api_key)):
    """Get user permissions"""

    role = user_info["role"]

    permissions = {
        "read_equipment": True,
        "update_equipment": role in ["admin", "operator"],
        "read_items": True,
        "update_items": role in ["admin", "operator", "scanner"],
        "create_transactions": role in ["admin", "operator", "scanner"],
        "bulk_operations": role in ["admin", "operator"],
        "sync_operations": role in ["admin", "operator"],
        "admin_functions": role == "admin"
    }

    return {
        "user": user_info["user"],
        "role": role,
        "permissions": permissions
    }