"""
Ultra Fast TTS Example - Pre-encoded references
This script pre-encodes and saves reference voices to .pt files
Then reuses them for instant inference without re-encoding
"""
import os
import soundfile as sf
import torch
from neuttsair.neutts import NeuTTSAir
import time
from pathlib import Path


def encode_and_save_reference(tts, ref_audio_path, save_path):
    """Pre-encode reference audio and save to disk"""
    print(f"🎤 Encoding reference: {ref_audio_path}")
    ref_codes = tts.encode_reference(ref_audio_path)
    torch.save(ref_codes, save_path)
    print(f"💾 Saved encoded reference to: {save_path}\n")
    return ref_codes


def load_reference(ref_codes_path):
    """Load pre-encoded reference"""
    print(f"⚡ Loading pre-encoded reference: {ref_codes_path}")
    ref_codes = torch.load(ref_codes_path)
    print(f"✅ Loaded instantly!\n")
    return ref_codes


def main(input_text, ref_audio_path, ref_text, output_path="output.wav", use_cached=True):
    print("🚀 Ultra Fast TTS Mode - Pre-encoded references")
    print(f"🎯 Target text: {input_text}\n")
    
    start_time = time.time()
    
    # Initialize with Q4 GGUF model
    print("📦 Loading Q4 GGUF model...")
    tts = NeuTTSAir(
        backbone_repo="neuphonic/neutts-air-q4-gguf",
        backbone_device="cpu",
        codec_repo="neuphonic/neucodec",
        codec_device="cpu"
    )
    load_time = time.time() - start_time
    print(f"✅ Model loaded in {load_time:.2f}s\n")
    
    # Read reference text
    if ref_text and os.path.exists(ref_text):
        with open(ref_text, "r") as f:
            ref_text = f.read().strip()
    
    # Handle reference encoding (use cached or create new)
    ref_codes_path = Path(ref_audio_path).with_suffix('.pt')
    
    encode_start = time.time()
    if use_cached and ref_codes_path.exists():
        ref_codes = load_reference(ref_codes_path)
    else:
        ref_codes = encode_and_save_reference(tts, ref_audio_path, ref_codes_path)
    encode_time = time.time() - encode_start
    
    # Generate audio
    print(f"🎵 Generating audio...")
    gen_start = time.time()
    wav = tts.infer(input_text, ref_codes, ref_text)
    gen_time = time.time() - gen_start
    print(f"✅ Audio generated in {gen_time:.2f}s\n")
    
    # Save output
    sf.write(output_path, wav, 24000)
    
    total_time = time.time() - start_time
    print(f"💾 Saved to: {output_path}")
    print(f"\n⏱️  Total time: {total_time:.2f}s")
    print(f"   - Model loading: {load_time:.2f}s")
    print(f"   - Reference handling: {encode_time:.2f}s")
    print(f"   - Audio generation: {gen_time:.2f}s")
    
    if not use_cached or not ref_codes_path.exists():
        print(f"\n💡 Tip: Next time will be faster! Pre-encoded reference saved to {ref_codes_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ultra Fast NeuTTSAir with Pre-encoded References")
    parser.add_argument(
        "--input_text", 
        type=str, 
        required=True, 
        help="Input text to be converted to speech"
    )
    parser.add_argument(
        "--ref_audio", 
        type=str, 
        default="./samples/dave.wav", 
        help="Path to reference audio file"
    )
    parser.add_argument(
        "--ref_text",
        type=str,
        default="./samples/dave.txt", 
        help="Reference text corresponding to the reference audio",
    )
    parser.add_argument(
        "--output_path", 
        type=str, 
        default="output.wav", 
        help="Path to save the output audio"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached encoded references, re-encode from scratch"
    )
    args = parser.parse_args()
    
    main(
        input_text=args.input_text,
        ref_audio_path=args.ref_audio,
        ref_text=args.ref_text,
        output_path=args.output_path,
        use_cached=not args.no_cache,
    )

