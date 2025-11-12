#!/bin/bash
# Start TTS Background Service with Hotkey Support

cd "$(dirname "$0")"

echo "🚀 Starting TTS Background Service..."
echo "=" | tr '=' '=' | head -c 60; echo

# Check if already running
if pgrep -f tts_service.py > /dev/null; then
    echo "⚠️  TTS service is already running!"
    echo ""
    echo "Use './tts-status.sh' to check status"
    echo "Use './tts-stop.sh' to stop it first"
    exit 1
fi

# Activate venv and start service in background
source venv/bin/activate

# Start TTS service
echo "📦 Starting TTS service (loading models, ~7-10 seconds)..."
python tts_service.py > /tmp/tts_service_output.log 2>&1 &
SERVICE_PID=$!

# Wait for service to be ready
echo "⏳ Waiting for models to load..."
sleep 12

# Check if service is still running
if ! kill -0 $SERVICE_PID 2>/dev/null; then
    echo "❌ Service failed to start! Check logs:"
    echo "   tail -f /tmp/tts_service.log"
    exit 1
fi

# Start hotkey client
echo "⌨️  Starting hotkey client..."
python tts_hotkey.py > /tmp/tts_hotkey_output.log 2>&1 &
HOTKEY_PID=$!

sleep 2

# Check if hotkey client is running
if ! kill -0 $HOTKEY_PID 2>/dev/null; then
    echo "❌ Hotkey client failed to start! Check logs:"
    echo "   tail -f /tmp/tts_hotkey.log"
    pkill -f tts_service.py
    exit 1
fi

echo ""
echo "=" | tr '=' '=' | head -c 60; echo
echo "✅ TTS Service is READY!"
echo "=" | tr '=' '=' | head -c 60; echo
echo ""
echo "Hotkeys:"
echo "  • Control+Right Arrow  →  Read clipboard text"
echo "  • Control+Left Arrow   →  Replay last audio"
echo "  • Cmd+Shift+Q  →  Stop service and quit"
echo ""
echo "Logs:"
echo "  • Service: tail -f /tmp/tts_service.log"
echo "  • Hotkey:  tail -f /tmp/tts_hotkey.log"
echo ""
echo "Memory usage: ~2GB RAM (models loaded)"
echo ""
echo "To stop manually: ./tts-stop.sh"
echo "=" | tr '=' '=' | head -c 60; echo

