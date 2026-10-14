"""Command-line interface for Plivo IVR application."""

import argparse
import sys
from .config import config
from .plivo_service import plivo_service
from .app import run_app


def parse_args():
    parser = argparse.ArgumentParser(
        description="InspireWorks Plivo Multi-Level IVR System CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: server
    server_parser = subparsers.add_parser("server", help="Start the Flask IVR webhook server")
    server_parser.add_argument("--port", type=int, default=config.port, help="Port to run Flask server on")

    # Command: call
    call_parser = subparsers.add_parser("call", help="Initiate an outbound demo IVR call")
    call_parser.add_argument(
        "--to",
        dest="to_number",
        required=True,
        type=str,
        help="Target phone number in E.164 format (e.g. +919876543210)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == "call":
        to_number = args.to_number.strip()
        print(f"\n📞 Initiating outbound IVR call to: {to_number}")
        print(f"   From Plivo Number: {config.plivo_source_number}")
        print(f"   Webhook Answer URL: {config.get_webhook_url('/ivr/otp')}")
        print(f"   Default Hardcoded OTP: {config.caller_birthdate_otp}\n")

        result = plivo_service.trigger_outbound_call(to_number)
        if result.get("success"):
            print("✅ Call successfully initiated and queued with Plivo!")
            print(f"   Request UUID: {result.get('request_uuid')}")
            print(f"   Status: {result.get('message')}")
            print("\n👉 Answer your phone to begin OTP authentication and explore the IVR menu.\n")
        else:
            print("❌ Call initiation failed:")
            print(f"   Error: {result.get('error')}\n")
            sys.exit(1)

    elif args.command == "server" or args.command is None:
        print(f"\n🚀 Starting InspireWorks Plivo IVR Server on http://0.0.0.0:{config.port}")
        print(f"   Base URL configured: {config.base_url}")
        print(f"   Hardcoded OTP: {config.caller_birthdate_otp}")
        print(f"   Plivo Source Number: {config.plivo_source_number}")
        print(f"   Live Associate Number: {config.live_associate_number}\n")
        run_app()


if __name__ == "__main__":
    main()
