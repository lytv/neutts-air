#!/usr/bin/env python3
"""
TTS Background Service - Keeps models loaded in memory for instant inference
Listens on Unix socket for requests from hotkey client
"""
import os
import sys
import socket
import json
import time
import logging
from pathlib import Path
import soundfile as sf
import torch
from neuttsair.neutts import NeuTTSAir
from threading import Thread
import subprocess
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/tts_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SOCKET_PATH = '/tmp/tts_service.sock'
MAX_TEXT_LENGTH = 500  # characters (~2048 tokens limit)


class TTSService:
    def __init__(self):
        self.tts = None
        self.voices = {}
        self.current_voice = 'dave'
        self.output_path = '/tmp/tts_output.wav'
        self.running = True
        self.audio_thread = None
        
    def initialize(self):
        """Load TTS models into memory"""
        logger.info("=" * 60)
        logger.info("🔥 TTS Background Service Starting")
        logger.info("=" * 60)
        
        try:
            logger.info("📦 Loading models (this takes ~7-10 seconds)...")
            start = time.time()
            
            # Choose codec based on ONNX availability
            codec_repo = "neuphonic/neucodec"
            try:
                import onnxruntime
                codec_repo = "neuphonic/neucodec-onnx-decoder"
                logger.info("   ✓ Using ONNX decoder for faster performance")
            except ImportError:
                logger.info("   ⚠️  Using PyTorch decoder (ONNX not installed)")
            
            self.tts = NeuTTSAir(
                backbone_repo="neuphonic/neutts-air-q4-gguf",
                backbone_device="cpu",
                codec_repo=codec_repo,
                codec_device="cpu"
            )
            
            load_time = time.time() - start
            logger.info(f"✅ Models loaded in {load_time:.2f}s")
            logger.info("💡 Service ready! Models in memory.\n")
            
            # Load pre-encoded voices
            self._load_voices()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize TTS: {e}")
            return False
    
    def _load_voices(self):
        """Load pre-encoded voice references"""
        logger.info("🎤 Loading voices...")
        samples_dir = Path("samples")
        
        for pt_file in samples_dir.glob("*.pt"):
            voice_name = pt_file.stem
            txt_file = pt_file.with_suffix(".txt")
            
            if txt_file.exists():
                try:
                    ref_codes = torch.load(pt_file, weights_only=True)
                    ref_text = txt_file.read_text().strip()
                    self.voices[voice_name] = {
                        'codes': ref_codes,
                        'text': ref_text
                    }
                    logger.info(f"   ✓ {voice_name}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Failed to load {voice_name}: {e}")
        
        if not self.voices:
            logger.error("❌ No voices loaded!")
            return False
        
        logger.info(f"\n🎯 Default voice: {self.current_voice}\n")
        return True
    
    def _play_audio_async(self, file_path):
        """Play audio in background thread"""
        def play():
            try:
                subprocess.run(['afplay', file_path], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            except Exception as e:
                logger.error(f"Failed to play audio: {e}")
        
        # Wait for previous playback to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()
        
        self.audio_thread = Thread(target=play, daemon=True)
        self.audio_thread.start()
    
    def generate_speech(self, text):
        """Generate speech from text"""
        if not text or not text.strip():
            return {"status": "error", "message": "Empty text"}
        
        # Truncate if too long
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
            logger.warning(f"Text truncated to {MAX_TEXT_LENGTH} characters")
        
        try:
            logger.info(f"🎵 Generating: '{text[:50]}...'")
            start = time.time()
            
            voice = self.voices[self.current_voice]
            wav = self.tts.infer(text, voice['codes'], voice['text'])
            
            gen_time = time.time() - start
            
            # Save
            sf.write(self.output_path, wav, 24000)
            
            # Play asynchronously
            self._play_audio_async(self.output_path)
            
            logger.info(f"⚡ Generated in {gen_time:.2f}s")
            
            return {
                "status": "success",
                "time": round(gen_time, 2),
                "message": f"Generated in {gen_time:.2f}s"
            }
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def replay_audio(self):
        """Replay the last generated audio file"""
        import os
        
        if not os.path.exists(self.output_path):
            logger.warning("No audio file to replay")
            return {"status": "error", "message": "No audio file found to replay"}
        
        try:
            logger.info("🔁 Replaying last audio...")
            self._play_audio_async(self.output_path)
            return {"status": "success", "message": "Replaying audio"}
        except Exception as e:
            logger.error(f"❌ Replay failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def switch_voice(self, voice_name):
        """Switch to another voice"""
        if voice_name in self.voices:
            self.current_voice = voice_name
            logger.info(f"✅ Switched to voice: {voice_name}")
            return {"status": "success", "message": f"Switched to {voice_name}"}
        else:
            return {"status": "error", "message": f"Voice '{voice_name}' not found"}
    
    def handle_request(self, request):
        """Handle incoming request"""
        try:
            data = json.loads(request)
            action = data.get('action')
            
            if action == 'speak':
                text = data.get('text', '')
                return self.generate_speech(text)
            
            elif action == 'replay':
                return self.replay_audio()
            
            elif action == 'switch_voice':
                voice = data.get('voice', 'dave')
                return self.switch_voice(voice)
            
            elif action == 'stop':
                logger.info("🛑 Stop signal received")
                self.running = False
                return {"status": "success", "message": "Service stopping"}
            
            elif action == 'ping':
                return {"status": "success", "message": "Service is running"}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def start_server(self):
        """Start Unix socket server"""
        # Remove old socket if exists
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        
        # Create socket
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(SOCKET_PATH)
        server.listen(1)
        server.settimeout(1.0)  # Timeout to allow checking self.running
        
        logger.info(f"🚀 Server listening on {SOCKET_PATH}")
        logger.info("💡 Ready to receive hotkey commands!\n")
        logger.info("=" * 60)
        
        try:
            while self.running:
                try:
                    conn, _ = server.accept()
                    
                    # Receive data
                    data = b''
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                    
                    if data:
                        request = data.decode('utf-8')
                        logger.info(f"📨 Request: {request[:100]}")
                        
                        # Handle request
                        response = self.handle_request(request)
                        
                        # Send response
                        conn.sendall(json.dumps(response).encode('utf-8'))
                    
                    conn.close()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error handling connection: {e}")
                    
        finally:
            server.close()
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)
            logger.info("🛑 Server stopped")
    
    def stop(self):
        """Stop the service"""
        logger.info("🛑 Shutting down service...")
        self.running = False


def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    # Change to project directory
    os.chdir('/Users/mac/tools/neutts-air')
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start service
    service = TTSService()
    
    if not service.initialize():
        logger.error("Failed to initialize service")
        sys.exit(1)
    
    try:
        service.start_server()
    except Exception as e:
        logger.error(f"Service crashed: {e}")
        sys.exit(1)
    finally:
        service.stop()


if __name__ == "__main__":
    main()

