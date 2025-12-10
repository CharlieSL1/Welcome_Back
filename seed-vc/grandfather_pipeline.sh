#!/usr/bin/env bash

set -euo pipefail



# ====== 基本路径（如与你本机不同，请在此改）======

SRC_WAV="data/Hi_CH.wav"                                  # 你要说的内容（source）

REF_RAW="data/grandfather/Grandfather.wav"                # 外公原始音频

REF_WAV="data/grandfather/Grandfather_ref.wav"            # 22.05k 单声道参考音频

OUT_DIR="outputs"                                         # 推理输出目录

AUG_DIR="data/grandfather_aug"                            # 数据增强目录

CHECKPOINT_DIR="checkpoints"

FINETUNE_OUT="${CHECKPOINT_DIR}/grandfather_vc_model.pt"  # 微调后的说话人模型

mkdir -p "$(dirname "$REF_WAV")" "$OUT_DIR" "$AUG_DIR" "$CHECKPOINT_DIR"



echo "=== 0) 前置检查 ==="

[ -f "$SRC_WAV" ] || { echo "❌ 找不到 source: $SRC_WAV"; exit 1; }

[ -f "$REF_RAW" ] || { echo "❌ 找不到外公原始音频: $REF_RAW"; exit 1; }



echo "=== 1) 禁用 MPS/GPU，强制 CPU+FP32 ==="

export PYTORCH_ENABLE_MPS_FALLBACK=1

export PYTORCH_MPS_DEVICE_DISABLED=1

export CUDA_VISIBLE_DEVICES=""

export OMP_NUM_THREADS=4



INF="inference.py"

[ -f "$INF" ] || { echo "❌ 没找到 inference.py，请在 seed-vc 根目录执行本脚本"; exit 1; }



# 幂等补丁：避免 MPS/FP16 报错（Whisper LayerNorm、fft）

if ! head -n 20 "$INF" | grep -q "__SEEDVC_CPU_FP32_PATCH__"; then

  TMPINF="$(mktemp)"

  cat > "$TMPINF" <<'PYHEAD'

# __SEEDVC_CPU_FP32_PATCH__

import os

os.environ["PYTORCH_MPS_DEVICE_DISABLED"]="1"

os.environ["CUDA_VISIBLE_DEVICES"]=""

import torch

if hasattr(torch, "set_default_dtype"):

    torch.set_default_dtype(torch.float32)

if hasattr(torch.backends, "mps"):

    torch.backends.mps.is_available = lambda: False

    torch.backends.mps.is_built = lambda: False

PYHEAD

  cp "$INF" "${INF}.bak.$(date +%s)"

  cat "$TMPINF" "${INF}" > "${INF}.patched" && mv "${INF}.patched" "$INF"

  rm -f "$TMPINF"

  echo "✅ 已为 inference.py 注入 CPU/FP32 补丁"

else

  echo "ℹ️  inference.py 已含 CPU/FP32 补丁，跳过注入"

fi



echo "=== 2) 依赖对齐（torch/torchaudio=2.2.2，及音频依赖）==="

python - <<'PY'

import sys, subprocess

pkgs=[("torch","2.2.2"),("torchaudio","2.2.2"),

      ("soundfile",None),("audioread",None),("librosa",None),

      ("tqdm",None),("numpy",None),("scipy",None)]

def pipi(s): subprocess.check_call([sys.executable,"-m","pip","install",s])

for n,v in pkgs:

    try: __import__(n); print("OK:",n)

    except: pipi(f"{n}=={v}" if v else n)

print("依赖就绪")

PY



echo "=== 3) 参考音频规范化（22.05k/mono + 轻度净化）==="

ffmpeg -y -hide_banner -loglevel error -i "$REF_RAW" -ac 1 -ar 22050 "$REF_WAV"

TMP_REF="${REF_WAV}.tmp.wav"

ffmpeg -y -hide_banner -loglevel error -i "$REF_WAV" -af "highpass=f=80,afftdn=nf=-25" "$TMP_REF"

mv "$TMP_REF" "$REF_WAV"



echo "=== 4) 数据增强（生成稳定嵌入的近邻样本）==="

rm -rf "$AUG_DIR" && mkdir -p "$AUG_DIR"

cp "$REF_WAV" "$AUG_DIR/ref_base.wav"

ffmpeg -y -hide_banner -loglevel error -i "$REF_WAV" -af "atempo=0.97" "$AUG_DIR/ref_t097.wav"

ffmpeg -y -hide_banner -loglevel error -i "$REF_WAV" -af "atempo=1.03" "$AUG_DIR/ref_t103.wav"

ffmpeg -y -hide_banner -loglevel error -i "$REF_WAV" -filter:a "asetrate=22050*1.017,aresample=22050,atempo=1/1.017" "$AUG_DIR/ref_p+0.3st.wav"

ffmpeg -y -hide_banner -loglevel error -i "$REF_WAV" -filter:a "asetrate=22050*0.983,aresample=22050,atempo=1/0.983" "$AUG_DIR/ref_p-0.3st.wav"

ffmpeg -y -hide_banner -loglevel error -i "$REF_WAV" -af "equalizer=f=200:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1:g=2" "$AUG_DIR/ref_eq.wav"



echo "=== 5) 说话人嵌入微调 ==="

python tools/finetune_speaker.py \
  --input_dir "$AUG_DIR" \
  --output_model "$FINETUNE_OUT" \
  --epochs 8 \
  --batch_size 2 \
  --lr 2e-4 \
  --save_interval 2

echo "✅ 微调完成：$FINETUNE_OUT"



echo "=== 6) 网格搜索推理（多组参数 + 参考音频/微调模型两路）==="

STEPS_LIST=(25 40)

CFG_LIST=(0.6 0.7 0.8)

F0C_LIST=(1 0)

SEMI_LIST=(-0.5 0 0.5)

TARGETS=("data/grandfather/Grandfather_ref.wav" "$FINETUNE_OUT")



for TGT in "${TARGETS[@]}"; do

  for STEPS in "${STEPS_LIST[@]}"; do

    for CFG in "${CFG_LIST[@]}"; do

      for F0C in "${F0C_LIST[@]}"; do

        for SEMI in "${SEMI_LIST[@]}"; do

          TAG="$(basename "$TGT")_s${STEPS}_cfg${CFG}_f0c${F0C}_semi${SEMI}"

          OUT_WAV="${OUT_DIR}/vc_${TAG}.wav"

          echo "-> Inference: $TAG"

          python inference.py \
            --source "$SRC_WAV" \
            --target "$TGT" \
            --output "$OUT_DIR" \
            --diffusion-steps "$STEPS" \
            --inference-cfg-rate "$CFG" \
            --f0-condition "$F0C" \
            --auto-f0-adjust 1 \
            --semi-tone-shift "$SEMI" \
            --fp16 False || echo "⚠️ 组合失败，跳过"

          LAST="$(ls -t "$OUT_DIR"/*.wav | head -n1 || true)"

          [ -f "$LAST" ] && mv -f "$LAST" "$OUT_WAV"

        done

      done

    done

  done

done



echo "=== 7) 客观相似度打分（Mel 余弦↑ + MFCC距离↓）并选 Top10 ==="

python - <<'PY'

import os, glob, numpy as np, soundfile as sf, librosa

ref="data/grandfather/Grandfather_ref.wav"

outs=sorted(glob.glob("outputs/*.wav"))

if not outs:

    print("❌ 无输出"); raise SystemExit(1)



def load_mono_22k(p):

    y,sr=sf.read(p,always_2d=False)

    if y.ndim>1: y=y.mean(axis=1)

    if sr!=22050: y=librosa.resample(y.astype(np.float32),sr,22050); sr=22050

    return y.astype(np.float32),sr



def score(op):

    yr,_=load_mono_22k(ref); yo,_=load_mono_22k(op)

    L=min(len(yr),len(yo))

    if L<11025: return None

    yr,yo=yr[:L],yo[:L]

    melr=librosa.feature.melspectrogram(y=yr,sr=22050,n_fft=1024,hop_length=256,n_mels=80)

    melo=librosa.feature.melspectrogram(y=yo,sr=22050,n_fft=1024,hop_length=256,n_mels=80)

    r=librosa.power_to_db(melr+1e-10).mean(axis=1)

    o=librosa.power_to_db(melo+1e-10).mean(axis=1)

    cos=float(np.dot(r,o)/(np.linalg.norm(r)*np.linalg.norm(o)+1e-9))

    mfccr=librosa.feature.mfcc(y=yr,sr=22050,n_mfcc=13)

    mfcco=librosa.feature.mfcc(y=yo,sr=22050,n_mfcc=13)

    T=min(mfccr.shape[1],mfcco.shape[1])

    mcd=float(np.mean(np.linalg.norm(mfccr[:,:T]-mfcco[:,:T],axis=0)))

    score=cos-0.01*mcd

    return {"file":op,"cos":cos,"mcd":mcd,"score":score}



rows=[]

for p in outs:

    try:

        s=score(p)

        if s: rows.append(s)

    except Exception as e:

        print("跳过",p,"因",e)

rows=sorted(rows,key=lambda x:-x["score"])[:10]

print("\n=== Top-10 候选 ===")

for i,r in enumerate(rows,1):

    print(f"{i:02d}. {os.path.basename(r['file'])}  score={r['score']:.4f}  (cos={r['cos']:.4f}, mcd~{r['mcd']:.3f})")

with open("outputs/TOP10.txt","w") as f:

    for r in rows: f.write(f"{r['file']}\n")

print("\n已写入 outputs/TOP10.txt")

PY



echo "=== 8) 完成 ==="

echo "👉 试听 outputs/TOP10.txt 列出的文件；通常 cfg=0.6/0.7、f0-condition=0、steps=40 更像外公音色；若觉得偏亮，可试 semi=-0.5。"


