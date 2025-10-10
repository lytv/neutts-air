#!/usr/bin/env python3
"""
TTS Hotkey Client - Listens for global hotkeys and communicates with TTS service

Hotkeys:
- Cmd+Shift+S: Read clipboard text
- Cmd+Shift+Q: Stop TTS service and exit
"""
import sys
import socket
import json
import subprocess
import logging
import time
from pynput import keyboard
import pyperclip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/tts_hotkey.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SOCKET_PATH = '/tmp/tts_service.sock'


class TTSHotkeyClient:
    def __init__(self):
        self.running = True
    
    def show_notification(self, title, message):
        """Show macOS notification"""
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         timeout=2)
        except Exception as e:
            logger.warning(f"Failed to show notification: {e}")
    
    def send_request(self, action, **kwargs):
        """Send request to TTS service"""
        try:
            # Create request
            request = {'action': action, **kwargs}
            request_str = json.dumps(request)
            
            # Connect to service
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(30.0)  # 30s timeout for generation
            client.connect(SOCKET_PATH)
            
            # Send request
            client.sendall(request_str.encode('utf-8'))
            client.shutdown(socket.SHUT_WR)
            
            # Receive response
            response_data = b''
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            client.close()
            
            # Parse response
            response = json.loads(response_data.decode('utf-8'))
            return response
            
        except FileNotFoundError:
            logger.error("Service not running!")
            return {"status": "error", "message": "Service not running"}
        except socket.timeout:
            logger.error("Request timeout")
            return {"status": "error", "message": "Request timeout"}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def on_speak_hotkey(self):
        """Handle Cmd+Shift+S - Read clipboard"""
        logger.info("🎤 Speak hotkey pressed")
        
        try:
            # Get clipboard text
            text = pyperclip.paste()
            
            if not text or not text.strip():
                logger.warning("Empty clipboard")
                self.show_notification("TTS", "Clipboard is empty")
                return
            
            logger.info(f"📋 Clipboard: '{text[:50]}...'")
            
            # Show start notification
            self.show_notification("TTS", "Reading text...")
            
            # Send to service
            start_time = time.time()
            response = self.send_request('speak', text=text)
            total_time = time.time() - start_time
            
            if response.get('status') == 'success':
                gen_time = response.get('time', 0)
                logger.info(f"✅ Success! Generated in {gen_time}s")
                self.show_notification("TTS", f"Done! ({gen_time}s)")
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"❌ Error: {error_msg}")
                self.show_notification("TTS Error", error_msg)
                
        except Exception as e:
            logger.error(f"Hotkey handler error: {e}")
            self.show_notification("TTS Error", str(e))
    
    def on_quit_hotkey(self):
        """Handle Cmd+Shift+Q - Stop service and exit"""
        logger.info("🛑 Quit hotkey pressed")
        
        try:
            # Send stop signal to service
            response = self.send_request('stop')
            
            if response.get('status') == 'success':
                logger.info("✅ Service stopped")
                self.show_notification("TTS", "Service stopped")
            else:
                logger.warning("Service may already be stopped")
                self.show_notification("TTS", "Service stopped")
            
            # Exit
            self.running = False
            
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            self.show_notification("TTS", "Service stopped")
            self.running = False
    
    def start(self):
        """Start listening for hotkeys"""
        logger.info("=" * 60)
        logger.info("⌨️  TTS Hotkey Client Starting")
        logger.info("=" * 60)
        logger.info("Hotkeys:")
        logger.info("  • Cmd+Shift+S: Read clipboard text")
        logger.info("  • Cmd+Shift+Q: Stop service and exit")
        logger.info("=" * 60)
        
        # Check if service is running
        response = self.send_request('ping')
        if response.get('status') != 'success':
            logger.error("❌ TTS service is not running!")
            logger.error("   Please start it first with: ./tts-start.sh")
            sys.exit(1)
        
        logger.info("✅ Connected to TTS service")
        logger.info("🎧 Listening for hotkeys...\n")
        
        # Show startup notification
        self.show_notification("TTS Ready", "Cmd+Shift+S to speak, Cmd+Shift+Q to quit")
        
        # Setup hotkeys
        hotkeys = {
            '<cmd>+<shift>+s': self.on_speak_hotkey,
            '<cmd>+<shift>+q': self.on_quit_hotkey,
        }
        
        # Start listening
        try:
            with keyboard.GlobalHotKeys(hotkeys) as listener:
                while self.running:
                    time.sleep(0.1)
                listener.stop()
        except Exception as e:
            logger.error(f"Hotkey listener error: {e}")
            sys.exit(1)
        
        logger.info("👋 Hotkey client stopped")


def main():
    client = TTSHotkeyClient()
    try:
        client.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()

