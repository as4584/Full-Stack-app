import logging
import asyncio
import json
import openai
from ai_receptionist.core.database import get_session_local
from ai_receptionist.models.business import Business
from ai_receptionist.config.settings import get_settings

logger = logging.getLogger(__name__)

async def run_audit_simulation(business_id: int):
    """
    RAG 2.0: Self-Correcting AI Auditor.
    Actually creates a 'shadow chat' to verify business instructions.
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    settings = get_settings()
    
    # Initialize OpenAI for the Auditor
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    try:
        biz = db.query(Business).filter(Business.id == business_id).first()
        if not biz:
            return
        
        logger.info(f"🚀 Starting Deep AI Audit for: {biz.name}")
        
        # 1. PERSONA SETUP
        tester_persona = "You are a skeptical customer testing an AI receptionist. You want to find contradictions or errors in their knowledge. Ask 2-3 tough questions about their services or business hours."
        receptionist_persona = f"You are Aria, an AI Receptionist for {biz.name}. Knowledge: {biz.pending_description}. FAQs: {json.dumps(biz.pending_faqs)}"
        
        # 2. SIMULATION
        # Turn 1: Tester starts
        q1 = "Hi, what exactly do you do and can I come in at 3 AM?"
        
        # Turn 2: Receptionist responds
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": receptionist_persona},
                {"role": "user", "content": q1}
            ]
        )
        answer = resp.choices[0].message.content
        
        # 3. EVALUATION
        eval_prompt = f"Does the following answer contradict this business info?\nInfo: {biz.pending_description}\nFAQs: {biz.pending_faqs}\nAnswer: {answer}\n\nRespond with 'PASS' or a detailed 'FAIL: [reason]'"
        
        eval_resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": eval_prompt}]
        )
        result = eval_resp.choices[0].message.content
        
        if "PASS" in result.upper():
            biz.description = biz.pending_description or biz.description
            biz.faqs = biz.pending_faqs or biz.faqs
            biz.audit_status = "verified"
            biz.audit_report = {
                "summary": "Shadow simulation passed. No contradictions found.",
                "tester_query": q1,
                "ai_response": answer
            }
            logger.info(f"✅ Audit PASSED for {biz.name}")
        else:
            biz.audit_status = "rejected"
            biz.audit_report = {"summary": "Hallucination Detected", "details": result}
            logger.warning(f"❌ Audit REJECTED for {biz.name}: {result}")
        
        db.commit()
    except Exception as e:
        logger.error(f"❌ Audit Error: {e}")
        db.rollback()
    finally:
        db.close()
