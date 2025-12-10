import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_DEVICE"] = "none"

import torch
if torch.backends.mps.is_available():
    print("⚠️  MPS detected, forcing CPU mode.")
device = torch.device("cpu")

import subprocess

# 调用原 inference.py
subprocess.run([
    "python", "inference.py",
    "--source", "data/Hi_CH.wav",
    "--target", "data/grandfather/Grandfather_ref.wav",
    "--output", "outputs",
    "--diffusion-steps", "25",
    "--inference-cfg-rate", "0.7"
])
