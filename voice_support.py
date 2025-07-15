import pyttsx3
import threading
import time

# Global variables
is_speaking = False
speak_thread = None
stop_requested = False
current_engine = None

def speak_text(text):
    global is_speaking, speak_thread, stop_requested
    
    # If already speaking, stop first
    if is_speaking:
        stop_speaking()
        time.sleep(0.5)  
    
    # Reset flags
    stop_requested = False
    
    # Start speaking in a separate thread
    speak_thread = threading.Thread(target=_speak_worker, args=(text,))
    speak_thread.daemon = True
    speak_thread.start()

def _speak_worker(text):
    global is_speaking, stop_requested, current_engine
    
    try:
        # Create fresh engine for this session
        current_engine = pyttsx3.init()
        current_engine.setProperty('rate', 150)
        current_engine.setProperty('volume', 1.0)
        
        is_speaking = True
        
        # Split text into sentences for better stop control
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        
        for sentence in sentences:
            if stop_requested:
                break
            
            # Use a flag to check if we should continue
            if not stop_requested and sentence:
                current_engine.say(sentence)
                
                # Run in small chunks to check stop_requested frequently
                start_time = time.time()
                while current_engine._inLoop:
                    if stop_requested:
                        current_engine.stop()
                        break
                    time.sleep(0.1)
                    # Prevent infinite loop
                    if time.time() - start_time > 30:
                        break
                
                # If not stopped, run normally
                if not stop_requested:
                    current_engine.runAndWait()
                
    except Exception as e:
        print(f"Speech error: {e}")
    finally:
        # Clean up
        is_speaking = False
        if current_engine:
            try:
                current_engine.stop()
                del current_engine
                current_engine = None
            except:
                pass

def stop_speaking():
    global is_speaking, stop_requested, speak_thread, current_engine
    
    # Set stop flag
    stop_requested = True
    
    # Stop the engine immediately
    if current_engine:
        try:
            current_engine.stop()
        except:
            pass
    
    # Set speaking flag to False
    is_speaking = False
    
    # Wait for thread to finish (with timeout)
    if speak_thread and speak_thread.is_alive():
        speak_thread.join(timeout=2.0)
    
    # Force cleanup
    if current_engine:
        try:
            del current_engine
            current_engine = None   
        except:
            pass

def get_speaking_status():
    return is_speaking