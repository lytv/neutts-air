#!/usr/bin/env python3
"""
Compare PyTorch decoder vs ONNX decoder
"""
import time
import torch
from neuttsair.neutts import NeuTTSAir

def benchmark_decoder(use_onnx, num_runs=5):
    """Benchmark a specific decoder"""
    codec_repo = "neuphonic/neucodec-onnx-decoder" if use_onnx else "neuphonic/neucodec"
    decoder_name = "ONNX" if use_onnx else "PyTorch"
    
    print(f"\n{'='*60}")
    print(f"Testing {decoder_name} Decoder")
    print(f"{'='*60}\n")
    
    # Initialize
    print("Loading...")
    tts = NeuTTSAir(
        backbone_repo="neuphonic/neutts-air-q4-gguf",
        backbone_device="cpu",
        codec_repo=codec_repo,
        codec_device="cpu"
    )
    
    # Load reference
    ref_codes = torch.load("samples/dave.pt", weights_only=True)
    ref_text = open("samples/dave.txt").read().strip()
    
    # Test texts of different lengths
    texts = [
        "Hello",
        "Hello world",
        "This is a longer test sentence",
        "And this is an even longer test sentence with more words",
        "Super long sentence for testing performance with lots of text"
    ]
    
    print(f"Running {num_runs} generations...\n")
    
    results = []
    for i, text in enumerate(texts[:num_runs], 1):
        start = time.time()
        wav = tts.infer(text, ref_codes, ref_text)
        elapsed = time.time() - start
        results.append(elapsed)
        print(f"  {i}. {elapsed:.3f}s - '{text[:30]}...'")
    
    avg = sum(results) / len(results)
    print(f"\n📊 Average: {avg:.3f}s")
    
    return avg, results


def main():
    import os
    os.chdir('/Users/mac/tools/neutts-air')
    
    print("\n" + "🏁 "*20)
    print("DECODER COMPARISON BENCHMARK")
    print("🏁 "*20)
    
    # Test PyTorch
    pytorch_avg, pytorch_times = benchmark_decoder(use_onnx=False, num_runs=5)
    
    # Test ONNX
    onnx_avg, onnx_times = benchmark_decoder(use_onnx=True, num_runs=5)
    
    # Compare
    print(f"\n{'='*60}")
    print("🏆 RESULTS")
    print(f"{'='*60}")
    print(f"\nPyTorch Decoder: {pytorch_avg:.3f}s")
    print(f"ONNX Decoder:    {onnx_avg:.3f}s")
    print(f"\nDifference:      {pytorch_avg - onnx_avg:.3f}s")
    print(f"Speedup:         {pytorch_avg/onnx_avg:.2f}x")
    
    savings_pct = (pytorch_avg - onnx_avg) / pytorch_avg * 100
    print(f"Savings:         {savings_pct:.1f}%")
    
    if onnx_avg < pytorch_avg:
        print(f"\n✅ ONNX is FASTER!")
        print(f"   Save ~{pytorch_avg - onnx_avg:.2f}s per generation")
        print(f"   For 20 gens/day: {(pytorch_avg - onnx_avg)*20:.1f}s/day savings")
    elif onnx_avg > pytorch_avg:
        print(f"\n⚠️  ONNX is SLOWER (unexpected)")
        print(f"   Stick with PyTorch decoder")
    else:
        print(f"\n➡️  Similar performance")
    
    print(f"\n{'='*60}")
    print("💡 RECOMMENDATION:")
    print(f"{'='*60}")
    if onnx_avg < pytorch_avg * 0.95:
        print("✅ Use ONNX decoder for best performance!")
        print("   Add --onnx flag when running blazing_fast_tts.py")
    else:
        print("➡️  PyTorch decoder is fine (minimal difference)")
        print("   ONNX not worth the extra dependency")
    print()


if __name__ == "__main__":
    main()

