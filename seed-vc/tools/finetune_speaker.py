import torch
import torchaudio
import os
import glob
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

class VoiceDataset(Dataset):
    def __init__(self, root):
        self.files = sorted(glob.glob(os.path.join(root, "*.wav")))
    def __len__(self):
        return len(self.files)
    def __getitem__(self, idx):
        import soundfile as sf
        wav, sr = sf.read(self.files[idx], always_2d=False, dtype="float32")
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        import torch
        wav = torch.from_numpy(wav).unsqueeze(0)
        if sr != 22050:
            import torchaudio.functional as F
            wav = F.resample(wav, sr, 22050)
            sr = 22050
        wav = wav[:, :22050 * 3]  # 3 s
        return wav

class SimpleVoiceEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv1d(1, 32, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv1d(32, 64, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv1d(64, 128, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.Tanh()
        )
    def forward(self, x):
        return self.model(x)

def train(args):
    ds = VoiceDataset(args.input_dir)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=True, drop_last=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

    model = SimpleVoiceEncoder().to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.MSELoss()

    for epoch in range(args.epochs):
        model.train()
        losses = []
        for wav in tqdm(dl, desc=f"Epoch {epoch+1}/{args.epochs}"):
            wav = wav.to(device)
            emb = model(wav)
            loss = criterion(emb, emb.detach())  # 自监督
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        print(f"Mean loss: {sum(losses)/len(losses):.6f}")
        if (epoch + 1) % args.save_interval == 0:
            torch.save(model.state_dict(), args.output_model)
            print(f"✅ Saved checkpoint: {args.output_model}")

    torch.save(model.state_dict(), args.output_model)
    print(f"✅ Final model saved: {args.output_model}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--input_dir", type=str, required=True)
    p.add_argument("--output_model", type=str, required=True)
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--save_interval", type=int, default=2)
    args = p.parse_args()
    train(args)


