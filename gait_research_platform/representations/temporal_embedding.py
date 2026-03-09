from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, Dataset

from gait_research_platform.core.interfaces import RepresentationModel
from gait_research_platform.core.registry import register_representation


def _to_tensor(sequence: np.ndarray) -> torch.Tensor:
    tensor = torch.as_tensor(sequence, dtype=torch.float32)
    if tensor.ndim != 2:
        raise ValueError(f"Expected sequence with shape T x F, got {tuple(tensor.shape)}")
    return tensor.transpose(0, 1)


class ContrastiveSequenceDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, sequences: Sequence[np.ndarray]) -> None:
        self.sequences = list(sequences)

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        sequence = self.sequences[index]
        return _augment_sequence(sequence), _augment_sequence(sequence)


def _augment_sequence(sequence: np.ndarray) -> torch.Tensor:
    features = np.array(sequence, dtype=np.float32, copy=True)
    length = features.shape[0]
    if length < 4:
        return _to_tensor(features)

    crop_ratio = float(np.random.uniform(0.7, 1.0))
    crop_length = max(4, int(length * crop_ratio))
    start = int(np.random.randint(0, max(1, length - crop_length + 1)))
    cropped = features[start : start + crop_length]

    if cropped.shape[0] < length:
        indices = np.linspace(0, cropped.shape[0] - 1, num=length)
        cropped = np.vstack(
            [np.interp(indices, np.arange(cropped.shape[0]), cropped[:, dim]) for dim in range(cropped.shape[1])]
        ).T

    noise = np.random.normal(loc=0.0, scale=0.01, size=cropped.shape).astype(np.float32)
    scale = np.random.uniform(0.9, 1.1)
    return _to_tensor(cropped * scale + noise)


class TemporalCNNEncoder(nn.Module):
    def __init__(self, input_dim: int, embedding_dim: int, channels: list[int], kernel_size: int) -> None:
        super().__init__()
        blocks: list[nn.Module] = []
        in_channels = input_dim
        padding = kernel_size // 2
        for out_channels in channels:
            blocks.extend(
                [
                    nn.Conv1d(in_channels, out_channels, kernel_size=kernel_size, padding=padding),
                    nn.BatchNorm1d(out_channels),
                    nn.GELU(),
                ]
            )
            in_channels = out_channels
        self.backbone = nn.Sequential(*blocks)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.embedding_head = nn.Linear(in_channels, embedding_dim)
        self.projection_head = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.GELU(),
            nn.Linear(embedding_dim, embedding_dim),
        )

    def forward(self, batch: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self.backbone(batch)
        pooled = self.pool(hidden).squeeze(-1)
        embedding = self.embedding_head(pooled)
        projection = self.projection_head(embedding)
        return F.normalize(embedding, dim=-1), F.normalize(projection, dim=-1)


def nt_xent_loss(z1: torch.Tensor, z2: torch.Tensor, temperature: float) -> torch.Tensor:
    batch_size = z1.size(0)
    representations = torch.cat([z1, z2], dim=0)
    similarity = representations @ representations.T
    mask = torch.eye(2 * batch_size, device=similarity.device, dtype=torch.bool)
    similarity = similarity / temperature
    similarity = similarity.masked_fill(mask, float("-inf"))

    positives = torch.cat(
        [torch.diag(similarity, batch_size), torch.diag(similarity, -batch_size)],
        dim=0,
    )
    denominator = torch.logsumexp(similarity, dim=1)
    loss = -positives + denominator
    return loss.mean()


@register_representation("temporal_embedding")
class TemporalEmbeddingModel(RepresentationModel):
    def __init__(self, input_dim: int, embedding_dim: int = 64, channels: list[int] | None = None, kernel_size: int = 3):
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        self.channels = channels or [64, 128]
        self.kernel_size = kernel_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = TemporalCNNEncoder(input_dim, embedding_dim, self.channels, kernel_size).to(self.device)

    def train(self, dataset: Sequence[np.ndarray], config: dict[str, Any]) -> dict[str, Any]:
        training = config["training"]
        loader = DataLoader(
            ContrastiveSequenceDataset(dataset),
            batch_size=training["batch_size"],
            shuffle=True,
            drop_last=len(dataset) > 1,
            num_workers=training.get("num_workers", 0),
        )
        optimizer = torch.optim.Adam(self.model.parameters(), lr=float(training["learning_rate"]))
        self.model.train()

        epochs = int(training["epochs"])
        loss_history: list[float] = []
        for _ in range(epochs):
            epoch_loss = 0.0
            batches = 0
            for view1, view2 in loader:
                view1 = view1.to(self.device)
                view2 = view2.to(self.device)
                _, proj1 = self.model(view1)
                _, proj2 = self.model(view2)
                loss = nt_xent_loss(proj1, proj2, float(training["temperature"]))
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                epoch_loss += float(loss.item())
                batches += 1
            if batches == 0:
                loss_history.append(0.0)
            else:
                loss_history.append(epoch_loss / batches)
        return {
            "final_loss": loss_history[-1] if loss_history else 0.0,
            "loss_history": loss_history,
            "num_sequences": len(dataset),
        }

    def encode(self, sequence: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            batch = _to_tensor(sequence).unsqueeze(0).to(self.device)
            embedding, _ = self.model(batch)
        return embedding.squeeze(0).cpu().numpy()

    def save(self, output_dir: str) -> None:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict(),
                "input_dim": self.input_dim,
                "embedding_dim": self.embedding_dim,
                "channels": self.channels,
                "kernel_size": self.kernel_size,
            },
            path / "model.pt",
        )

    @classmethod
    def load(cls, model_dir: str) -> "TemporalEmbeddingModel":
        checkpoint = torch.load(Path(model_dir) / "model.pt", map_location="cpu")
        model = cls(
            input_dim=int(checkpoint["input_dim"]),
            embedding_dim=int(checkpoint["embedding_dim"]),
            channels=list(checkpoint["channels"]),
            kernel_size=int(checkpoint["kernel_size"]),
        )
        model.model.load_state_dict(checkpoint["state_dict"])
        return model
