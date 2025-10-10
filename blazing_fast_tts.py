#!/usr/bin/env python3
"""
Blazing Fast TTS - Mọi tối ưu có thể!

Optimizations applied:
1. Interactive mode (no reload)
2. GGUF Q4 quantized model
3. Pre-encoded references  
4. ONNX decoder option (faster decoding)
5. Async audio playback (parallel)
6. Minimal overhead
"""
import os
import soundfile as sf
import torch
from neuttsair.neutts import NeuTTSAir
import time
from pathlib import Path
import subprocess
import sys
from threading import Thread


class BlazingFastTTS:
    def __init__(self, use_onnx_decoder=False):
        self.tts = None
        self.voices = {}
        self.current_voice = None
        self.output_path = "output.wav"
        self.use_onnx = use_onnx_decoder
        self.audio_thread = None
        
    def initialize(self):
        """Load model optimally"""
        print("=" * 60)
        print("🔥 BLAZING FAST TTS - Maximum Optimization")
        print("=" * 60)
        
        if self.use_onnx:
            print("\n🚀 Using ONNX decoder for faster audio decoding!")
            print("   (This could save 0.1-0.2s per generation)\n")
        
        print("📦 Loading models (once only)...")
        start = time.time()
        
        # Choose codec based on ONNX availability
        codec_repo = "neuphonic/neucodec"
        if self.use_onnx:
            try:
                import onnxruntime
                codec_repo = "neuphonic/neucodec-onnx-decoder"
                print("   ✓ ONNX runtime detected")
            except ImportError:
                print("   ⚠️  onnxruntime not installed, using PyTorch decoder")
                print("   💡 Install with: pip install onnxruntime")
                self.use_onnx = False
        
        self.tts = NeuTTSAir(
            backbone_repo="neuphonic/neutts-air-q4-gguf",
            backbone_device="cpu",
            codec_repo=codec_repo,
            codec_device="cpu"
        )
        
        load_time = time.time() - start
        print(f"✅ Models loaded in {load_time:.2f}s")
        print("💡 Now in memory. Generations will be blazing fast!\n")
        
        self._scan_voices()
        
    def _scan_voices(self):
        """Load pre-encoded voices"""
        print("🎤 Loading voices...")
        samples_dir = Path("samples")
        
        for pt_file in samples_dir.glob("*.pt"):
            voice_name = pt_file.stem
            txt_file = pt_file.with_suffix(".txt")
            
            if txt_file.exists():
                ref_codes = torch.load(pt_file, weights_only=True)
                ref_text = txt_file.read_text().strip()
                self.voices[voice_name] = {
                    'codes': ref_codes,
                    'text': ref_text
                }
                print(f"   ✓ {voice_name}")
        
        self.current_voice = 'dave' if 'dave' in self.voices else list(self.voices.keys())[0]
        print(f"\n🎯 Current voice: {self.current_voice}\n")
    
    def _play_audio_async(self, file_path):
        """Play audio in background thread"""
        def play():
            subprocess.run(['afplay', file_path], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        # Wait for previous playback to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()
        
        self.audio_thread = Thread(target=play, daemon=True)
        self.audio_thread.start()
    
    def generate(self, text, auto_play=True, verbose=True):
        """Generate speech with minimal overhead"""
        if not text.strip():
            return None
        
        if verbose:
            print(f"🎵 [{self.current_voice}] {text}")
        
        start = time.time()
        
        voice = self.voices[self.current_voice]
        wav = self.tts.infer(text, voice['codes'], voice['text'])
        
        gen_time = time.time() - start
        
        # Save
        sf.write(self.output_path, wav, 24000)
        
        if verbose:
            print(f"⚡ {gen_time:.2f}s", end="")
        
        # Play asynchronously
        if auto_play:
            if verbose:
                print(" 🔊", end="")
            self._play_audio_async(self.output_path)
        
        if verbose:
            print()
        
        return gen_time
    
    def switch_voice(self, voice_name):
        """Switch voice"""
        if voice_name in self.voices:
            self.current_voice = voice_name
            print(f"✅ Voice: {voice_name}\n")
        else:
            print(f"❌ Unknown voice: {voice_name}")
            self.list_voices()
    
    def list_voices(self):
        """List voices"""
        print("\n🎤 Voices:")
        for name in self.voices.keys():
            marker = "→" if name == self.current_voice else " "
            print(f"  {marker} {name}")
        print()
    
    def run_interactive(self):
        """Interactive mode with minimal UI"""
        print("💡 Commands:")
        print("   • Text → Generate")
        print("   • :v <name> → Switch voice")
        print("   • :l → List voices")
        print("   • :q → Quit\n")
        
        generation_times = []
        
        while True:
            try:
                text = input(f"[{self.current_voice}] ").strip()
                
                if not text:
                    continue
                
                # Quick commands
                if text.startswith(':'):
                    cmd = text[1:].lower().split()
                    
                    if cmd[0] in ['q', 'quit']:
                        break
                    elif cmd[0] in ['l', 'list']:
                        self.list_voices()
                    elif cmd[0] in ['v', 'voice'] and len(cmd) > 1:
                        self.switch_voice(cmd[1])
                    elif cmd[0] == 's':  # stats
                        if generation_times:
                            avg = sum(generation_times) / len(generation_times)
                            print(f"📊 {len(generation_times)} gens, avg {avg:.2f}s\n")
                    else:
                        print(f"? {cmd[0]}\n")
                    continue
                
                # Generate
                gen_time = self.generate(text, auto_play=True, verbose=True)
                if gen_time:
                    generation_times.append(gen_time)
                
            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"❌ {e}\n")
        
        # Summary
        if generation_times:
            avg = sum(generation_times) / len(generation_times)
            print(f"\n📊 Summary: {len(generation_times)} generations, avg {avg:.2f}s")
        
        print("👋\n")
    
    def benchmark(self, num_runs=5):
        """Benchmark speed"""
        print(f"🏁 Benchmark: {num_runs} generations\n")
        
        test_texts = [
            "Hello world",
            "This is a test",
            "How fast can we go",
            "Blazing fast performance",
            "Optimized to the max"
        ]
        
        times = []
        for i in range(num_runs):
            text = test_texts[i % len(test_texts)]
            gen_time = self.generate(text, auto_play=False, verbose=False)
            times.append(gen_time)
            print(f"  Run {i+1}: {gen_time:.3f}s")
        
        avg = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Results:")
        print(f"   Average: {avg:.3f}s")
        print(f"   Best:    {min_time:.3f}s")
        print(f"   Worst:   {max_time:.3f}s")
        print(f"\n🎯 Theoretical limit: ~2.0-2.5s (model inference)")
        print(f"   Your speed: {avg:.3f}s")
        
        if avg < 2.5:
            print(f"   🏆 EXCELLENT! You're at the hardware limit!")
        elif avg < 3.0:
            print(f"   ✅ VERY GOOD! Close to optimal.")
        else:
            print(f"   💡 Room for improvement. Try ONNX decoder.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Blazing Fast TTS - Maximum optimization!',
    )
    
    parser.add_argument('--text', '-t', type=str, help='Text to generate')
    parser.add_argument('--voice', '-v', type=str, default='dave', help='Voice')
    parser.add_argument('--onnx', action='store_true', help='Use ONNX decoder (faster)')
    parser.add_argument('--benchmark', '-b', action='store_true', help='Run benchmark')
    parser.add_argument('--no-play', action='store_true', help='No audio playback')
    
    args = parser.parse_args()
    
    # Initialize
    engine = BlazingFastTTS(use_onnx_decoder=args.onnx)
    engine.initialize()
    
    # Set voice
    if args.voice in engine.voices:
        engine.switch_voice(args.voice)
    
    # Mode
    if args.benchmark:
        engine.benchmark()
    elif args.text:
        engine.generate(args.text, auto_play=not args.no_play)
    else:
        engine.run_interactive()


if __name__ == "__main__":
    main()

