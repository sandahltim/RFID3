# Authentication API Endpoints - Simplified
from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from typing import Dict

router = APIRouter()
security = HTTPBearer()

# Simple API key validation
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
            detail="Invalid API key"
        )
    return VALID_API_KEYS[api_key]

@router.post("/validate")
async def validate_token(user_info: Dict = Depends(verify_api_key)):
    """Validate API token"""
    return {"valid": True, "user": user_info["user"], "role": user_info["role"]}