#!/usr/bin/env python3
"""
TTS Hotkey Client - Listens for global hotkeys and communicates with TTS service

Hotkeys:
- Control+Right Arrow: Read clipboard text
- Control+Left Arrow: Replay last generated audio
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

SPEAK_HOTKEY_BINDING = '<ctrl>+<right>'
SPEAK_HOTKEY_DISPLAY = 'Control+Right Arrow'
REPLAY_HOTKEY_BINDING = '<ctrl>+<left>'
REPLAY_HOTKEY_DISPLAY = 'Control+Left Arrow'
QUIT_HOTKEY_BINDING = '<cmd>+<shift>+q'
QUIT_HOTKEY_DISPLAY = 'Cmd+Shift+Q'

SOCKET_PATH = '/tmp/tts_service.sock'


class TTSHotkeyClient:
    def __init__(self):
        self.running = True
        self.last_service_check = 0
        self.service_check_interval = 30  # Check service health every 30 seconds
        self.connection_retries = 3
        self.retry_delay = 1.0
    
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
    
    def check_service_health(self):
        """Check if service is still running and accessible"""
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(2.0)
            client.connect(SOCKET_PATH)
            client.close()
            return True
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            return False
    
    def send_request(self, action, **kwargs):
        """Send request to TTS service with retry logic"""
        last_error = None
        
        for attempt in range(self.connection_retries):
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
                error_msg = "Service socket not found - service may have stopped"
                last_error = error_msg
                if attempt < self.connection_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {error_msg}. Retrying...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"❌ {error_msg}")
                    return {"status": "error", "message": "Service not running - please restart with 'tts-start'"}
                    
            except ConnectionRefusedError:
                error_msg = "Service connection refused - service may have crashed"
                last_error = error_msg
                if attempt < self.connection_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {error_msg}. Retrying...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"❌ {error_msg}")
                    return {"status": "error", "message": "Service connection refused - please restart with 'tts-start'"}
                    
            except socket.timeout:
                error_msg = "Request timeout"
                last_error = error_msg
                if attempt < self.connection_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {error_msg}. Retrying...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"❌ {error_msg}")
                    return {"status": "error", "message": "Request timeout - service may be unresponsive"}
                    
            except OSError as e:
                error_msg = f"Connection error: {e}"
                last_error = error_msg
                if attempt < self.connection_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {error_msg}. Retrying...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"❌ {error_msg}")
                    return {"status": "error", "message": "Connection error - service may have stopped"}
                    
            except Exception as e:
                error_msg = f"Request failed: {e}"
                last_error = error_msg
                if attempt < self.connection_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {error_msg}. Retrying...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"❌ {error_msg}")
                    return {"status": "error", "message": str(e)}
        
        # If we get here, all retries failed
        return {"status": "error", "message": f"Failed after {self.connection_retries} attempts: {last_error}"}
    
    def on_speak_hotkey(self):
        """Handle Control+Right Arrow - Read clipboard"""
        logger.info("🎤 Speak hotkey pressed")
        
        # Quick health check before proceeding
        if not self.check_service_health():
            error_msg = "Service unavailable - restart with 'tts-start'"
            logger.error(f"❌ {error_msg}")
            self.show_notification("TTS Error", error_msg)
            return
        
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
                logger.info(
                    "✅ Success! Generated in %ss (total %.2fs)",
                    gen_time,
                    total_time
                )
                self.show_notification("TTS", f"Done! ({gen_time}s)")
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"❌ Error: {error_msg}")
                self.show_notification("TTS Error", error_msg)
                
        except Exception as e:
            logger.error(f"Hotkey handler error: {e}")
            self.show_notification("TTS Error", str(e))
    
    def on_replay_hotkey(self):
        """Handle Control+Left Arrow - Replay last audio"""
        logger.info("🔁 Replay hotkey pressed")
        
        # Quick health check before proceeding
        if not self.check_service_health():
            error_msg = "Service unavailable - restart with 'tts-start'"
            logger.error(f"❌ {error_msg}")
            self.show_notification("TTS Error", error_msg)
            return
        
        try:
            # Show notification
            self.show_notification("TTS", "Replaying...")
            
            # Send replay request to service
            response = self.send_request('replay')
            
            if response.get('status') == 'success':
                logger.info("✅ Replay started")
                self.show_notification("TTS", "Replaying audio")
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"❌ Replay error: {error_msg}")
                self.show_notification("TTS Error", error_msg)
                
        except Exception as e:
            logger.error(f"Replay hotkey handler error: {e}")
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
        logger.info("  • %s: Read clipboard text", SPEAK_HOTKEY_DISPLAY)
        logger.info("  • %s: Replay last audio", REPLAY_HOTKEY_DISPLAY)
        logger.info("  • %s: Stop service and exit", QUIT_HOTKEY_DISPLAY)
        logger.info("=" * 60)
        
        # Check if service is running
        response = self.send_request('ping')
        if response.get('status') != 'success':
            logger.error("❌ TTS service is not running!")
            logger.error("   Please start it first with: ./tts-start.sh")
            sys.exit(1)
        
        logger.info("✅ Connected to TTS service")
        logger.info("🎧 Listening for hotkeys...\n")
        
        # Initialize service check time
        self.last_service_check = time.time()
        
        # Show startup notification
        self.show_notification(
            "TTS Ready",
            f"{SPEAK_HOTKEY_DISPLAY} to speak, {REPLAY_HOTKEY_DISPLAY} to replay, {QUIT_HOTKEY_DISPLAY} to quit"
        )
        
        # Setup hotkeys
        hotkeys = {
            SPEAK_HOTKEY_BINDING: self.on_speak_hotkey,
            REPLAY_HOTKEY_BINDING: self.on_replay_hotkey,
            QUIT_HOTKEY_BINDING: self.on_quit_hotkey,
        }
        
        # Start listening
        try:
            with keyboard.GlobalHotKeys(hotkeys) as listener:
                while self.running:
                    # Periodic health check to detect service disconnection
                    current_time = time.time()
                    if current_time - self.last_service_check > self.service_check_interval:
                        if not self.check_service_health():
                            logger.warning("⚠️  Service health check failed - service may have stopped")
                            self.show_notification(
                                "TTS Warning",
                                "Service disconnected. Restart with 'tts-start'"
                            )
                        self.last_service_check = current_time
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

