import os
import sys
import subprocess
import tempfile
from pathlib import Path


def text_to_speech_tts(text: str, output_path: str, language: str = "zh", api_key: str = None) -> bool:
    try:
        from openai import OpenAI
        import os
        
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        client = OpenAI(api_key=api_key)
        
        voice = "alloy"
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
        
        return True
        
    except Exception as e:
        print(f"TTS conversion failed: {e}")
        return False


def speak_with_seed_vc(text: str, 
                       seed_vc_path: str = None,
                       reference_audio: str = None,
                       output_dir: str = None,
                       api_key: str = None) -> str:
    try:
        if seed_vc_path is None:
            seed_vc_path = os.getenv("SEED_VC_PATH")
        if seed_vc_path is None:
            project_root = Path(__file__).resolve().parent
            default_path = project_root / "seed-vc"
            if default_path.exists():
                seed_vc_path = str(default_path)
        if seed_vc_path is None:
            raise ValueError("Seed-VC path not found. Set SEED_VC_PATH or place seed-vc/ in project root.")
        
        if reference_audio is None:
            grandfather_dir = os.path.join(seed_vc_path, "data/grandfather")
            checkpoints_dir = os.path.join(seed_vc_path, "checkpoints")
            
            reference_audio_options = [
                os.path.join(checkpoints_dir, "grandfather_vc_model.pt"),
                os.path.join(grandfather_dir, "Grandfather_ref_enhanced.wav"),
                os.path.join(grandfather_dir, "Grandfather_ref_long.wav"),
                os.path.join(grandfather_dir, "Grandfather_ref_rebuild.wav"),
                os.path.join(grandfather_dir, "Grandfather_ref.wav"),
                os.path.join(grandfather_dir, "Grandfather.wav"),
                os.path.join(grandfather_dir, "WelcomeHome_ref.wav"),
                os.path.join(grandfather_dir, "Hi_ref.wav"),
            ]
            
            reference_audio = None
            for option in reference_audio_options:
                if os.path.exists(option):
                    reference_audio = option
                    break
            
            if reference_audio is None:
                if os.path.exists(grandfather_dir):
                    wav_files = list(Path(grandfather_dir).glob("*.wav"))
                    if wav_files:
                        ref_files = [f for f in wav_files if "ref" in f.name.lower() or "grandfather" in f.name.lower()]
                        if ref_files:
                            reference_audio = str(ref_files[0])
                        else:
                            reference_audio = str(wav_files[0])
                
                if reference_audio is None:
                    reference_audio = os.path.join(grandfather_dir, "Grandfather_ref.wav")
        
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        
        os.makedirs(output_dir, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_source:
            source_audio_path = tmp_source.name
        
        if not text_to_speech_tts(text, source_audio_path, language="zh", api_key=api_key):
            print("TTS conversion failed")
            os.unlink(source_audio_path)
            return None
        
        if not os.path.exists(reference_audio):
            print(f"Reference audio not found: {reference_audio}")
            os.unlink(source_audio_path)
            return None
        
        inference_script = os.path.join(seed_vc_path, "inference.py")
        
        if not os.path.exists(inference_script):
            print(f"inference.py not found: {inference_script}")
            os.unlink(source_audio_path)
            return None
        
        cmd = [
            sys.executable,
            inference_script,
            "--source", source_audio_path,
            "--target", reference_audio,
            "--output", output_dir,
            "--diffusion-steps", "40",
            "--inference-cfg-rate", "0.7",
            "--f0-condition", "0",
            "--auto-f0-adjust", "1",
            "--fp16", "False"
        ]
        
        result = subprocess.run(cmd, cwd=seed_vc_path, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"seed-vc conversion failed: {result.stderr}")
            os.unlink(source_audio_path)
            return None
        
        output_files = sorted(Path(output_dir).glob("*.wav"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if output_files:
            output_path = str(output_files[0])
            
            try:
                os.unlink(source_audio_path)
            except:
                pass
            
            return output_path
        else:
            print("Output file not found")
            os.unlink(source_audio_path)
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_text = "你好，今天过得怎么样？"
    result = speak_with_seed_vc(test_text)
    if result:
        print(f"Generated audio file: {result}")
    else:
        print("Generation failed")

