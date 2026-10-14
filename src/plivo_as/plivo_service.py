"""Service layer for Plivo API interactions."""

import logging
from typing import Dict, Any
import plivo
from .config import config
from .events import event_tracker

logger = logging.getLogger(__name__)


class PlivoService:
    def __init__(self):
        self.client = plivo.RestClient(
            auth_id=config.plivo_auth_id,
            auth_token=config.plivo_auth_token,
        )

    def trigger_outbound_call(self, to_number: str) -> Dict[str, Any]:
        """Initiates an outbound call to the target phone number using Plivo Voice API."""
        answer_url = config.get_webhook_url("/ivr/otp")
        hangup_url = config.get_webhook_url("/ivr/hangup")

        logger.info(f"Triggering outbound call: from={config.plivo_source_number} to={to_number} answer_url={answer_url}")

        event_tracker.add_event(
            stage="CALL_INITIATED",
            message=f"Outbound call initiated to {to_number}",
            details={"from": config.plivo_source_number, "to": to_number, "answer_url": answer_url},
        )

        try:
            response = self.client.calls.create(
                from_=config.plivo_source_number,
                to_=to_number,
                answer_url=answer_url,
                answer_method="POST",
                hangup_url=hangup_url,
                hangup_method="POST",
            )

            # Plivo SDK returns response with message and request_uuid
            request_uuid = getattr(response, "request_uuid", None) or getattr(response, "call_uuid", None)
            logger.info(f"Call initiated successfully: request_uuid={request_uuid}")

            event_tracker.add_event(
                stage="CALL_QUEUED",
                message=f"Plivo queued call successfully (Request UUID: {request_uuid})",
                call_uuid=request_uuid,
                details={"response": str(response)},
            )

            return {
                "success": True,
                "request_uuid": request_uuid,
                "message": getattr(response, "message", "Call created"),
            }
        except Exception as e:
            logger.error(f"Error initiating call: {e}", exc_info=True)
            event_tracker.add_event(
                stage="CALL_FAILED",
                message=f"Failed to initiate call: {str(e)}",
                details={"error": str(e)},
            )
            return {
                "success": False,
                "error": str(e),
            }


plivo_service = PlivoService()
