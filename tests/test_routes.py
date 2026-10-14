"""Integration tests for Flask routes and Plivo webhook endpoints."""

import unittest
from plivo_as.app import app
from plivo_as.config import config


class TestFlaskRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"InspireWorks IVR Console", response.data)
        self.assertIn(config.caller_birthdate_otp.encode(), response.data)

    def test_api_config(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["caller_birthdate_otp"], config.caller_birthdate_otp)
        self.assertEqual(data["plivo_source_number"], config.plivo_source_number)
        self.assertEqual(data["live_associate_number"], config.live_associate_number)

    def test_api_call_validation(self):
        # Empty payload
        response = self.client.post("/api/call", json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_ivr_otp_prompt_route(self):
        response = self.client.post("/ivr/otp", data={"CallUUID": "test-uuid-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        self.assertIn(b"<GetDigits", response.data)
        self.assertIn(b'numDigits="4"', response.data)

    def test_ivr_otp_verify_incorrect(self):
        # Incorrect OTP entered (e.g. 0000 instead of 2404)
        response = self.client.post(
            "/ivr/otp/verify",
            data={"CallUUID": "test-uuid-1", "Digits": "0000"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        self.assertIn(b"Incorrect OTP", response.data)
        self.assertIn(b"<GetDigits", response.data)

    def test_ivr_otp_verify_correct(self):
        # Correct OTP entered
        response = self.client.post(
            "/ivr/otp/verify",
            data={"CallUUID": "test-uuid-1", "Digits": config.caller_birthdate_otp},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        self.assertIn(b"Authentication successful", response.data)
        self.assertIn(b"/ivr/menu/level1", response.data)

    def test_ivr_menu_level1_route(self):
        response = self.client.post("/ivr/menu/level1", data={"CallUUID": "test-uuid-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        self.assertIn(b"For English, press 1. Para", response.data)

    def test_ivr_menu_level1_select_english(self):
        response = self.client.post(
            "/ivr/menu/level1/select",
            data={"CallUUID": "test-uuid-1", "Digits": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        self.assertIn(b"lang=en", response.data)
        self.assertIn(b"You have selected English", response.data)

    def test_ivr_menu_level1_select_spanish(self):
        response = self.client.post(
            "/ivr/menu/level1/select",
            data={"CallUUID": "test-uuid-1", "Digits": "2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        self.assertIn(b"lang=es", response.data)
        self.assertIn(b"Ha seleccionado", response.data)

    def test_ivr_menu_level1_select_invalid(self):
        response = self.client.post(
            "/ivr/menu/level1/select",
            data={"CallUUID": "test-uuid-1", "Digits": "9"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid selection", response.data)

    def test_ivr_menu_level2_action_audio(self):
        response = self.client.post(
            "/ivr/menu/level2/action?lang=en",
            data={"CallUUID": "test-uuid-1", "Digits": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<Play>", response.data)
        self.assertIn(b"<Hangup/>", response.data)

    def test_ivr_menu_level2_action_forward(self):
        response = self.client.post(
            "/ivr/menu/level2/action?lang=en",
            data={"CallUUID": "test-uuid-1", "Digits": "2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<Dial", response.data)
        self.assertIn(config.live_associate_number.encode(), response.data)

    def test_ivr_hangup_route(self):
        response = self.client.post(
            "/ivr/hangup",
            data={"CallUUID": "test-uuid-1", "Duration": "45", "HangupCause": "NORMAL_CLEARING"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<Response></Response>", response.data)


if __name__ == "__main__":
    unittest.main()
