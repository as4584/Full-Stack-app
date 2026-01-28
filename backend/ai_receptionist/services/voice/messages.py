"""
Bilingual message templates for English and Spanish.
"""

from typing import Dict


# Language selection (entry point)
LANGUAGE_SELECTION: Dict[str, str] = {
    "en": "Hello! Press 1 for English or say English.",
    "es": "¡Hola! Presione 2 para español o diga Español.",
}

# Combined language selection (both languages in one message)
LANGUAGE_SELECTION_COMBINED: str = "Hello! Press 1 for English or say English. ¡Hola! Presione 2 para español o diga Español."


# Greeting (after language selected)
GREETING: Dict[str, str] = {
    "en": "Thank you for calling {business_name}. How can we assist you today?",
    "es": "Gracias por llamar a {business_name}. ¿Cómo podemos ayudarle hoy?",
}


# Services listing
SERVICES_INTRO: Dict[str, str] = {
    "en": "We offer the following services:",
    "es": "Ofrecemos los siguientes servicios:",
}


# Hours
HOURS_RESPONSE: Dict[str, str] = {
    "en": "We are open {weekday_hours}. {weekend_hours}. {notes}",
    "es": "Estamos abiertos {weekday_hours}. {weekend_hours}. {notes}",
}


# Staff
STAFF_INTRO: Dict[str, str] = {
    "en": "Our team includes:",
    "es": "Nuestro equipo incluye:",
}


# Availability
AVAILABILITY_QUESTION: Dict[str, str] = {
    "en": "Let me check our availability. What type of service do you need?",
    "es": "Déjame verificar nuestra disponibilidad. ¿Qué tipo de servicio necesita?",
}


# Unclear audio
UNCLEAR_RESPONSE: Dict[str, str] = {
    "en": "I'm sorry, I didn't catch that. Could you please repeat?",
    "es": "Lo siento, no entendí. ¿Puede repetir por favor?",
}


# Clarification request (for unclear intents)
CLARIFICATION_REQUEST: Dict[str, str] = {
    "en": "I want to make sure I help you with the right information. Are you asking about our hours, services, scheduling an appointment, pricing, or our team? Please let me know what you need.",
    "es": "Quiero asegurarme de ayudarle con la información correcta. ¿Pregunta sobre nuestro horario, servicios, programar una cita, precios o nuestro equipo? Por favor dígame qué necesita.",
}


# Help menu
HELP_MENU: Dict[str, str] = {
    "en": "I can help you with: checking our office hours, learning about our legal services, scheduling a consultation, discussing pricing, or meeting our team. What would you like to know?",
    "es": "Puedo ayudarle con: verificar nuestro horario de oficina, conocer nuestros servicios legales, programar una consulta, discutir precios o conocer nuestro equipo. ¿Qué le gustaría saber?",
}


# Escalation (only after multiple failed attempts)
ESCALATION_RESPONSE: Dict[str, str] = {
    "en": "I apologize for any confusion. Let me connect you with a team member who can better assist you. Please hold.",
    "es": "Me disculpo por cualquier confusión. Permítame conectarlo con un miembro del equipo que pueda ayudarle mejor. Por favor espere.",
}


# Goodbye
GOODBYE: Dict[str, str] = {
    "en": "Thank you for calling {business_name}. Have a great day!",
    "es": "Gracias por llamar a {business_name}. ¡Que tenga un buen día!",
}


# Pricing inquiry
PRICING_RESPONSE: Dict[str, str] = {
    "en": "Our pricing varies by service. {service_name} starts at ${price}. Would you like more details?",
    "es": "Nuestros precios varían según el servicio. {service_name} comienza en ${price}. ¿Desea más detalles?",
}


def get_message(template_name: str, language: str, **kwargs) -> str:
    """
    Get a message in the specified language with placeholders filled.

    Args:
        template_name: Name of the message template (e.g., "GREETING")
        language: "en" or "es"
        **kwargs: Placeholder values for formatting

    Returns:
        Formatted message string
    """
    template_map: Dict[str, Dict[str, str]] = {
        "LANGUAGE_SELECTION": LANGUAGE_SELECTION,
        "GREETING": GREETING,
        "SERVICES_INTRO": SERVICES_INTRO,
        "HOURS_RESPONSE": HOURS_RESPONSE,
        "STAFF_INTRO": STAFF_INTRO,
        "AVAILABILITY_QUESTION": AVAILABILITY_QUESTION,
        "UNCLEAR_RESPONSE": UNCLEAR_RESPONSE,
        "CLARIFICATION_REQUEST": CLARIFICATION_REQUEST,
        "HELP_MENU": HELP_MENU,
        "ESCALATION_RESPONSE": ESCALATION_RESPONSE,
        "GOODBYE": GOODBYE,
        "PRICING_RESPONSE": PRICING_RESPONSE,
    }

    template_dict = template_map.get(template_name)
    if not template_dict:
        raise ValueError(f"Unknown template: {template_name}")

    message = template_dict.get(language, template_dict.get("en"))
    return message.format(**kwargs) if kwargs else message
