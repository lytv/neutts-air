#!/bin/bash
# Quick launcher for Interactive TTS

cd "$(dirname "$0")"
source venv/bin/activate
python interactive_tts.py "$@"

