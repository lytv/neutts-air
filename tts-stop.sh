#!/bin/bash
# Stop TTS Background Service and Free RAM

echo "🛑 Stopping TTS Service..."
echo "=" | tr '=' '=' | head -c 60; echo

# Kill processes
if pgrep -f tts_service.py > /dev/null; then
    echo "🔪 Killing TTS service..."
    pkill -f tts_service.py
    sleep 1
fi

if pgrep -f tts_hotkey.py > /dev/null; then
    echo "🔪 Killing hotkey client..."
    pkill -f tts_hotkey.py
    sleep 1
fi

# Remove socket file
if [ -f /tmp/tts_service.sock ]; then
    echo "🗑️  Removing socket file..."
    rm -f /tmp/tts_service.sock
fi

# Verify stopped
if pgrep -f "tts_service.py\|tts_hotkey.py" > /dev/null; then
    echo "⚠️  Some processes still running, forcing kill..."
    pkill -9 -f tts_service.py
    pkill -9 -f tts_hotkey.py
    sleep 1
fi

echo ""
echo "=" | tr '=' '=' | head -c 60; echo
echo "✅ TTS Service stopped"
echo "=" | tr '=' '=' | head -c 60; echo
echo ""
echo "💾 ~2GB RAM has been freed"
echo ""
echo "To start again: ./tts-start.sh"
echo "=" | tr '=' '=' | head -c 60; echo

