from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


requires_ffmpeg = pytest.mark.skipif(not _have_ffmpeg(), reason="ffmpeg not on PATH")


@pytest.fixture(scope="session")
def synthetic_clip(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a 6s clip with the pattern: tone(1s) | silence(2s) | tone(1s) | silence(1s) | tone(1s).

    Used to verify silence detection produces the expected ranges.
    Requires ffmpeg on PATH.
    """
    if not _have_ffmpeg():
        pytest.skip("ffmpeg not available")

    out = tmp_path_factory.mktemp("media") / "tone_silence.wav"

    audio_filter = (
        "sine=frequency=440:duration=1:sample_rate=44100[a0];"
        "anullsrc=duration=2:sample_rate=44100:channel_layout=mono[a1];"
        "sine=frequency=440:duration=1:sample_rate=44100[a2];"
        "anullsrc=duration=1:sample_rate=44100:channel_layout=mono[a3];"
        "sine=frequency=440:duration=1:sample_rate=44100[a4];"
        "[a0][a1][a2][a3][a4]concat=n=5:v=0:a=1[out]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-filter_complex",
        audio_filter,
        "-map",
        "[out]",
        "-ac",
        "1",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out
