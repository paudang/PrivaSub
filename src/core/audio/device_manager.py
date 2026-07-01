import os
import sys

# We try to import pyaudiowpatch (for Windows loopback), 
# and fall back to standard pyaudio on other platforms.
try:
    import pyaudiowpatch as pyaudio
    HAS_WPATCH = True
except ImportError:
    import pyaudio
    HAS_WPATCH = False

def find_wasapi_loopback_device():
    """Finds the default WASAPI loopback device for Windows."""
    if not HAS_WPATCH:
        return None
        
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except IOError:
        p.terminate()
        return None
        
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    
    # Check if default speakers are already a loopback device
    if default_speakers.get("isLoopbackDevice", False):
        p.terminate()
        return default_speakers
        
    # Otherwise, search loopback devices matching the default speaker's name
    for loopback in p.get_loopback_device_info_generator():
        if default_speakers["name"] in loopback["name"]:
            p.terminate()
            return loopback
            
    # Fallback to any loopback device
    for loopback in p.get_loopback_device_info_generator():
        p.terminate()
        return loopback
        
    p.terminate()
    return None

def get_available_devices():
    """Returns a list of dicts with available WASAPI loopback and unique input devices."""
    devices = []
    seen_names = set()
    p = pyaudio.PyAudio()
    try:
        if HAS_WPATCH:
            for loopback in p.get_loopback_device_info_generator():
                if loopback["name"] not in seen_names:
                    seen_names.add(loopback["name"])
                    devices.append({
                        "index": loopback["index"],
                        "name": loopback["name"],
                        "channels": loopback["maxInputChannels"],
                        "rate": int(loopback["defaultSampleRate"]),
                        "is_loopback": True
                    })
        # Also add standard input devices (microphones/virtual cables), avoiding duplicates
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxInputChannels"] > 0 and not dev.get("isLoopbackDevice", False):
                if dev["name"] not in seen_names:
                    seen_names.add(dev["name"])
                    devices.append({
                        "index": dev["index"],
                        "name": dev["name"],
                        "channels": dev["maxInputChannels"],
                        "rate": int(dev["defaultSampleRate"]),
                        "is_loopback": False
                    })
    except Exception as e:
        print(f"[Audio] Error listing devices: {e}")
    finally:
        p.terminate()
    return devices
