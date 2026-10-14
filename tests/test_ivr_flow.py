"""Unit tests for Plivo IVR XML flow generation."""

import unittest
import xml.etree.ElementTree as ET
from plivo_as.ivr_flow import (
    build_otp_prompt_xml,
    build_otp_success_xml,
    build_level1_language_menu_xml,
    build_level2_action_menu_xml,
    build_play_audio_xml,
    build_forward_associate_xml,
    build_dial_status_xml,
)
from plivo_as.config import config


class TestIVRFlow(unittest.TestCase):
    def test_build_otp_prompt_xml(self):
        xml_str = build_otp_prompt_xml()
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "Response")

        # Find GetDigits
        get_digits = root.find("GetDigits")
        self.assertIsNotNone(get_digits)
        self.assertEqual(get_digits.attrib.get("numDigits"), "4")
        self.assertIn("/ivr/otp/verify", get_digits.attrib.get("action"))

        # Verify Speak element inside GetDigits
        speak = get_digits.find("Speak")
        self.assertIsNotNone(speak)
        self.assertIn("OTP", speak.text)

    def test_build_otp_prompt_xml_with_error(self):
        error_msg = "Incorrect OTP entered."
        xml_str = build_otp_prompt_xml(error_message=error_msg)
        root = ET.fromstring(xml_str)
        get_digits = root.find("GetDigits")
        speak = get_digits.find("Speak")
        self.assertEqual(speak.text, error_msg)

    def test_build_otp_success_xml(self):
        xml_str = build_otp_success_xml()
        root = ET.fromstring(xml_str)
        redirect = root.find("Redirect")
        self.assertIsNotNone(redirect)
        self.assertIn("/ivr/menu/level1", redirect.text)

    def test_build_level1_language_menu_xml(self):
        xml_str = build_level1_language_menu_xml()
        root = ET.fromstring(xml_str)
        get_digits = root.find("GetDigits")
        self.assertIsNotNone(get_digits)
        self.assertEqual(get_digits.attrib.get("numDigits"), "1")
        self.assertIn("/ivr/menu/level1/select", get_digits.attrib.get("action"))

        speak = get_digits.find("Speak")
        self.assertIn("English", speak.text)
        self.assertIn("español", speak.text)

    def test_build_level2_english_menu_xml(self):
        xml_str = build_level2_action_menu_xml(language="en")
        root = ET.fromstring(xml_str)
        get_digits = root.find("GetDigits")
        self.assertIsNotNone(get_digits)
        self.assertIn("lang=en", get_digits.attrib.get("action"))

        speak = get_digits.find("Speak")
        self.assertIn("English", speak.text)
        self.assertIn("audio message", speak.text)
        self.assertIn("live associate", speak.text)

    def test_build_level2_spanish_menu_xml(self):
        xml_str = build_level2_action_menu_xml(language="es")
        root = ET.fromstring(xml_str)
        get_digits = root.find("GetDigits")
        self.assertIsNotNone(get_digits)
        self.assertIn("lang=es", get_digits.attrib.get("action"))

        speak = get_digits.find("Speak")
        self.assertEqual(speak.attrib.get("language"), "es-ES")
        self.assertIn("español", speak.text)

    def test_build_play_audio_xml_en(self):
        xml_str = build_play_audio_xml(language="en")
        root = ET.fromstring(xml_str)
        play = root.find("Play")
        self.assertIsNotNone(play)
        self.assertEqual(play.text, config.audio_url)
        hangup = root.find("Hangup")
        self.assertIsNotNone(hangup)

    def test_build_play_audio_xml_es(self):
        xml_str = build_play_audio_xml(language="es")
        root = ET.fromstring(xml_str)
        play = root.find("Play")
        self.assertIsNotNone(play)
        self.assertEqual(play.text, config.audio_url)

        speaks = root.findall("Speak")
        self.assertTrue(any(s.attrib.get("language") == "es-ES" for s in speaks))

    def test_build_forward_associate_xml(self):
        xml_str = build_forward_associate_xml(language="en")
        root = ET.fromstring(xml_str)
        dial = root.find("Dial")
        self.assertIsNotNone(dial)
        self.assertEqual(dial.attrib.get("callerId"), config.plivo_source_number)
        self.assertIn("/ivr/dial/status", dial.attrib.get("action"))

        number = dial.find("Number")
        self.assertIsNotNone(number)
        self.assertEqual(number.text, config.formatted_live_associate_number)

    def test_build_dial_status_xml_completed(self):
        xml_str = build_dial_status_xml("completed", language="en")
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "Response")
        speak = root.find("Speak")
        self.assertIn("Thank you for speaking with our associate", speak.text)
        self.assertIsNotNone(root.find("Hangup"))

    def test_build_dial_status_xml_unavailable(self):
        xml_str = build_dial_status_xml("busy", language="en")
        root = ET.fromstring(xml_str)
        speak = root.find("Speak")
        self.assertIn("unavailable", speak.text)


if __name__ == "__main__":
    unittest.main()
