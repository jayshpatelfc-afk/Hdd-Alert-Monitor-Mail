"""
=============================================================
  HDD Monitor — One-Time Email Setup
  ------------------------------------
  Run this ONCE on your PC to save your Gmail credentials.
  The config is saved as hdd_config.json on the HDD.

  HOW TO GET A GMAIL APP PASSWORD:
  1. Go to https://myaccount.google.com/security
  2. Enable 2-Step Verification (if not already)
  3. Go to "App Passwords" (search it in the page)
  4. Select "Mail" → "Windows Computer" → Generate
  5. Copy the 16-character password shown
=============================================================
"""

import json
import os
import smtplib
import getpass

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hdd_config.json")


def test_credentials(sender, password, receiver):
    """Quick test to verify Gmail credentials work."""
    print("\n  Testing connection to Gmail...")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender, password)
        print("  ✅  Login successful!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("  ❌  Authentication failed.")
        print("      → Make sure you are using an APP PASSWORD, not your regular Gmail password.")
        print("      → Visit: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"  ❌  Connection error: {e}")
        return False


def main():
    print("="*55)
    print("  HDD Monitor — Email Setup Wizard")
    print("="*55)
    print()

    print("  ℹ️  You need a Gmail ACCOUNT + APP PASSWORD.")
    print("  ℹ️  Get App Password at: https://myaccount.google.com/apppasswords")
    print()

    sender   = input("  Enter YOUR Gmail address (sender): ").strip()
    password = getpass.getpass("  Enter Gmail APP PASSWORD (16 chars, no spaces): ").strip().replace(" ", "")
    receiver = input("  Enter RECEIVER email (alert will be sent here): ").strip()

    print()

    if not sender or not password or not receiver:
        print("  ❌  All fields are required. Please run again.")
        return

    if test_credentials(sender, password, receiver):
        config = {
            "sender_email":   sender,
            "app_password":   password,
            "receiver_email": receiver
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

        print(f"\n  ✅  Config saved to: {CONFIG_FILE}")
        print("  ✅  Setup complete! hdd_monitor.py is ready to use.")
        print()
        print("  Next Step → Set up AutoRun:")
        print("  • Copy autorun.inf to the ROOT of your HDD.")
        print("  • Also copy hdd_monitor.py and hdd_config.json to ROOT.")
        print()
    else:
        print("\n  ❌  Setup failed. Please check your credentials and try again.")


if __name__ == "__main__":
    main()
