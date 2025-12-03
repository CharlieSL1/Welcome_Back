import os
import sys
import subprocess


def play_audio(audio_file: str) -> bool:
    try:
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return False
        
        platform = sys.platform
        
        if platform == "linux":
            try:
                subprocess.run(["aplay", "-q", audio_file], check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(["paplay", audio_file], check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        subprocess.run(["mpv", "--no-video", audio_file], check=True)
                        return True
                    except:
                        pass
        
        elif platform == "darwin":
            subprocess.run(["afplay", audio_file], check=True, capture_output=True)
            return True
        
        else:
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                return True
            except ImportError:
                pass
        
        print("No audio player available")
        return False
        
    except Exception as e:
        print(f"Audio playback failed: {e}")
        return False

