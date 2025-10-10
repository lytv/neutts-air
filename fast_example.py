"""
Fast TTS Example - Optimized for speed on Apple Silicon
Uses Q4 GGUF quantized model for 3-4x faster inference
"""
import os
import soundfile as sf
from neuttsair.neutts import NeuTTSAir
import time


def main(input_text, ref_audio_path, ref_text, output_path="output.wav"):
    print("⚡ Fast TTS Mode - Using optimized settings")
    print(f"🎯 Target text: {input_text}\n")
    
    start_time = time.time()
    
    # Initialize with Q4 GGUF model (much faster!)
    print("📦 Loading Q4 GGUF model (this is much faster than full PyTorch)...")
    tts = NeuTTSAir(
        backbone_repo="neuphonic/neutts-air-q4-gguf",  # Quantized model
        backbone_device="cpu",  # GGUF works best on CPU
        codec_repo="neuphonic/neucodec",
        codec_device="cpu"
    )
    
    load_time = time.time() - start_time
    print(f"✅ Model loaded in {load_time:.2f}s\n")
    
    # Read reference text
    if ref_text and os.path.exists(ref_text):
        with open(ref_text, "r") as f:
            ref_text = f.read().strip()
    
    # Encode reference audio
    print("🎤 Encoding reference audio...")
    encode_start = time.time()
    ref_codes = tts.encode_reference(ref_audio_path)
    encode_time = time.time() - encode_start
    print(f"✅ Reference encoded in {encode_time:.2f}s\n")
    
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
    print(f"   - Reference encoding: {encode_time:.2f}s")
    print(f"   - Audio generation: {gen_time:.2f}s")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fast NeuTTSAir Example")
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
    args = parser.parse_args()
    
    main(
        input_text=args.input_text,
        ref_audio_path=args.ref_audio,
        ref_text=args.ref_text,
        output_path=args.output_path,
    )

