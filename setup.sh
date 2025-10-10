#!/bin/bash
# Automated Setup Script for NeuTTS Air with Hotkey Service
# Optimized for macOS (Apple Silicon)

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        NeuTTS Air - Automated Setup Script                ║"
echo "║        Optimized for macOS (Apple Silicon)                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Setup directory: $SCRIPT_DIR"
echo ""

# Step 1: Check Python version
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/8: Checking Python version..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✅ Found Python $PYTHON_VERSION${NC}"
echo ""

# Step 2: Install espeak
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/8: Installing espeak (required dependency)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v espeak &> /dev/null; then
    echo -e "${GREEN}✅ espeak already installed${NC}"
else
    echo "📦 Installing espeak via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install espeak
        echo -e "${GREEN}✅ espeak installed${NC}"
    else
        echo -e "${RED}❌ Homebrew not found!${NC}"
        echo "Please install Homebrew: https://brew.sh"
        exit 1
    fi
fi
echo ""

# Step 3: Create virtual environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/8: Setting up Python virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists"
    read -p "Recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing old venv..."
        rm -rf venv
        echo "📦 Creating new virtual environment..."
        python3 -m venv venv
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    else
        echo "⏭️  Skipping venv creation"
    fi
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi
echo ""

# Activate venv
source venv/bin/activate

# Step 4: Install core dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/8: Installing core dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "📦 Installing from requirements.txt..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✅ Core dependencies installed${NC}"
echo ""

# Step 5: Install speed optimization packages
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5/8: Installing speed optimization packages..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "📦 Installing llama-cpp-python (GGUF support)..."
pip install --quiet llama-cpp-python
echo -e "${GREEN}✅ llama-cpp-python installed${NC}"

echo "📦 Installing onnxruntime (faster decoding)..."
pip install --quiet onnxruntime
echo -e "${GREEN}✅ onnxruntime installed${NC}"

echo "📦 Installing pynput & pyperclip (hotkey support)..."
pip install --quiet pynput pyperclip
echo -e "${GREEN}✅ Hotkey dependencies installed${NC}"
echo ""

# Step 6: Verify espeak library path
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6/8: Configuring espeak for macOS..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ESPEAK_LIB=$(find /opt/homebrew/Cellar/espeak -name "libespeak.*.*.*.dylib" 2>/dev/null | head -1)
if [ -z "$ESPEAK_LIB" ]; then
    echo -e "${YELLOW}⚠️  espeak library not found in expected location${NC}"
    echo "   Configuration already set in neuttsair/neutts.py"
else
    echo -e "${GREEN}✅ espeak library found: $ESPEAK_LIB${NC}"
    echo "   Configuration already set in neuttsair/neutts.py"
fi
echo ""

# Step 7: Pre-encode sample voices
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7/8: Pre-encoding sample voices..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "samples/dave.pt" ] && [ -f "samples/jo.pt" ]; then
    echo -e "${GREEN}✅ Voices already pre-encoded${NC}"
else
    echo "🎤 Pre-encoding voices (this may take a minute)..."
    echo "   This is done once to speed up future usage"
    
    # Create a quick script to pre-encode
    python3 << 'EOFPYTHON'
import torch
from neuttsair.neutts import NeuTTSAir
from pathlib import Path

print("   Loading TTS models...")
tts = NeuTTSAir(
    backbone_repo="neuphonic/neutts-air-q4-gguf",
    backbone_device="cpu",
    codec_repo="neuphonic/neucodec",
    codec_device="cpu"
)

samples_dir = Path("samples")
for wav_file in samples_dir.glob("*.wav"):
    pt_file = wav_file.with_suffix('.pt')
    if not pt_file.exists():
        print(f"   Encoding {wav_file.name}...")
        ref_codes = tts.encode_reference(str(wav_file))
        torch.save(ref_codes, pt_file)
        print(f"   ✓ Saved {pt_file.name}")

print("   ✅ All voices pre-encoded!")
EOFPYTHON
    
    echo -e "${GREEN}✅ Voices pre-encoded${NC}"
fi
echo ""

# Step 8: Setup aliases
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8/8: Setting up aliases..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if grep -q "alias tts-start=" ~/.zshrc 2>/dev/null; then
    echo "✅ Aliases already exist in ~/.zshrc"
else
    echo "📝 Adding aliases to ~/.zshrc..."
    cat >> ~/.zshrc << EOF

# TTS Hotkey Service aliases
alias tts-start='$SCRIPT_DIR/tts-start.sh'
alias tts-stop='$SCRIPT_DIR/tts-stop.sh'
alias tts-status='$SCRIPT_DIR/tts-status.sh'
alias tts-fast='$SCRIPT_DIR/tts-fast.sh'
EOF
    echo -e "${GREEN}✅ Aliases added${NC}"
    echo "   Run 'source ~/.zshrc' to activate"
fi
echo ""

# Make scripts executable
chmod +x tts-start.sh tts-stop.sh tts-status.sh tts-fast.sh tts_service.py tts_hotkey.py blazing_fast_tts.py 2>/dev/null || true

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ SETUP COMPLETE!                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🎉 NeuTTS Air is ready to use!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "QUICK START"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Activate aliases (one time):"
echo "   ${GREEN}source ~/.zshrc${NC}"
echo ""
echo "2. Start the hotkey service:"
echo "   ${GREEN}tts-start${NC}"
echo "   (or: ./tts-start.sh)"
echo ""
echo "3. Use it:"
echo "   • Copy any text (Cmd+C)"
echo "   • Press ${GREEN}Cmd+Shift+S${NC}"
echo "   • Listen! (~2.3 seconds)"
echo ""
echo "4. Stop service:"
echo "   • Press ${GREEN}Cmd+Shift+Q${NC}"
echo "   • Or: ${GREEN}tts-stop${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "ALIASES"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  tts-start      Start background service"
echo "  tts-stop       Stop service & free RAM"
echo "  tts-status     Check service status"
echo "  tts-fast       Interactive mode"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "PERFORMANCE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  First start:   ~7-10 seconds (load models)"
echo "  Each use:      ~2.3 seconds (clipboard → audio)"
echo "  Memory:        ~2GB RAM while running"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "NEXT STEPS"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Run: ${GREEN}source ~/.zshrc && tts-start${NC}"
echo ""
echo "Then copy text and press ${GREEN}Cmd+Shift+S${NC} to test!"
echo ""
echo "For help: See README.md"
echo ""
echo "═══════════════════════════════════════════════════════════"

