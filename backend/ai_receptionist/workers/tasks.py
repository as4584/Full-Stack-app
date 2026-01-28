import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.orm import Session
from ai_receptionist.core.database import get_session_local
from ai_receptionist.models.call import Call

logger = logging.getLogger(__name__)

async def async_audit_log(event: Dict[str, Any]) -> None:
    """Example async worker task for auditing events."""
    await asyncio.sleep(0)  # simulate async I/O
    return None

async def cleanup_phantom_calls() -> int:
    """
    Finds calls stuck in 'in-progress' status for > 1 hour 
    and marks them interrupted. This prevents dashboard clutter.
    """
    logger.info("Starting phantom call cleanup...")
    db = get_session_local()()
    try:
        threshold = datetime.utcnow() - timedelta(hours=1)
        phantom_calls = db.query(Call).filter(
            Call.status == "in-progress",
            Call.created_at < threshold
        ).all()
        
        count = len(phantom_calls)
        for call in phantom_calls:
            logger.info(f"Cleaning up phantom call: {call.call_sid}")
            call.status = "interrupted"
            call.summary = "Call timed out naturally."
            
        db.commit()
        if count > 0:
            logger.info(f"Cleaned up {count} phantom calls.")
        return count
    except Exception as e:
        logger.error(f"Error during phantom call cleanup: {e}")
        db.rollback()
        return 0
    finally:
        db.close()
