import os
import sys
import subprocess


def get_bluetooth_sink():
    try:
        bt_device = os.getenv("Welcome_Back")
        if bt_device:
            result = subprocess.run(
                ["pactl", "list", "short", "sinks"],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n'):
                if bt_device.lower() in line.lower() and 'bluez' in line.lower():
                    sink_id = line.split()[1]
                    return sink_id
    except:
        pass
    
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sinks"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if 'bluez' in line.lower():
                sink_id = line.split()[1]
                return sink_id
    except:
        pass
    
    return None


def play_audio_bluetooth(audio_file: str) -> bool:
    try:
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return False
        
        platform = sys.platform
        
        if platform == "linux":
            bt_sink = get_bluetooth_sink()
            if bt_sink:
                try:
                    subprocess.run(
                        ["paplay", "--device", bt_sink, audio_file],
                        check=True
                    )
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print(f"Failed to play via Bluetooth sink {bt_sink}")
                    return False
            else:
                print("No Bluetooth audio device found")
                return False
        
        elif platform == "darwin":
            try:
                subprocess.run(["afplay", audio_file], check=True, capture_output=True)
                return True
            except:
                return False
        
        return False
        
    except Exception as e:
        print(f"Bluetooth audio playback failed: {e}")
        return False

