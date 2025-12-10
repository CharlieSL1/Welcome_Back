import datetime
import time
import random
import os
import json
from pathlib import Path
from openai import OpenAI
from SeedVCSpeaker import speak_with_seed_vc
from AudioPlayer import play_audio

try:
    from dotenv import load_dotenv  # type: ignore
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or create a .env file.")

client = OpenAI(api_key=api_key)

# This will control the interval between messages. All the scale is in hours.
MIN_INTERVAL_HOURS = 0.01 
MAX_INTERVAL_HOURS = 0.02


def get_status_from_hour(hour):
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 14:
        return "noon"
    elif 14 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def generate_and_play_message():
    try:
        now = datetime.datetime.now()
        hour = now.hour
        status = get_status_from_hour(hour)

        prompt = f"""
You are writing as a loving Chinese grandfather (外公/爷爷) talking to his grandchild.

Current datetime: {now.strftime('%Y-%m-%d %H:%M')}
Time period: {status}

Task:
- Generate 5 short, warm, everyday messages that this grandfather might naturally send or say to his grandchild at this time of day.
- The messages should be written in natural, modern Chinese.
- Each message should be 1–2 sentences, spoken in a gentle, caring tone, like a voice message on WeChat.
- Do NOT mention that you are an AI, a program, or that the grandfather has passed away. Just write it as if he is alive and talking normally.
- The content should match the time period:
  - In the morning: ask if they slept well, remind them to吃早饭、注意天气、别太累.
  - At noon:问吃饭了没、别熬夜、注意午休.
  - In the afternoon:关心学习/工作进展、提醒放松眼睛、多活动.
  - In the evening:问今天累不累、嘱咐早点休息、少玩手机.
  - At night/very late:轻声叮嘱早点睡、别太辛苦、身体最重要.
- Randomly mix:
  - simple greetings
  - small life reminders (健康、吃饭、睡眠、穿衣、注意安全)
  - emotional support (为你骄傲、想你、慢慢来、有事跟外公说)
- The relationship should feel close and warm, sometimes用"你小子""史立"之类的昵称，但不要过度夸张。

Output format:
- Return ONLY a JSON array of strings.
- Example:
  ["sentence1", "sentence2", "sentence3", "sentence4", "sentence5"]
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        # Try to extract JSON array from the response
        try:
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            messages = json.loads(content)
            if isinstance(messages, list) and len(messages) > 0:
                random_response = random.choice(messages)
            else:
                random_response = content
        except json.JSONDecodeError:
            # If JSON parsing fails, use the content directly
            random_response = content

        audio_output = speak_with_seed_vc(random_response, api_key=api_key)

        if audio_output:
            print(f"Audio file generated: {audio_output}")
            print(f"Attempting to play audio...")
            play_result = play_audio(audio_output)
            if play_result:
                print("✓ Audio playback completed successfully")
            else:
                print("✗ Audio playback failed - check error messages above")
        else:
            print("✗ Generation failed - no audio file was created")

    except Exception as e:
        print(f"Error generating message: {e}")


def get_next_trigger_interval():
    return random.uniform(MIN_INTERVAL_HOURS, MAX_INTERVAL_HOURS) * 3600


def main():
    print("WelcomeBack scheduler started with random triggers")
    print(f"Random interval: {MIN_INTERVAL_HOURS}-{MAX_INTERVAL_HOURS} hours")
    print("Press Ctrl+C to stop")
    
    next_trigger_time = datetime.datetime.now() + datetime.timedelta(seconds=get_next_trigger_interval())
    print(f"Next trigger scheduled at: {next_trigger_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        while True:
            now = datetime.datetime.now()
            
            if now >= next_trigger_time:
                current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Triggering at {current_time_str}")
                generate_and_play_message()
                
                next_interval = get_next_trigger_interval()
                next_trigger_time = now + datetime.timedelta(seconds=next_interval)
                print(f"Next trigger scheduled at: {next_trigger_time.strftime('%Y-%m-%d %H:%M:%S')} (in {next_interval/3600:.2f} hours)")
            
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nScheduler stopped")


if __name__ == "__main__":
    main()