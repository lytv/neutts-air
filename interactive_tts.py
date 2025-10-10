#!/usr/bin/env python3
"""
Interactive TTS - Load once, generate forever!
Giải pháp tối ưu: Load model 1 lần, inference nhiều lần mà không cần reload
"""
import os
import soundfile as sf
import torch
from neuttsair.neutts import NeuTTSAir
import time
from pathlib import Path
import subprocess
import sys


class InteractiveTTS:
    def __init__(self):
        self.tts = None
        self.voices = {}
        self.current_voice = None
        self.output_path = "output.wav"
        
    def initialize(self):
        """Load model one time only"""
        print("=" * 60)
        print("🚀 Interactive TTS - Ultra Fast Mode")
        print("=" * 60)
        print("\n📦 Loading models (this happens only ONCE)...")
        start = time.time()
        
        self.tts = NeuTTSAir(
            backbone_repo="neuphonic/neutts-air-q4-gguf",
            backbone_device="cpu",
            codec_repo="neuphonic/neucodec",
            codec_device="cpu"
        )
        
        load_time = time.time() - start
        print(f"✅ Models loaded in {load_time:.2f}s")
        print("💡 Models are now in memory. Future generations will be INSTANT!\n")
        
        # Load available voices
        self._scan_voices()
        
    def _scan_voices(self):
        """Scan and load all available pre-encoded voices"""
        print("🎤 Scanning available voices...")
        samples_dir = Path("samples")
        
        for pt_file in samples_dir.glob("*.pt"):
            voice_name = pt_file.stem
            txt_file = pt_file.with_suffix(".txt")
            
            if txt_file.exists():
                ref_codes = torch.load(pt_file)
                ref_text = txt_file.read_text().strip()
                self.voices[voice_name] = {
                    'codes': ref_codes,
                    'text': ref_text,
                    'file': pt_file
                }
                print(f"   ✓ {voice_name}")
        
        if not self.voices:
            print("   ⚠️  No pre-encoded voices found. Creating them now...")
            self._create_default_voices()
        
        # Set default voice
        if 'dave' in self.voices:
            self.current_voice = 'dave'
        else:
            self.current_voice = list(self.voices.keys())[0]
        
        print(f"\n🎯 Current voice: {self.current_voice}")
        print()
    
    def _create_default_voices(self):
        """Create pre-encoded voices for samples"""
        samples_dir = Path("samples")
        for wav_file in samples_dir.glob("*.wav"):
            txt_file = wav_file.with_suffix(".txt")
            pt_file = wav_file.with_suffix(".pt")
            
            if txt_file.exists() and not pt_file.exists():
                print(f"   Encoding {wav_file.name}...")
                ref_codes = self.tts.encode_reference(str(wav_file))
                torch.save(ref_codes, pt_file)
                
                ref_text = txt_file.read_text().strip()
                self.voices[wav_file.stem] = {
                    'codes': ref_codes,
                    'text': ref_text,
                    'file': pt_file
                }
                print(f"   ✓ {wav_file.stem}")
    
    def generate(self, text, auto_play=True):
        """Generate speech (FAST - no model loading!)"""
        if not text.strip():
            print("⚠️  Empty text!")
            return
        
        print(f"\n{'='*60}")
        print(f"🎵 Voice: {self.current_voice}")
        print(f"📝 Text: {text}")
        print(f"{'='*60}")
        
        start = time.time()
        
        voice = self.voices[self.current_voice]
        wav = self.tts.infer(text, voice['codes'], voice['text'])
        
        gen_time = time.time() - start
        
        sf.write(self.output_path, wav, 24000)
        
        print(f"✅ Generated in {gen_time:.2f}s")
        print(f"💾 Saved to: {self.output_path}")
        
        if auto_play:
            print("🔊 Playing audio...")
            subprocess.run(['afplay', self.output_path], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        print(f"{'='*60}\n")
        return gen_time
    
    def switch_voice(self, voice_name):
        """Switch to another voice"""
        if voice_name in self.voices:
            self.current_voice = voice_name
            print(f"✅ Switched to voice: {voice_name}\n")
        else:
            print(f"❌ Voice '{voice_name}' not found!")
            self.list_voices()
    
    def list_voices(self):
        """List all available voices"""
        print("\n🎤 Available voices:")
        for name in self.voices.keys():
            marker = "👉" if name == self.current_voice else "  "
            print(f"   {marker} {name}")
        print()
    
    def run_interactive(self):
        """Run in interactive mode"""
        print("💡 Interactive Mode Commands:")
        print("   • Just type text to generate speech")
        print("   • ':voice <name>' - Switch voice (e.g., :voice jo)")
        print("   • ':list' - List all voices")
        print("   • ':quit' or ':q' - Exit")
        print("   • ':help' - Show this help")
        print()
        
        while True:
            try:
                text = input(f"[{self.current_voice}] 💬 Enter text: ").strip()
                
                if not text:
                    continue
                
                # Commands
                if text.startswith(':'):
                    cmd = text[1:].lower().split()
                    
                    if cmd[0] in ['quit', 'q', 'exit']:
                        print("\n👋 Goodbye!")
                        break
                    
                    elif cmd[0] == 'list':
                        self.list_voices()
                    
                    elif cmd[0] == 'voice' and len(cmd) > 1:
                        self.switch_voice(cmd[1])
                    
                    elif cmd[0] == 'help':
                        print("\n💡 Commands:")
                        print("   :voice <name> - Switch voice")
                        print("   :list - List voices")
                        print("   :quit - Exit")
                        print()
                    
                    else:
                        print(f"❌ Unknown command: {cmd[0]}")
                        print("   Type ':help' for help\n")
                    
                    continue
                
                # Generate speech
                self.generate(text, auto_play=True)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    def run_single(self, text):
        """Run single generation (for command line usage)"""
        gen_time = self.generate(text, auto_play=True)
        return gen_time


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Interactive TTS - Load once, generate forever!',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  python interactive_tts.py
  
  # Single generation
  python interactive_tts.py --text "Hello world"
  
  # Choose voice
  python interactive_tts.py --text "Hello" --voice jo
  
  # No auto-play
  python interactive_tts.py --text "Hello" --no-play
        """
    )
    
    parser.add_argument(
        '--text', '-t',
        type=str,
        help='Text to generate (if not provided, runs in interactive mode)'
    )
    parser.add_argument(
        '--voice', '-v',
        type=str,
        default='dave',
        help='Voice to use (default: dave)'
    )
    parser.add_argument(
        '--no-play',
        action='store_true',
        help='Do not auto-play generated audio'
    )
    
    args = parser.parse_args()
    
    # Initialize TTS
    tts_engine = InteractiveTTS()
    tts_engine.initialize()
    
    # Set voice if specified
    if args.voice and args.voice in tts_engine.voices:
        tts_engine.switch_voice(args.voice)
    
    # Single generation or interactive mode
    if args.text:
        # Single mode
        tts_engine.generate(args.text, auto_play=not args.no_play)
    else:
        # Interactive mode
        tts_engine.run_interactive()


if __name__ == "__main__":
    main()

