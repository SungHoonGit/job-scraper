#!/bin/bash
# Job Scraper - 한방 설치 스크립트
# Usage: bash setup.sh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== Job Scraper Setup ==="
echo "Project: $PROJECT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Install Python 3.8+ first."
    exit 1
fi
echo "[OK] Python $(python3 --version)"

# Install dependencies (macOS Sequoia+ 호환)
echo "Installing dependencies..."
if python3 -c "import requests, bs4, lxml" 2>/dev/null; then
    echo "[OK] Already installed"
else
    pip3 install requests beautifulsoup4 lxml --break-system-packages -q 2>/dev/null \
        || pip3 install requests beautifulsoup4 lxml --user -q 2>/dev/null \
        || pip3 install requests beautifulsoup4 lxml -q
    echo "[OK] Dependencies installed"
fi

# Create config from example
if [ ! -f config.json ]; then
    cp config.example.json config.json
    echo "[OK] config.json created (edit it first!)"
else
    echo "[OK] config.json exists"
fi

# Create daily directory
mkdir -p daily
echo "[OK] daily/ directory ready"

# Parse schedule from config.json
SCHEDULE_ENABLED=$(python3 -c "import json; c=json.load(open('config.json')); print(str(c.get('schedule', {}).get('enabled', False)).lower())" 2>/dev/null || echo "false")
SCHEDULE_HOUR=$(python3 -c "import json; c=json.load(open('config.json')); print(c.get('schedule', {}).get('hour', 10))" 2>/dev/null || echo "10")
SCHEDULE_MINUTE=$(python3 -c "import json; c=json.load(open('config.json')); print(c.get('schedule', {}).get('minute', 0))" 2>/dev/null || echo "0")

if [ "$SCHEDULE_ENABLED" = "true" ]; then
    LABEL="com.jobscraper.daily"
    PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"

    echo ""
    echo "Generating launchd plist..."
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-u</string>
        <string>$PROJECT_DIR/job_scraper.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$SCHEDULE_HOUR</integer>
        <key>Minute</key>
        <integer>$SCHEDULE_MINUTE</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/jobscraper.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/jobscraper.stderr.log</string>
    <key>RunAtLoad</key>
    <false/>
    <key>ProcessType</key>
    <string>Background</string>
    <key>Nice</key>
    <integer>1</integer>
</dict>
</plist>
EOF
    echo "[OK] $PLIST_PATH created"

    # Unload if already loaded (to apply changes)
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    echo "[OK] launchd loaded (매일 $SCHEDULE_HOUR:$SCHEDULE_MINUTE 실행)"
else
    echo "[SKIP] Scheduling disabled in config.json (schedule.enabled: false)"
    echo "  To enable: set schedule.enabled to true and re-run setup.sh"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next:"
echo "  vim config.json              # 검색어/경력/스케줄 수정"
echo "  python3 job_scraper.py       # 수동 실행"
echo ""
echo "Logs: tail -f /tmp/jobscraper.stdout.log"
