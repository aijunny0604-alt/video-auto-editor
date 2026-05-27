"""STT analyzer - word-level transcription via faster-whisper."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from vae.models.subtitle import Subtitle, Word

_SENTENCE_ENDS = frozenset(".,!?")


def transcribe(
    path: Path,
    model_size: Literal["tiny", "base", "small", "medium", "large-v3"] = "large-v3",
    language: str = "ko",
    device: Literal["cuda", "cpu", "auto"] = "auto",
    compute_type: str | None = None,
) -> list[Word]:
    """Transcribe an audio/video file and return word-level timestamps.

    Uses faster-whisper for GPU-accelerated inference when available.

    Args:
        path: Input media file (video or audio).
        model_size: Whisper model variant to load.
        language: BCP-47 language code (e.g. 'ko', 'en').
        device: Inference device; 'auto' picks 'cuda' if available else 'cpu'.
        compute_type: Quantisation type; None auto-selects float16 (cuda) or int8 (cpu).

    Returns:
        List of Word objects with text, start, end, and confidence.
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "faster-whisper is required for transcription. "
            "Install it with: pip install faster-whisper"
        ) from exc

    resolved_device = _resolve_device(device)
    resolved_compute = compute_type or ("float16" if resolved_device == "cuda" else "int8")

    model = WhisperModel(model_size, device=resolved_device, compute_type=resolved_compute)
    segments, _ = model.transcribe(str(path), language=language, word_timestamps=True)

    words: list[Word] = []
    for segment in segments:
        if segment.words is None:
            continue
        for w in segment.words:
            words.append(
                Word(
                    text=w.word.strip(),
                    start=w.start,
                    end=w.end,
                    confidence=w.probability,
                )
            )
    return words


def words_to_subtitles(
    words: list[Word],
    max_chars: int = 30,
    max_duration: float = 4.0,
    gap_threshold: float = 0.5,
) -> list[Subtitle]:
    """Group Word objects into subtitle chunks.

    Splits on sentence punctuation, max_chars, max_duration, or inter-word gaps.

    Args:
        words: Ordered list of Word objects from transcribe().
        max_chars: Maximum characters per subtitle (counted as joined text).
        max_duration: Maximum duration in seconds per subtitle.
        gap_threshold: Minimum gap (seconds) between words that forces a split.

    Returns:
        List of Subtitle objects.
    """
    if not words:
        return []

    subtitles: list[Subtitle] = []
    group: list[Word] = []

    for i, word in enumerate(words):
        group.append(word)
        joined = " ".join(w.text for w in group)
        duration = group[-1].end - group[0].start

        ends_sentence = word.text and word.text[-1] in _SENTENCE_ENDS
        over_chars = len(joined) > max_chars
        over_duration = duration > max_duration

        next_gap_big = False
        if i + 1 < len(words):
            next_gap_big = (words[i + 1].start - word.end) >= gap_threshold

        if ends_sentence or over_chars or over_duration or next_gap_big:
            subtitles.append(_make_subtitle(group))
            group = []

    if group:
        subtitles.append(_make_subtitle(group))

    return subtitles


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_device(device: str) -> str:
    """Return 'cuda' or 'cpu' based on the requested device and availability."""
    if device != "auto":
        return device
    try:
        import torch  # type: ignore[import]
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _make_subtitle(words: list[Word]) -> Subtitle:
    """Build a Subtitle from a non-empty list of Word objects."""
    return Subtitle(
        text=" ".join(w.text for w in words),
        start=words[0].start,
        end=words[-1].end,
        words=list(words),
    )
