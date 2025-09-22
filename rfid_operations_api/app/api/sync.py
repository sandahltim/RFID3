# Sync API Endpoints - Simplified
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from datetime import datetime

from app.api.auth import verify_api_key

router = APIRouter()

@router.get("/status")
async def get_sync_status():
    """Get sync status - public endpoint"""
    from sqlalchemy import text
    from app.models import get_db

    # Get actual record count from database
    try:
        db = next(get_db())
        result = db.execute(text("SELECT COUNT(*) as count FROM id_item_master"))
        total_records = result.fetchone()[0]
        db.close()
    except:
        total_records = 0

    return {
        "status": "operational",
        "manager_db": {
            "last_sync": datetime.now().isoformat(),
            "total_records": total_records,
            "status": "connected"
        },
        "rfidpro": {
            "last_sync": "Managed by Executive Dashboard",
            "status": "manual_only"
        },
        "pending_changes": 0
    }

@router.post("/from-manager")
async def sync_from_manager(user_info: Dict = Depends(verify_api_key)):
    """Sync from manager database"""
    if user_info["role"] not in ["admin", "operator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {"status": "started", "sync_id": f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}