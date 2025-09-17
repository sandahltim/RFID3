# Sync API Endpoints - Simplified
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from datetime import datetime

from app.api.auth import verify_api_key

router = APIRouter()

@router.get("/status")
async def get_sync_status(user_info: Dict = Depends(verify_api_key)):
    """Get sync status"""
    return {
        "status": "operational",
        "last_sync": datetime.now().isoformat(),
        "pending_changes": 0
    }

@router.post("/from-manager")
async def sync_from_manager(user_info: Dict = Depends(verify_api_key)):
    """Sync from manager database"""
    if user_info["role"] not in ["admin", "operator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {"status": "started", "sync_id": f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}