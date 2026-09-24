"""Script to record a browser demo video of SafeSpend AI agent with upbeat lo-fi background music."""

import math
import os
import struct
import time
import wave
import imageio_ffmpeg
from google.cloud import storage
from playwright.sync_api import sync_playwright

PROJECT_ID = "qwiklabs-gcp-01-fa8e86a4b8f6"
BUCKET_NAME = "safespend-ai-assets-qwiklabs-gcp-01-fa8e86a4b8f6"


def create_lofi_audio(filename="lofi_track.wav", duration_sec=30, sample_rate=44100):
    """Synthesizes an upbeat lo-fi background music track using pure Python math."""
    num_samples = int(sample_rate * duration_sec)
    wav_file = wave.open(filename, "w")
    wav_file.setnchannels(2)  # Stereo
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)

    # Chords (Emaj7, C#m7, Amaj7, B7) in Hz
    chords = [
        [329.63, 415.30, 493.88, 622.25],  # Emaj7
        [277.18, 329.63, 415.30, 493.88],  # C#m7
        [220.00, 277.18, 329.63, 415.30],  # Amaj7
        [246.94, 311.13, 369.99, 440.00],  # B7
    ]
    bpm = 85
    beat_sec = 60.0 / bpm

    audio_bytes = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        chord_idx = int((t / (beat_sec * 4))) % len(chords)
        chord = chords[chord_idx]

        # Soft warm warm synth chords
        synth = 0.0
        for freq in chord:
            synth += 0.1 * math.sin(2 * math.pi * freq * t)
            synth += 0.03 * math.sin(2 * math.pi * (freq * 0.5) * t)  # Sub-octave

        # Lo-fi vinyl warmth / crackle
        vinyl = (math.sin(2 * math.pi * 12000 * t) * 0.005) if (i % 73 == 0) else 0.0

        # Upbeat kick & snare drum rhythm
        beat_t = t % beat_sec
        kick = 0.0
        snare = 0.0
        if beat_t < 0.1 and int(t / beat_sec) % 2 == 0:  # Kick on beats 1 & 3
            kick = 0.3 * math.sin(2 * math.pi * 60 * (1 - beat_t / 0.1) * beat_t)
        if beat_t < 0.12 and int(t / beat_sec) % 2 == 1:  # Snare on beats 2 & 4
            snare = 0.15 * (math.sin(2 * math.pi * 250 * beat_t) + math.sin(2 * math.pi * 800 * beat_t))

        # Hi-hat on eighth notes
        hihat = 0.0
        if (t % (beat_sec / 2)) < 0.03:
            hihat = 0.04 * (math.sin(2 * math.pi * 7000 * t))

        mix = (synth + vinyl + kick + snare + hihat) * 0.4
        mix = max(-1.0, min(1.0, mix))
        sample_val = int(mix * 32767)

        # Write stereo samples
        data = struct.pack("<hh", sample_val, sample_val)
        audio_bytes.extend(data)

    wav_file.writeframes(audio_bytes)
    wav_file.close()
    return filename


def record_demo():
    print("Generating lo-fi music track...")
    audio_path = create_lofi_audio("lofi_track.wav", duration_sec=40)

    record_dir = "./recordings"
    os.makedirs(record_dir, exist_ok=True)

    print("Starting Playwright browser recording...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=record_dir,
            record_video_size={"width": 1280, "height": 800},
        )

        page = context.new_page()
        page.goto("http://localhost:8080")
        page.wait_for_timeout(2000)

        # Prompt 1: Click first prompt chip
        print("Clicking prompt chip 1...")
        page.click("button.chip[data-prompt*='espresso machine']")
        page.wait_for_timeout(1000)

        # Wait for agent response bubble / card
        page.wait_for_selector(".msg.agent", timeout=45000)
        page.wait_for_timeout(6000)

        # Prompt 2: Rich prompt with tool calls & cashflow projection & image generation
        print("Sending prompt 2 (cashflow + image gen)...")
        prompt2 = "Project my cashflow for the next 30 days and generate a product image of an espresso machine."
        page.fill("#input", prompt2)
        page.wait_for_timeout(1000)
        page.click("form button")

        # Wait for response & rendered card
        page.wait_for_timeout(12000)

        page.wait_for_timeout(5000)
        context.close()
        browser.close()

    # Find recorded webm
    recorded_files = [os.path.join(record_dir, f) for f in os.listdir(record_dir) if f.endswith(".webm")]
    if not recorded_files:
        raise RuntimeError("No webm video recorded by Playwright.")

    raw_video = recorded_files[0]
    print(f"Raw video recorded: {raw_video}")

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    output_mp4 = "safespend_ai_demo.mp4"

    print("Merging video and lo-fi audio track with ffmpeg...")
    cmd = (
        f'"{ffmpeg_exe}" -y -i "{raw_video}" -i "{audio_path}" '
        f'-c:v libx264 -preset fast -crf 22 -c:a aac -b:a 192k -shortest "{output_mp4}"'
    )
    os.system(cmd)

    if not os.path.exists(output_mp4):
        raise RuntimeError("FFmpeg failed to create output_mp4")

    print(f"Demo video created: {output_mp4} ({os.path.getsize(output_mp4)} bytes)")

    # Upload demo video to GCS
    print("Uploading demo video to GCS...")
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("safespend_ai_demo.mp4")
    blob.upload_from_filename(output_mp4, content_type="video/mp4")

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/safespend_ai_demo.mp4"
    print(f"Public URL: {public_url}")


if __name__ == "__main__":
    record_demo()
