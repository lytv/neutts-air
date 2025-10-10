#!/bin/bash
# Check TTS Service Status

echo "🔍 TTS Service Status"
echo "=" | tr '=' '=' | head -c 60; echo
echo ""

# Check if service is running
if pgrep -f tts_service.py > /dev/null; then
    echo "✅ TTS Service: RUNNING"
    SERVICE_PID=$(pgrep -f tts_service.py)
    echo "   PID: $SERVICE_PID"
    
    # Get memory usage
    if command -v ps > /dev/null; then
        MEM=$(ps -o rss= -p $SERVICE_PID | awk '{print $1/1024 " MB"}')
        echo "   Memory: ~$MEM"
    fi
else
    echo "❌ TTS Service: NOT RUNNING"
fi

echo ""

# Check if hotkey client is running
if pgrep -f tts_hotkey.py > /dev/null; then
    echo "✅ Hotkey Client: RUNNING"
    HOTKEY_PID=$(pgrep -f tts_hotkey.py)
    echo "   PID: $HOTKEY_PID"
else
    echo "❌ Hotkey Client: NOT RUNNING"
fi

echo ""

# Check socket file
if [ -S /tmp/tts_service.sock ]; then
    echo "✅ Socket: /tmp/tts_service.sock (exists)"
else
    echo "❌ Socket: NOT FOUND"
fi

echo ""
echo "=" | tr '=' '=' | head -c 60; echo

# Show process details if running
if pgrep -f "tts_service.py\|tts_hotkey.py" > /dev/null; then
    echo ""
    echo "Process Details:"
    echo "=" | tr '=' '=' | head -c 60; echo
    ps aux | grep -E "tts_service|tts_hotkey" | grep -v grep | grep -v status
    echo "=" | tr '=' '=' | head -c 60; echo
    echo ""
    echo "Logs:"
    echo "  • Service: tail -f /tmp/tts_service.log"
    echo "  • Hotkey:  tail -f /tmp/tts_hotkey.log"
    echo ""
    echo "Control:"
    echo "  • Stop:    ./tts-stop.sh"
    echo "  • Hotkeys: Cmd+Shift+S (speak), Cmd+Shift+Q (quit)"
else
    echo ""
    echo "To start service: ./tts-start.sh"
fi

echo "=" | tr '=' '=' | head -c 60; echo

