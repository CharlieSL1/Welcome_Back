#!/bin/bash
set -e

echo "=== Step 1: Create dataset directory ==="
mkdir -p data/grandfather_aug
mkdir -p checkpoints

echo "=== Step 2: Data augmentation (pitch/tempo/noise) ==="
for f in data/grandfather/Grandfather.wav data/grandfather/Hi.wav data/grandfather/WelcomeHome.wav; do
  base=$(basename "$f" .wav)
  for pitch in -2 0 2; do
    for speed in 0.9 1.0 1.1; do
      ffmpeg -y -i "$f" -filter:a "asetrate=22050*${speed},atempo=1/${speed},rubberband=pitch=${pitch}" \
        "data/grandfather_aug/${base}_p${pitch}_s${speed}.wav" >/dev/null 2>&1 || true
    done
  done
done

echo "=== Step 3: Normalize to mono 22.05 kHz before adding noise ==="
for f in data/grandfather_aug/*.wav; do
  tmp="data/grandfather_aug/tmp_$(basename "$f")"
  ffmpeg -y -i "$f" -ac 1 -ar 22050 "$tmp" >/dev/null 2>&1
  mv "$tmp" "$f"
done

echo "=== Step 3b: Add mild noise ==="
for f in data/grandfather_aug/*.wav; do
  base=$(basename "$f")
  sr=$(soxi -r "$f")
  sox -M "$f" "|sox -n -r ${sr} -c 1 -p synth whitenoise vol 0.01" "data/grandfather_aug/noise_${base}" rate ${sr} || true
done



echo "=== Step 4: Finetune embedding model ==="
python tools/finetune_speaker.py \
  --input_dir data/grandfather_aug \
  --output_model checkpoints/grandfather_vc_model.pt \
  --epochs 8 \
  --batch_size 8 \
  --lr 2e-4 \
  --save_interval 2

echo "=== Step 5: Done ==="
echo "✅ Saved fine-tuned model: checkpoints/grandfather_vc_model.pt"


