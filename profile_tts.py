#!/usr/bin/env python3
"""
Profile TTS to find bottlenecks
"""
import time
import torch
from neuttsair.neutts import NeuTTSAir
import soundfile as sf

def profile_generation():
    print("🔍 Profiling TTS Generation to find bottlenecks...\n")
    print("="*70)
    
    # Initialize
    print("📦 Initializing...")
    start = time.time()
    tts = NeuTTSAir(
        backbone_repo="neuphonic/neutts-air-q4-gguf",
        backbone_device="cpu",
        codec_repo="neuphonic/neucodec",
        codec_device="cpu"
    )
    init_time = time.time() - start
    print(f"✅ Init: {init_time:.3f}s\n")
    
    # Load reference
    print("🎤 Loading reference...")
    start = time.time()
    ref_codes = torch.load("samples/dave.pt")
    ref_text = open("samples/dave.txt").read().strip()
    load_ref_time = time.time() - start
    print(f"✅ Load ref: {load_ref_time:.3f}s\n")
    
    # Test text
    input_text = "Hello world, this is a test of the optimized model"
    
    # Profile each step
    print(f"📝 Input text: '{input_text}'")
    print(f"   Length: {len(input_text)} chars, {len(input_text.split())} words\n")
    print("="*70)
    print("PROFILING GENERATION:\n")
    
    # Step 1: Phonemization
    print("1️⃣  Phonemizing text...")
    start = time.time()
    ref_phones = tts._to_phones(ref_text)
    input_phones = tts._to_phones(input_text)
    phoneme_time = time.time() - start
    print(f"   ⏱️  {phoneme_time:.3f}s")
    print(f"   📊 Phones: {len(input_phones.split())} phonemes")
    
    # Step 2: Model inference
    print("\n2️⃣  Running model inference...")
    start = time.time()
    
    if tts._is_quantized_model:
        codes_str = "".join([f"<|speech_{idx}|>" for idx in ref_codes])
        prompt = (
            f"user: Convert the text to speech:<|TEXT_PROMPT_START|>{ref_phones} {input_phones}"
            f"<|TEXT_PROMPT_END|>\nassistant:<|SPEECH_GENERATION_START|>{codes_str}"
        )
        output = tts.backbone(
            prompt,
            max_tokens=tts.max_context,
            temperature=1.0,
            top_k=50,
            stop=["<|SPEECH_GENERATION_END|>"],
        )
        output_str = output["choices"][0]["text"]
    
    inference_time = time.time() - start
    print(f"   ⏱️  {inference_time:.3f}s")
    
    # Count tokens
    import re
    speech_ids = [int(num) for num in re.findall(r"<\|speech_(\d+)\|>", output_str)]
    print(f"   📊 Generated: {len(speech_ids)} audio tokens")
    print(f"   📊 Speed: {len(speech_ids)/inference_time:.1f} tokens/sec")
    
    # Step 3: Audio decoding
    print("\n3️⃣  Decoding audio...")
    start = time.time()
    wav = tts._decode(output_str)
    decode_time = time.time() - start
    print(f"   ⏱️  {decode_time:.3f}s")
    print(f"   📊 Audio length: {len(wav)/24000:.2f}s")
    
    # Step 4: Watermarking
    print("\n4️⃣  Applying watermark...")
    start = time.time()
    watermarked_wav = tts.watermarker.apply_watermark(wav, sample_rate=24_000)
    watermark_time = time.time() - start
    print(f"   ⏱️  {watermark_time:.3f}s")
    
    # Step 5: Saving
    print("\n5️⃣  Saving to file...")
    start = time.time()
    sf.write("output.wav", watermarked_wav, 24000)
    save_time = time.time() - start
    print(f"   ⏱️  {save_time:.3f}s")
    
    # Summary
    total_time = phoneme_time + inference_time + decode_time + watermark_time + save_time
    
    print("\n" + "="*70)
    print("📊 BREAKDOWN:")
    print("="*70)
    print(f"1. Phonemization:  {phoneme_time:6.3f}s ({phoneme_time/total_time*100:5.1f}%)")
    print(f"2. Model inference: {inference_time:6.3f}s ({inference_time/total_time*100:5.1f}%) ← BIGGEST")
    print(f"3. Audio decoding:  {decode_time:6.3f}s ({decode_time/total_time*100:5.1f}%)")
    print(f"4. Watermarking:    {watermark_time:6.3f}s ({watermark_time/total_time*100:5.1f}%)")
    print(f"5. File saving:     {save_time:6.3f}s ({save_time/total_time*100:5.1f}%)")
    print("-"*70)
    print(f"TOTAL:              {total_time:6.3f}s")
    print("="*70)
    
    # Recommendations
    print("\n💡 OPTIMIZATION OPPORTUNITIES:\n")
    
    if inference_time/total_time > 0.6:
        print(f"⚠️  Model inference takes {inference_time/total_time*100:.0f}% of time!")
        print("   → Cannot optimize much (already using Q4 GGUF)")
        print("   → This is the physical limit on M1 CPU")
        print("   → Need GPU/NPU for faster inference\n")
    
    if decode_time/total_time > 0.15:
        print(f"💡 Audio decoding takes {decode_time/total_time*100:.0f}% of time")
        print("   → Try ONNX decoder: pip install onnxruntime")
        print("   → Could save ~0.2-0.5s (10-20% faster)")
        print("   → codec_repo='neuphonic/neucodec-onnx-decoder'\n")
    
    if phoneme_time/total_time > 0.05:
        print(f"💡 Phonemization takes {phoneme_time/total_time*100:.0f}% of time")
        print("   → Could cache common phrases")
        print("   → Could save ~0.1-0.2s\n")
    
    if watermark_time/total_time > 0.05:
        print(f"💡 Watermarking takes {watermark_time/total_time*100:.0f}% of time")
        print("   → Cannot skip (required by model)")
        print("   → Already optimized\n")
    
    # Calculate theoretical minimum
    theoretical_min = total_time - phoneme_time - watermark_time - save_time
    print("="*70)
    print("🎯 THEORETICAL LIMITS:")
    print("="*70)
    print(f"Current total:       {total_time:.3f}s")
    print(f"With ONNX decoder:   ~{total_time - decode_time*0.5:.3f}s (realistic)")
    print(f"With caching:        ~{total_time - phoneme_time*0.5:.3f}s (marginal)")
    print(f"Absolute minimum:    ~{inference_time:.3f}s (inference only, impossible)")
    print("="*70)
    
    return {
        'phoneme': phoneme_time,
        'inference': inference_time,
        'decode': decode_time,
        'watermark': watermark_time,
        'save': save_time,
        'total': total_time
    }


if __name__ == "__main__":
    import os
    os.chdir('/Users/mac/tools/neutts-air')
    
    profile_generation()

