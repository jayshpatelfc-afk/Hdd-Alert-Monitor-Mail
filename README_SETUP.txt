===================================================================
  HDD MONITOR & EMAIL ALERT — COMPLETE SETUP GUIDE
===================================================================

WHAT THIS DOES:
  Every time you plug your External HDD into any Windows PC,
  it automatically sends you an important email with:
    ✅  Drive health status (S.M.A.R.T.)
    ✅  Total / Used / Free space
    ✅  Drive name, serial number, interface type
    ✅  Which PC it was connected to (hostname + OS)
    ✅  Date & time of connection
    ✅  Largest files on the drive root
    ✅  Full connection history log (hdd_connection_log.txt)

-------------------------------------------------------------------
  FILES ON YOUR HDD (ROOT FOLDER)
-------------------------------------------------------------------
  hdd_monitor.py          ← Main script (do not rename)
  setup_email.py          ← Run once to save your email
  run_monitor.bat         ← Launcher (triggers the Python script)
  autorun.inf             ← Windows AutoRun config
  hdd_config.json         ← Created by setup_email.py (auto)
  hdd_connection_log.txt  ← Connection log (auto-created)
  README_SETUP.txt        ← This file

-------------------------------------------------------------------
  STEP 1 — COPY FILES TO YOUR HDD
-------------------------------------------------------------------
  Copy ALL the above files to the ROOT (top level) of your HDD.
  Example:  E:\hdd_monitor.py
            E:\run_monitor.bat
            E:\autorun.inf
            etc.

-------------------------------------------------------------------
  STEP 2 — GET A GMAIL APP PASSWORD
-------------------------------------------------------------------
  ⚠️  You MUST use an App Password, NOT your regular Gmail password.

  1. Go to: https://myaccount.google.com/security
  2. Enable "2-Step Verification" (if not already ON)
  3. Search for "App Passwords" on the same page
  4. Click "App Passwords"
  5. Select App: "Mail", Device: "Windows Computer"
  6. Click GENERATE
  7. Copy the 16-character password shown (e.g.: abcd efgh ijkl mnop)

-------------------------------------------------------------------
  STEP 3 — RUN SETUP (ONCE)
-------------------------------------------------------------------
  On ANY PC (your main PC), open Command Prompt:

    cd E:\         (replace E: with your HDD drive letter)
    python setup_email.py

  Enter:
    • Your Gmail address (sender)
    • The 16-char App Password
    • Email where alerts should be sent (can be the same email)

  This saves hdd_config.json on the HDD — done!

-------------------------------------------------------------------
  STEP 4 — ENABLE AUTO-RUN (WINDOWS 10 / 11)
-------------------------------------------------------------------
  Windows 10/11 disabled AutoRun for security.
  Use the TASK SCHEDULER METHOD instead (most reliable):

  METHOD A — Task Scheduler (Recommended):
  ─────────────────────────────────────────
  1. Press  Win + R  →  type  taskschd.msc  → Enter
  2. Click "Create Task" (right panel)
  3. General tab:
       Name: HDD Monitor Alert
       ☑ Run whether user is logged on or not
  4. Triggers tab → New:
       Begin the task: On an event
       Log: System
       Source: disk
       Event ID: 98   ← (USB disk connected event)
  5. Actions tab → New:
       Program: pythonw.exe   (or full path: C:\Python312\pythonw.exe)
       Add arguments: E:\hdd_monitor.py
       (Replace E: with your HDD drive letter)
  6. Click OK, enter your Windows password → Done!

  METHOD B — AutoPlay (Windows 7/8/10 older):
  ─────────────────────────────────────────────
  1. Plug in the HDD
  2. Windows will show "AutoPlay" popup
  3. Select "Run run_monitor.bat"
  4. Next time it plugs in, it auto-runs

  METHOD C — Manual Test (any time):
  ────────────────────────────────────
  Just double-click  run_monitor.bat  on the HDD to test.
  Or run in terminal:  python E:\hdd_monitor.py

-------------------------------------------------------------------
  TROUBLESHOOTING
-------------------------------------------------------------------
  ❌ "No module named smtplib"
     → smtplib is built into Python. Reinstall Python from python.org

  ❌ "Authentication failed"
     → You used your regular Gmail password instead of App Password
     → Go to https://myaccount.google.com/apppasswords and generate one

  ❌ "Config file not found"
     → Run setup_email.py first (Step 3 above)

  ❌ Script runs but no email received
     → Check your Spam/Junk folder
     → Make sure receiver email is correct in hdd_config.json

  ❌ S.M.A.R.T. shows "smartctl not installed"
     → This is OK — basic drive info still works
     → For deep health check, install smartmontools:
        https://www.smartmontools.org/wiki/Download#InstalltheWindowspackage
        Then add its folder to your Windows PATH.

===================================================================
  SECURITY NOTE
===================================================================
  hdd_config.json contains your Gmail App Password.
  • This is an App Password — it only allows sending email.
  • Even if someone copies it, they cannot access your Gmail inbox.
  • You can revoke it anytime at: https://myaccount.google.com/apppasswords
  • Do NOT share the hdd_config.json file with anyone.

===================================================================
