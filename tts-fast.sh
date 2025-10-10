#!/bin/bash
# Blazing Fast TTS with ONNX decoder
# This is the FASTEST version!

cd "$(dirname "$0")"
source venv/bin/activate
python blazing_fast_tts.py --onnx "$@"

