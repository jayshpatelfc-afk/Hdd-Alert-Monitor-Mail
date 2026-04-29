import os
import sys
import json
import smtplib
import platform
import subprocess
import socket
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hdd_config.json")
def load_config():
    """Load email config from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        print("❌  Config file not found! Please run setup_email.py first.")
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
def get_drive_letter():
    """Auto-detect which drive letter this script is running from."""
    script_path = os.path.abspath(__file__)
    drive = os.path.splitdrive(script_path)[0]
    return drive if drive else "Unknown"
def get_drive_info(drive_letter):
    """Get total, used, and free space of the drive."""
    info = {}
    try:
        import shutil
        total, used, free = shutil.disk_usage(drive_letter + "\\")
        info["total_gb"]  = round(total / (1024**3), 2)
        info["used_gb"]   = round(used  / (1024**3), 2)
        info["free_gb"]   = round(free  / (1024**3), 2)
        info["used_pct"]  = round((used / total) * 100, 1)
    except Exception as e:
        info["error"] = str(e)
    return info
def get_smart_status(drive_letter):
    """
    Try to read S.M.A.R.T. data using wmic (Windows) or smartctl (Linux/Mac).
    Returns a dict with health info.
    """
    smart = {}
    system = platform.system()

    if system == "Windows":
        try:
            # Use wmic to get drive status
            result = subprocess.run(
                ["wmic", "diskdrive", "get",
                 "Caption,Status,Size,InterfaceType,SerialNumber,FirmwareRevision",
                 "/format:csv"],
                capture_output=True, text=True, timeout=15
            )
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and l.strip() != "Node"]
            if len(lines) >= 2:
                headers = lines[0].split(",")
                for row in lines[1:]:
                    values = row.split(",")
                    if len(values) == len(headers):
                        entry = dict(zip(headers, values))
                        smart["caption"]       = entry.get("Caption", "N/A")
                        smart["status"]        = entry.get("Status", "N/A")
                        smart["interface"]     = entry.get("InterfaceType", "N/A")
                        smart["serial"]        = entry.get("SerialNumber", "N/A")
                        smart["firmware"]      = entry.get("FirmwareRevision", "N/A")
                        size_bytes = entry.get("Size", "0")
                        if size_bytes.isdigit():
                            smart["size_gb"] = round(int(size_bytes) / (1024**3), 2)
                        break  # take the first external drive found
        except Exception as e:
            smart["wmic_error"] = str(e)

        # Try smartctl if available (needs to be installed separately)
        try:
            result = subprocess.run(
                ["smartctl", "-H", drive_letter],
                capture_output=True, text=True, timeout=15
            )
            output = result.stdout
            if "PASSED" in output:
                smart["smart_health"] = "✅ PASSED"
            elif "FAILED" in output:
                smart["smart_health"] = "❌ FAILED — BACKUP DATA IMMEDIATELY!"
            else:
                smart["smart_health"] = "⚠️ Unknown (smartctl installed but no result)"
        except FileNotFoundError:
            smart["smart_health"] = "ℹ️ smartctl not installed (install for deep S.M.A.R.T. check)"
        except Exception as e:
            smart["smart_health"] = f"⚠️ smartctl error: {e}"

    elif system in ("Linux", "Darwin"):
        try:
            result = subprocess.run(
                ["smartctl", "-H", "-i", drive_letter],
                capture_output=True, text=True, timeout=15
            )
            output = result.stdout
            smart["raw_output"] = output[:1500]
            smart["smart_health"] = "✅ PASSED" if "PASSED" in output else (
                "❌ FAILED" if "FAILED" in output else "⚠️ Unknown"
            )
        except FileNotFoundError:
            smart["smart_health"] = "ℹ️ smartctl not found. Install with: sudo apt install smartmontools"
        except Exception as e:
            smart["smart_health"] = str(e)
    else:
        smart["smart_health"] = "Unsupported OS"

    return smart
def get_system_info():
    return {
        "hostname":    socket.gethostname(),
        "os":          f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "processor":   platform.processor() or "N/A",
        "python":      platform.python_version(),
        "timestamp":   datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
def get_file_stats(drive_letter, top_n=5):
    """Count files at root level and find largest files (fast scan)."""
    stats = {"root_items": 0, "large_files": []}
    try:
        root_path = Path(drive_letter + "\\")
        items = list(root_path.iterdir())
        stats["root_items"] = len(items)

        all_files = []
        for item in items:
            if item.is_file():
                try:
                    all_files.append((item.name, item.stat().st_size))
                except Exception:
                    pass

        all_files.sort(key=lambda x: x[1], reverse=True)
        stats["large_files"] = [
            {"name": name, "size_mb": round(size / (1024**2), 2)}
            for name, size in all_files[:top_n]
        ]
    except Exception as e:
        stats["error"] = str(e)
    return stats
def build_html_email(drive_letter, drive_info, smart, sys_info, file_stats):
    """Create a clean, professional HTML email body."""

    status_color = "#27ae60"  # green by default
    status_label = "✅ HEALTHY"
    health_text  = smart.get("smart_health", "N/A")

    if "FAILED" in health_text:
        status_color = "#e74c3c"
        status_label = "❌ CRITICAL — DRIVE FAILURE DETECTED"
    elif "PASSED" not in health_text and "ℹ️" not in health_text:
        status_color = "#f39c12"
        status_label = "⚠️ WARNING — CHECK REQUIRED"

    used_pct = drive_info.get("used_pct", 0)
    bar_color = "#e74c3c" if used_pct > 90 else ("#f39c12" if used_pct > 75 else "#27ae60")

    large_files_html = ""
    for f in file_stats.get("large_files", []):
        large_files_html += f"""
        <tr>
          <td style="padding:6px 10px; border-bottom:1px solid #eee;">{f['name']}</td>
          <td style="padding:6px 10px; border-bottom:1px solid #eee; text-align:right;">{f['size_mb']} MB</td>
        </tr>"""

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background:#f5f5f5; margin:0; padding:20px;">

  <div style="max-width:600px; margin:auto; background:#fff; border-radius:10px;
              box-shadow:0 2px 8px rgba(0,0,0,0.12); overflow:hidden;">

    <!-- HEADER -->
    <div style="background:{status_color}; padding:24px 30px; color:#fff;">
      <h1 style="margin:0; font-size:22px;">🔌 External HDD Connected</h1>
      <p style="margin:6px 0 0; font-size:15px; opacity:0.92;">
        Drive <strong>{drive_letter}</strong> was just plugged into <strong>{sys_info['hostname']}</strong>
      </p>
    </div>

    <!-- STATUS BADGE -->
    <div style="background:{status_color}22; border-left:5px solid {status_color};
                margin:20px 30px; padding:14px 18px; border-radius:4px;">
      <strong style="font-size:16px; color:{status_color};">{status_label}</strong><br>
      <span style="color:#555; font-size:13px;">S.M.A.R.T. Status: {health_text}</span>
    </div>

    <div style="padding:0 30px 20px;">

      <!-- DRIVE USAGE -->
      <h2 style="font-size:15px; color:#333; border-bottom:1px solid #eee; padding-bottom:8px;">
        💾 Drive Usage — {drive_letter}
      </h2>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Total Capacity</td>
          <td style="text-align:right; font-size:14px; font-weight:600;">{drive_info.get('total_gb', 'N/A')} GB</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Used Space</td>
          <td style="text-align:right; font-size:14px; font-weight:600; color:{bar_color};">
            {drive_info.get('used_gb', 'N/A')} GB ({used_pct}%)
          </td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Free Space</td>
          <td style="text-align:right; font-size:14px; font-weight:600; color:#27ae60;">
            {drive_info.get('free_gb', 'N/A')} GB
          </td>
        </tr>
      </table>
      <!-- Progress Bar -->
      <div style="background:#eee; border-radius:20px; height:10px; margin:12px 0 20px;">
        <div style="background:{bar_color}; width:{min(used_pct,100)}%; height:10px;
                    border-radius:20px;"></div>
      </div>

      <!-- DRIVE DETAILS -->
      <h2 style="font-size:15px; color:#333; border-bottom:1px solid #eee; padding-bottom:8px;">
        🔧 Drive Details
      </h2>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Drive Name</td>
          <td style="text-align:right; font-size:14px;">{smart.get('caption', 'N/A')}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Interface</td>
          <td style="text-align:right; font-size:14px;">{smart.get('interface', 'N/A')}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Serial Number</td>
          <td style="text-align:right; font-size:14px;">{smart.get('serial', 'N/A')}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Firmware</td>
          <td style="text-align:right; font-size:14px;">{smart.get('firmware', 'N/A')}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">WMIC Status</td>
          <td style="text-align:right; font-size:14px;">{smart.get('status', 'N/A')}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Root Items Count</td>
          <td style="text-align:right; font-size:14px;">{file_stats.get('root_items', 'N/A')} items</td>
        </tr>
      </table>

      <!-- LARGE FILES -->
      {"<h2 style='font-size:15px; color:#333; border-bottom:1px solid #eee; padding-bottom:8px; margin-top:20px;'>📁 Largest Files at Root</h2><table width='100%' cellpadding='0' cellspacing='0'>" + large_files_html + "</table>" if large_files_html else ""}

      <!-- SYSTEM INFO -->
      <h2 style="font-size:15px; color:#333; border-bottom:1px solid #eee; padding-bottom:8px; margin-top:20px;">
        🖥️ Connected Computer
      </h2>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Hostname</td>
          <td style="text-align:right; font-size:14px;">{sys_info['hostname']}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Operating System</td>
          <td style="text-align:right; font-size:14px;">{sys_info['os']}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Architecture</td>
          <td style="text-align:right; font-size:14px;">{sys_info['architecture']}</td>
        </tr>
        <tr>
          <td style="padding:4px 0; color:#555; font-size:14px;">Connected At</td>
          <td style="text-align:right; font-size:14px;">{sys_info['timestamp']}</td>
        </tr>
      </table>

    </div>

    <!-- FOOTER -->
    <div style="background:#f9f9f9; padding:14px 30px; text-align:center;
                font-size:12px; color:#999; border-top:1px solid #eee;">
      This is an automated alert from your External HDD Monitor script.<br>
      Stored on drive {drive_letter} | Sent by hdd_monitor.py
    </div>
  </div>

</body>
</html>
"""
    return html
def send_email(config, subject, html_body):
    """Send HTML email via Gmail SMTP (App Password)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"HDD Monitor <{config['sender_email']}>"
    msg["To"]      = config["receiver_email"]
    msg["X-Priority"] = "1"          # Mark as HIGH IMPORTANCE
    msg["Importance"] = "High"

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(config["sender_email"], config["app_password"])
            server.sendmail(config["sender_email"], config["receiver_email"], msg.as_string())
        print("✅  Email sent successfully!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌  Authentication failed. Check your App Password in hdd_config.json")
        return False
    except Exception as e:
        print(f"❌  Failed to send email: {e}")
        return False
def write_log(drive_letter, sys_info, health_text):
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hdd_connection_log.txt")
    with open(log_file, "a") as f:
        f.write(f"[{sys_info['timestamp']}] Connected to: {sys_info['hostname']} ({sys_info['os']}) | "
                f"Drive: {drive_letter} | Health: {health_text}\n")
def main():
    print("="*55)
    print("  HDD Monitor — Starting Up")
    print("="*55)

    config      = load_config()
    drive       = get_drive_letter()
    drive_info  = get_drive_info(drive)
    smart       = get_smart_status(drive)
    sys_info    = get_system_info()
    file_stats  = get_file_stats(drive)

    print(f"  Drive     : {drive}")
    print(f"  Hostname  : {sys_info['hostname']}")
    print(f"  OS        : {sys_info['os']}")
    print(f"  Health    : {smart.get('smart_health', 'N/A')}")
    print(f"  Used      : {drive_info.get('used_pct', '?')}%")
    print("-"*55)

    # Compose subject with urgency indicator
    health = smart.get("smart_health", "")
    if "FAILED" in health:
        subject = f"🚨 URGENT: HDD FAILURE on {sys_info['hostname']} — Backup Now!"
    else:
        subject = f"🔌 HDD Connected: {drive} on {sys_info['hostname']} [{sys_info['timestamp']}]"

    html = build_html_email(drive, drive_info, smart, sys_info, file_stats)

    print("  Sending email alert...")
    send_email(config, subject, html)

    write_log(drive, sys_info, smart.get("smart_health", "Unknown"))
    print("  Log updated → hdd_connection_log.txt")
    print("="*55)
if __name__ == "__main__":
    main()
