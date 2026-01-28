"""
Intent handlers for voice conversation.

Detects user intent and generates appropriate responses.
"""

from typing import Optional, Tuple
from .business_config import BUSINESS_NAME, SERVICES, HOURS, STAFF
from .messages import get_message


def detect_intent(user_input: str, language: str = "en") -> str:
    """
    Detect user intent from speech input.

    Args:
        user_input: What the user said (transcribed speech)
        language: "en" or "es"

    Returns:
        Intent name: "availability", "services", "hours", "staff", "pricing", "unclear", "goodbye", "help_menu", "other"
    """
    user_input_lower = user_input.lower()

    # Availability keywords - expanded
    if any(word in user_input_lower for word in [
        "appointment", "schedule", "available", "availability", "book", "booking", "reserve", "reservation",
        "meet", "meeting", "consultation", "consult", "slot", "time slot", "visit",
        "cita", "disponibilidad", "reserva", "reunión", "consulta"
    ]):
        return "availability"

    # Services keywords - expanded
    if any(word in user_input_lower for word in [
        "service", "services", "help with", "do you offer", "can you help", "need help",
        "what do you do", "what can you", "practice area", "specialize", "handle",
        "divorce", "custody", "estate", "will", "domestic violence", "family law",
        "servicio", "servicios", "ofrecen", "pueden ayudar", "qué hacen", "especialidad"
    ]):
        return "services"

    # Hours keywords - expanded
    if any(word in user_input_lower for word in [
        "hours", "open", "close", "closed", "when are you", "what time", "business hours",
        "operating hours", "available when", "schedule",
        "horario", "abierto", "cerrado", "cuándo", "qué hora"
    ]):
        return "hours"

    # Staff keywords - expanded
    if any(word in user_input_lower for word in [
        "staff", "attorney", "lawyer", "team", "who works", "who is", "who can",
        "partner", "associate", "counsel", "paralegal", "legal team",
        "abogado", "abogada", "equipo", "quién", "personal"
    ]):
        return "staff"

    # Pricing keywords - expanded
    if any(word in user_input_lower for word in [
        "price", "prices", "cost", "costs", "fee", "fees", "how much", "charge", "charges",
        "rate", "rates", "payment", "afford", "expensive", "budget",
        "precio", "precios", "costo", "costos", "cuánto", "tarifa", "pago"
    ]):
        return "pricing"

    # General help/menu request
    if any(word in user_input_lower for word in [
        "help", "options", "menu", "what can", "tell me about", "information",
        "ayuda", "opciones", "menú", "información"
    ]):
        return "help_menu"

    # Goodbye keywords - expanded
    if any(word in user_input_lower for word in [
        "goodbye", "bye", "thank", "thanks", "that's all", "that is all", "no more",
        "done", "finished", "nothing else", "have a good",
        "adiós", "gracias", "eso es todo", "nada más", "terminé"
    ]):
        return "goodbye"

    # Unclear (very short or garbled)
    if len(user_input_lower.strip()) < 3:
        return "unclear"

    # Default - but this will now be handled better
    return "other"


def handle_intent(intent: str, language: str = "en", user_input: str = "") -> Tuple[str, Optional[str]]:
    """
    Generate response for an intent.

    Args:
        intent: Intent name from detect_intent
        language: "en" or "es"
        user_input: Original user input (for context)

    Returns:
        Tuple of (response_text, next_action)
        next_action: "gather" to continue conversation, "hangup" to end call, None for default
    """
    if intent == "availability":
        response = get_message("AVAILABILITY_QUESTION", language)
        return response, "gather"

    elif intent == "services":
        intro = get_message("SERVICES_INTRO", language)
        service_list = ", ".join([s["name"] for s in SERVICES])
        response = f"{intro} {service_list}."
        return response, "gather"

    elif intent == "hours":
        weekday = HOURS.get("weekday", "Monday to Friday, 9 AM to 5 PM")
        weekend = HOURS.get("weekend", "Closed on weekends")
        notes = HOURS.get("notes", "")
        response = get_message("HOURS_RESPONSE", language, weekday_hours=weekday, weekend_hours=weekend, notes=notes)
        return response, "gather"

    elif intent == "staff":
        intro = get_message("STAFF_INTRO", language)
        staff_list = ", ".join([f"{s['name']} ({s['role']})" for s in STAFF])
        response = f"{intro} {staff_list}."
        return response, "gather"

    elif intent == "pricing":
        # Default pricing response (first service as example)
        if SERVICES:
            service_name = SERVICES[0]["name"]
            price = SERVICES[0].get("price", "varies")
            response = get_message("PRICING_RESPONSE", language, service_name=service_name, price=price)
        else:
            response = "Our pricing varies by service. Please call us for details." if language == "en" else "Nuestros precios varían según el servicio. Por favor llámenos para más detalles."
        return response, "gather"

    elif intent == "unclear":
        response = get_message("UNCLEAR_RESPONSE", language)
        return response, "gather"

    elif intent == "goodbye":
        response = get_message("GOODBYE", language, business_name=BUSINESS_NAME)
        return response, "hangup"

    elif intent == "help_menu":
        response = get_message("HELP_MENU", language)
        return response, "gather"

    else:  # "other" - Try to help instead of immediately escalating
        response = get_message("CLARIFICATION_REQUEST", language)
        return response, "gather"
