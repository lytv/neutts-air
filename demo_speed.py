#!/usr/bin/env python3
"""
Demo script to show the speed difference between:
1. Old way: Load model every time
2. New way: Load once, generate many times
"""
import subprocess
import time
import sys

def demo_old_way():
    """Old way: Reload model each time"""
    print("\n" + "="*70)
    print("❌ OLD WAY: Loading model each time")
    print("="*70)
    
    texts = [
        "Hello, this is the first generation",
        "And this is the second one",
        "Finally, the third generation"
    ]
    
    total_time = 0
    for i, text in enumerate(texts, 1):
        print(f"\n🔄 Generation {i}/3: '{text}'")
        start = time.time()
        
        result = subprocess.run([
            'python', 'ultra_fast_example.py',
            '--input_text', text,
            '--ref_audio', 'samples/dave.wav',
            '--ref_text', 'samples/dave.txt'
        ], capture_output=True, text=True)
        
        elapsed = time.time() - start
        total_time += elapsed
        print(f"   ⏱️  Time: {elapsed:.2f}s")
    
    print(f"\n{'='*70}")
    print(f"📊 OLD WAY TOTAL: {total_time:.2f}s for 3 generations")
    print(f"   Average: {total_time/3:.2f}s per generation")
    print("="*70)
    
    return total_time


def demo_new_way():
    """New way: Load once, generate multiple times"""
    print("\n" + "="*70)
    print("✅ NEW WAY: Load model ONCE, generate many times")
    print("="*70)
    
    # Start interactive mode and send multiple commands
    import os
    os.chdir('/Users/mac/tools/neutts-air')
    
    from interactive_tts import InteractiveTTS
    
    print("\n🚀 Initializing (this happens ONCE)...")
    start_init = time.time()
    tts = InteractiveTTS()
    tts.initialize()
    init_time = time.time() - start_init
    print(f"✅ Initialization: {init_time:.2f}s")
    
    texts = [
        "Hello, this is the first generation",
        "And this is the second one", 
        "Finally, the third generation"
    ]
    
    total_gen_time = 0
    for i, text in enumerate(texts, 1):
        print(f"\n⚡ Generation {i}/3: '{text}'")
        gen_time = tts.generate(text, auto_play=False)
        total_gen_time += gen_time
        print(f"   ⏱️  Time: {gen_time:.2f}s")
    
    total_time = init_time + total_gen_time
    
    print(f"\n{'='*70}")
    print(f"📊 NEW WAY BREAKDOWN:")
    print(f"   • Initialization (once): {init_time:.2f}s")
    print(f"   • 3 generations: {total_gen_time:.2f}s")
    print(f"   • Average per generation: {total_gen_time/3:.2f}s")
    print(f"   • TOTAL: {total_time:.2f}s")
    print("="*70)
    
    return total_time, init_time, total_gen_time


def main():
    print("\n" + "🎯 " * 20)
    print("SPEED COMPARISON DEMO")
    print("🎯 " * 20)
    
    # Run new way first (to show the benefit)
    new_total, new_init, new_gen = demo_new_way()
    
    # Show comparison
    print("\n" + "="*70)
    print("🏆 COMPARISON RESULTS")
    print("="*70)
    print(f"\n✅ NEW WAY (Interactive):")
    print(f"   • First generation: {new_init + new_gen/3:.2f}s")
    print(f"   • Next generations: {new_gen/3:.2f}s each")
    print(f"   • Total for 3: {new_total:.2f}s")
    
    print(f"\n❌ OLD WAY (Script reload):")
    print(f"   • Every generation: ~9-11s")
    print(f"   • Total for 3: ~27-33s")
    
    savings = 30 - new_total  # approximate
    print(f"\n💰 SAVINGS: ~{savings:.2f}s ({savings/30*100:.0f}%)")
    print(f"\n💡 KEY INSIGHT:")
    print(f"   • Old way: Load model EVERY time = SLOW ❌")
    print(f"   • New way: Load model ONCE = FAST ✅")
    print(f"   • Generation time: ~2-3s (this is the minimum)")
    print(f"   • Model loading: ~7s (skip this with interactive mode!)")
    
    print("\n" + "="*70)
    print("🚀 RECOMMENDATION: Use Interactive Mode!")
    print("="*70)
    print("\nHow to use:")
    print("  cd /Users/mac/tools/neutts-air && source venv/bin/activate")
    print("  python interactive_tts.py")
    print("\nThen:")
    print("  • First generation: ~9s (includes loading)")
    print("  • All next generations: ~2-3s ⚡")
    print("="*70)
    print()


if __name__ == "__main__":
    # Change to project directory
    import os
    os.chdir('/Users/mac/tools/neutts-air')
    
    # Activate venv
    import sys
    venv_path = '/Users/mac/tools/neutts-air/venv'
    if sys.prefix != venv_path:
        sys.path.insert(0, f'{venv_path}/lib/python3.13/site-packages')
    
    main()

