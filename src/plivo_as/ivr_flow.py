"""Plivo XML IVR Flow Generator.

Handles OTP authentication layer, multi-level IVR menu branching (Language & Actions),
audio streaming, and call forwarding to a live associate.
"""

from typing import Optional
from plivo import plivoxml
from .config import config


def build_otp_prompt_xml(error_message: Optional[str] = None) -> str:
    """Builds Plivo XML to prompt caller for a 4-digit birthdate OTP."""
    response = plivoxml.ResponseElement()

    prompt_text = (
        error_message
        if error_message
        else "Welcome to InspireWorks. Please enter your 4-digit birthdate OTP in day and month format."
    )

    action_url = config.get_webhook_url("/ivr/otp/verify")
    fallback_url = config.get_webhook_url("/ivr/otp")

    get_digits = plivoxml.GetDigitsElement(
        action=action_url,
        method="POST",
        num_digits=4,
        timeout=10,
        retries=1,
    )
    get_digits.add_speak(prompt_text, language="en-US", voice="WOMAN")
    response.add(get_digits)

    # If timeout or no input, loop back to prompt
    response.add_speak("We did not receive your input. Let's try again.", language="en-US", voice="WOMAN")
    response.add_redirect(fallback_url, method="POST")

    return response.to_string()


def build_otp_success_xml() -> str:
    """Builds XML acknowledging OTP success and transitioning to Level 1 Menu."""
    response = plivoxml.ResponseElement()
    response.add_speak("Authentication successful. Welcome!", language="en-US", voice="WOMAN")
    response.add_redirect(config.get_webhook_url("/ivr/menu/level1"), method="POST")
    return response.to_string()


def build_level1_language_menu_xml(error_message: Optional[str] = None) -> str:
    """Builds Plivo XML for Level 1: Language selection (English or Spanish)."""
    response = plivoxml.ResponseElement()

    prompt_text = (
        error_message
        if error_message
        else "Main Menu. For English, press 1. Para español, oprima 2."
    )

    action_url = config.get_webhook_url("/ivr/menu/level1/select")
    fallback_url = config.get_webhook_url("/ivr/menu/level1")

    get_digits = plivoxml.GetDigitsElement(
        action=action_url,
        method="POST",
        num_digits=1,
        timeout=10,
        retries=1,
    )
    get_digits.add_speak(prompt_text, language="en-US", voice="WOMAN")
    response.add(get_digits)

    # Loop back if no selection
    response.add_speak("We did not detect a selection.", language="en-US", voice="WOMAN")
    response.add_redirect(fallback_url, method="POST")

    return response.to_string()


def build_level2_action_menu_xml(language: str = "en", error_message: Optional[str] = None) -> str:
    """Builds Plivo XML for Level 2: Actions based on selected language."""
    response = plivoxml.ResponseElement()
    lang = language.lower()

    if lang == "es":
        prompt_text = (
            error_message
            if error_message
            else "Ha seleccionado español. Presione 1 para escuchar un mensaje de audio corto. Presione 2 para conectarse con un asesor en vivo."
        )
        voice_lang = "es-ES"
        no_input_text = "No hemos recibido su selección. Por favor intente nuevamente."
    else:
        prompt_text = (
            error_message
            if error_message
            else "You have selected English. Press 1 to play a short audio message. Press 2 to connect to a live associate."
        )
        voice_lang = "en-US"
        no_input_text = "We did not receive your selection. Let's try again."

    action_url = config.get_webhook_url(f"/ivr/menu/level2/action?lang={lang}")
    fallback_url = config.get_webhook_url(f"/ivr/menu/level2?lang={lang}")

    get_digits = plivoxml.GetDigitsElement(
        action=action_url,
        method="POST",
        num_digits=1,
        timeout=10,
        retries=1,
    )
    get_digits.add_speak(prompt_text, language=voice_lang, voice="WOMAN")
    response.add(get_digits)

    response.add_speak(no_input_text, language=voice_lang, voice="WOMAN")
    response.add_redirect(fallback_url, method="POST")

    return response.to_string()


def build_play_audio_xml(language: str = "en") -> str:
    """Builds Plivo XML to play a short audio message (public MP3)."""
    response = plivoxml.ResponseElement()
    lang = language.lower()

    if lang == "es":
        response.add_speak("Reproduciendo su mensaje de audio.", language="es-ES", voice="WOMAN")
        response.add_play(config.audio_url)
        response.add_speak("Gracias por comunicarse con InspireWorks. ¡Hasta luego!", language="es-ES", voice="WOMAN")
    else:
        response.add_speak("Playing your audio message.", language="en-US", voice="WOMAN")
        response.add_play(config.audio_url)
        response.add_speak("Thank you for calling InspireWorks. Goodbye!", language="en-US", voice="WOMAN")

    response.add_hangup()
    return response.to_string()


def build_forward_associate_xml(language: str = "en") -> str:
    """Builds Plivo XML to forward call to a live associate."""
    response = plivoxml.ResponseElement()
    lang = language.lower()

    if lang == "es":
        response.add_speak(
            "Conectando con un asesor en vivo. Por favor espere en la línea.",
            language="es-ES",
            voice="WOMAN",
        )
    else:
        response.add_speak(
            "Connecting you to a live associate. Please hold the line.",
            language="en-US",
            voice="WOMAN",
        )

    dial = plivoxml.DialElement(caller_id=config.plivo_source_number)
    dial.add_number(config.live_associate_number)
    response.add(dial)

    return response.to_string()
