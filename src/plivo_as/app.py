"""Flask Web Application and Plivo Webhook Handlers."""

import logging
from flask import Flask, request, Response, render_template, jsonify
from .config import config
from .events import event_tracker
from .plivo_service import plivo_service
from .ivr_flow import (
    build_otp_prompt_xml,
    build_otp_success_xml,
    build_level1_language_menu_xml,
    build_level2_action_menu_xml,
    build_play_audio_xml,
    build_forward_associate_xml,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("plivo_as")

app = Flask(__name__)


def xml_response(xml_content: str) -> Response:
    """Helper to return an XML HTTP response."""
    return Response(xml_content, mimetype="application/xml")


# ==========================================
# Frontend & API Endpoints
# ==========================================


@app.route("/", methods=["GET"])
def index():
    """Renders the interactive demo dashboard."""
    return render_template(
        "index.html",
        source_number=config.plivo_source_number,
        associate_number=config.live_associate_number,
        otp=config.caller_birthdate_otp,
        base_url=config.base_url,
    )


@app.route("/api/call", methods=["POST"])
def api_call():
    """Triggers an outbound call to the requested phone number."""
    data = request.get_json(silent=True) or {}
    to_number = data.get("phone_number", "").strip()

    if not to_number:
        return jsonify({"success": False, "error": "Phone number is required."}), 400

    logger.info(f"Received request to call {to_number}")
    result = plivo_service.trigger_outbound_call(to_number)

    if result.get("success"):
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@app.route("/api/events", methods=["GET"])
def api_events():
    """Returns recorded call events since specified index."""
    since = int(request.args.get("since", 0))
    events = event_tracker.get_events(since_index=since)
    return jsonify({"events": events, "total": len(events) + since})


@app.route("/api/events/clear", methods=["POST"])
def api_clear_events():
    """Clears the live event log."""
    event_tracker.clear()
    return jsonify({"success": True})


@app.route("/api/config", methods=["GET"])
def api_config():
    """Returns public configuration for the UI."""
    return jsonify(
        {
            "plivo_source_number": config.plivo_source_number,
            "live_associate_number": config.live_associate_number,
            "caller_birthdate_otp": config.caller_birthdate_otp,
            "base_url": config.base_url,
            "audio_url": config.audio_url,
        }
    )


# ==========================================
# Plivo IVR Webhooks
# ==========================================


@app.route("/ivr/otp", methods=["GET", "POST"])
def ivr_otp_prompt():
    """Answer URL webhook: Prompts caller for 4-digit birthdate OTP."""
    call_uuid = request.values.get("CallUUID")
    caller = request.values.get("From")
    called = request.values.get("To")

    logger.info(f"Call answered: UUID={call_uuid}, From={caller}, To={called}")
    event_tracker.add_event(
        stage="CALL_ANSWERED",
        message="Call answered by user. Presenting OTP DTMF prompt.",
        call_uuid=call_uuid,
        details={"from": caller, "to": called},
    )

    xml = build_otp_prompt_xml()
    return xml_response(xml)


@app.route("/ivr/otp/verify", methods=["GET", "POST"])
def ivr_otp_verify():
    """Validates entered DTMF OTP digits and re-prompts until valid."""
    call_uuid = request.values.get("CallUUID")
    digits = (request.values.get("Digits") or "").strip()

    logger.info(f"OTP verification request: UUID={call_uuid}, Digits entered='{digits}'")

    if digits == config.caller_birthdate_otp:
        logger.info(f"OTP verified successfully for CallUUID={call_uuid}")
        event_tracker.add_event(
            stage="OTP_VERIFIED",
            message=f"OTP '{digits}' matched successfully. Caller authenticated.",
            call_uuid=call_uuid,
            details={"digits": digits},
        )
        xml = build_otp_success_xml()
        return xml_response(xml)
    else:
        logger.warning(f"OTP verification failed for CallUUID={call_uuid}. Expected {config.caller_birthdate_otp}, got '{digits}'")
        event_tracker.add_event(
            stage="OTP_FAILED",
            message=f"Incorrect OTP '{digits}' entered. Re-prompting caller.",
            call_uuid=call_uuid,
            details={"digits_entered": digits, "expected": config.caller_birthdate_otp},
        )
        error_msg = "Incorrect OTP entered. Please enter your valid 4-digit birthdate in day and month format."
        xml = build_otp_prompt_xml(error_message=error_msg)
        return xml_response(xml)


@app.route("/ivr/menu/level1", methods=["GET", "POST"])
def ivr_menu_level1():
    """Presents Level 1 Language Selection Menu."""
    call_uuid = request.values.get("CallUUID")
    logger.info(f"Presenting Level 1 Language menu for CallUUID={call_uuid}")

    event_tracker.add_event(
        stage="LEVEL1_MENU",
        message="Presenting Level 1: Language selection (1: English, 2: Spanish).",
        call_uuid=call_uuid,
    )

    xml = build_level1_language_menu_xml()
    return xml_response(xml)


@app.route("/ivr/menu/level1/select", methods=["GET", "POST"])
def ivr_menu_level1_select():
    """Handles Level 1 Language selection."""
    call_uuid = request.values.get("CallUUID")
    digits = (request.values.get("Digits") or "").strip()

    logger.info(f"Level 1 selection: CallUUID={call_uuid}, Digits='{digits}'")

    if digits == "1":
        event_tracker.add_event(
            stage="LANGUAGE_SELECTED",
            message="Caller selected English (Option 1).",
            call_uuid=call_uuid,
            details={"language": "en"},
        )
        xml = build_level2_action_menu_xml(language="en")
        return xml_response(xml)
    elif digits == "2":
        event_tracker.add_event(
            stage="LANGUAGE_SELECTED",
            message="Caller selected Spanish (Option 2).",
            call_uuid=call_uuid,
            details={"language": "es"},
        )
        xml = build_level2_action_menu_xml(language="es")
        return xml_response(xml)
    else:
        logger.warning(f"Invalid language selection: '{digits}'")
        event_tracker.add_event(
            stage="INVALID_INPUT",
            message=f"Invalid language selection '{digits}'. Re-prompting Level 1.",
            call_uuid=call_uuid,
            details={"digits": digits},
        )
        error_msg = "Invalid selection. For English, press 1. Para español, oprima 2."
        xml = build_level1_language_menu_xml(error_message=error_msg)
        return xml_response(xml)


@app.route("/ivr/menu/level2", methods=["GET", "POST"])
def ivr_menu_level2():
    """Presents Level 2 Action Menu for chosen language."""
    call_uuid = request.values.get("CallUUID")
    language = request.args.get("lang", "en").lower()

    logger.info(f"Presenting Level 2 menu: CallUUID={call_uuid}, lang={language}")
    xml = build_level2_action_menu_xml(language=language)
    return xml_response(xml)


@app.route("/ivr/menu/level2/action", methods=["GET", "POST"])
def ivr_menu_level2_action():
    """Handles Level 2 Action selection (1: Play Audio, 2: Forward Call)."""
    call_uuid = request.values.get("CallUUID")
    language = request.args.get("lang", "en").lower()
    digits = (request.values.get("Digits") or "").strip()

    logger.info(f"Level 2 action chosen: CallUUID={call_uuid}, lang={language}, Digits='{digits}'")

    if digits == "1":
        event_tracker.add_event(
            stage="ACTION_AUDIO_PLAYBACK",
            message=f"Caller chose Option 1: Playing audio message ({language.upper()}).",
            call_uuid=call_uuid,
            details={"audio_url": config.audio_url, "language": language},
        )
        xml = build_play_audio_xml(language=language)
        return xml_response(xml)
    elif digits == "2":
        event_tracker.add_event(
            stage="ACTION_CALL_FORWARD",
            message=f"Caller chose Option 2: Forwarding call to associate ({config.live_associate_number}).",
            call_uuid=call_uuid,
            details={"associate_number": config.live_associate_number, "language": language},
        )
        xml = build_forward_associate_xml(language=language)
        return xml_response(xml)
    else:
        logger.warning(f"Invalid Level 2 selection: '{digits}'")
        event_tracker.add_event(
            stage="INVALID_INPUT",
            message=f"Invalid Level 2 selection '{digits}'. Re-prompting Level 2.",
            call_uuid=call_uuid,
            details={"digits": digits, "language": language},
        )
        if language == "es":
            error_msg = "Opción inválida. Presione 1 para escuchar un mensaje de audio. Presione 2 para conectarse con un asesor."
        else:
            error_msg = "Invalid selection. Press 1 to play a short audio message. Press 2 to connect to a live associate."
        xml = build_level2_action_menu_xml(language=language, error_message=error_msg)
        return xml_response(xml)


@app.route("/ivr/hangup", methods=["GET", "POST"])
def ivr_hangup():
    """Captures call completion and hangup events."""
    call_uuid = request.values.get("CallUUID")
    duration = request.values.get("Duration")
    hangup_cause = request.values.get("HangupCause")

    logger.info(f"Call hangup: CallUUID={call_uuid}, Duration={duration}s, Cause={hangup_cause}")
    event_tracker.add_event(
        stage="CALL_COMPLETED",
        message=f"Call completed. Duration: {duration or 0}s, Cause: {hangup_cause or 'NORMAL_CLEARING'}",
        call_uuid=call_uuid,
        details={"duration": duration, "cause": hangup_cause},
    )
    return xml_response("<Response></Response>")


def run_app():
    """Starts the Flask server."""
    logger.info(f"Starting Plivo IVR server on port {config.port}...")
    app.run(host="0.0.0.0", port=config.port, debug=False)


if __name__ == "__main__":
    run_app()
