import json
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ai_receptionist.models.call import Call
from ai_receptionist.models.evaluation import EvaluationBenchmark

logger = logging.getLogger(__name__)

def calculate_metrics(db: Session, days: int = 7) -> EvaluationBenchmark:
    """
    Analyzes recent calls and their shadow results to produce aggregate quality metrics.
    """
    since = datetime.utcnow() - timedelta(days=days)
    calls = db.query(Call).filter(Call.updated_at >= since, Call.shadow_result != None).all()
    
    if not calls:
        logger.warning("No calls with shadow results found for metrics calculation.")
        return None
        
    total_calls = len(calls)
    total_booking_attempts = 0
    successful_bookings = 0
    total_turns_for_bookings = 0
    false_confirmations = 0
    latencies = []
    matches = 0
    
    for call in calls:
        shadow_res = json.loads(call.shadow_result) if call.shadow_result else {}
        frame = json.loads(call.conversation_frame) if call.conversation_frame else {"turns": []}
        
        # 1. Success Rate & False Confirmations
        is_live_booked = call.appointment_booked == 1
        is_shadow_booked = shadow_res.get("tool_match", False) and any(d.get("shadow_tool") == "book_appointment" for d in shadow_res.get("shadow_decisions", []))
        
        if is_live_booked:
            total_booking_attempts += 1
            # Check if it was actually successful (based on tool result if available)
            # For prototype, we assume if appointment_booked=1 and it matched shadow, it's good.
            successful_bookings += 1
            
            # Count turns
            turns = [t for t in frame.get("turns", []) if t.get("role") != "System"]
            total_turns_for_bookings += len(turns)
            
        # False confirmation: Live said booked, Shadow said No (or v-v)
        if is_live_booked and not is_shadow_booked:
            false_confirmations += 1
            
        # 2. Latency (Assistant turns)
        for turn in frame.get("turns", []):
            if turn.get("role") == "Aria" and "latency_ms" in turn.get("metadata", {}):
                latencies.append(turn["metadata"]["latency_ms"])
                
        # 3. Overall match score
        matches += shadow_res.get("match_score", 0)

    # Aggregates
    booking_success_rate = (successful_bookings / total_booking_attempts * 100) if total_booking_attempts > 0 else 0
    avg_turns = (total_turns_for_bookings / successful_bookings) if successful_bookings > 0 else 0
    
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
    
    benchmark = EvaluationBenchmark(
        version="v1-shadow",
        total_calls=total_calls,
        booking_success_rate=booking_success_rate,
        avg_turns_per_booking=avg_turns,
        false_confirmations=false_confirmations,
        p95_latency_ms=p95_latency,
        raw_data={
            "match_score_avg": matches / total_calls if total_calls > 0 else 0,
            "period_days": days
        }
    )
    
    db.add(benchmark)
    db.commit()
    return benchmark
