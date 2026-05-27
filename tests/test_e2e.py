"""End-to-end pipeline test using synthetic media."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from vae.pipeline.orchestrator import analyze, collect_clips, run_pipeline
from vae.writers.capcut import write_draft
from vae.writers.report import write_report
from vae.writers.srt import write_srt
from vae.models.subtitle import Subtitle, Word
from tests.conftest import requires_ffmpeg


def _make_synthetic_video(target: Path) -> Path:
    """Create a 6s video with audio pattern tone/silence/tone/silence/tone."""
    audio = (
        "sine=frequency=440:duration=1:sample_rate=44100[a0];"
        "anullsrc=duration=2:sample_rate=44100:channel_layout=mono[a1];"
        "sine=frequency=440:duration=1:sample_rate=44100[a2];"
        "anullsrc=duration=1:sample_rate=44100:channel_layout=mono[a3];"
        "sine=frequency=440:duration=1:sample_rate=44100[a4];"
        "[a0][a1][a2][a3][a4]concat=n=5:v=0:a=1[aout]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=320x240:r=30:d=6",
        "-filter_complex",
        audio,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        str(target),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return target


@pytest.fixture(scope="session")
def synthetic_video_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("e2e_input")
    _make_synthetic_video(root / "clip_01.mp4")
    return root


@requires_ffmpeg
def test_collect_clips_lists_supported_files(synthetic_video_dir: Path):
    clips = collect_clips(synthetic_video_dir)
    assert len(clips) == 1
    assert clips[0].suffix == ".mp4"


@requires_ffmpeg
def test_analyze_populates_silences(synthetic_video_dir: Path):
    clips = collect_clips(synthetic_video_dir)
    ctx = analyze(clips)
    assert len(ctx.clips) == 1
    assert ctx.clips[0].has_audio
    assert ctx.clips[0].width == 320
    silences = ctx.silences[clips[0]]
    # Expect 2 silence ranges (synthetic pattern)
    assert len(silences) == 2


@requires_ffmpeg
def test_run_pipeline_vlog_builds_timeline(synthetic_video_dir: Path):
    ctx, timelines = run_pipeline("vlog", synthetic_video_dir)
    assert len(timelines) == 1
    timeline = timelines[0]
    assert timeline.width == 1920
    assert timeline.height == 1080
    # 3 tones kept (~1s each) after silence removal + padding overlap merging
    video_track = next(t for t in timeline.tracks if t.kind == "video")
    assert 1 <= len(video_track.segments) <= 3
    assert timeline.duration > 0


@requires_ffmpeg
def test_run_pipeline_shorts_returns_vertical_timeline(synthetic_video_dir: Path):
    ctx, timelines = run_pipeline(
        "shorts", synthetic_video_dir, shorts_count=2, shorts_length=4.0
    )
    assert len(timelines) >= 1
    for tl in timelines:
        assert tl.width == 1080
        assert tl.height == 1920
        assert tl.duration > 0


@requires_ffmpeg
def test_writers_emit_files(synthetic_video_dir: Path, tmp_path: Path):
    ctx, timelines = run_pipeline("vlog", synthetic_video_dir)
    timeline = timelines[0]
    out = tmp_path / "out"

    report = write_report(ctx, timeline, out / "analysis_report.json")
    draft = write_draft(timeline, out / "capcut_project")

    assert report.exists()
    assert draft.exists()

    report_data = json.loads(report.read_text(encoding="utf-8"))
    assert "clips" in report_data
    assert "timeline" in report_data
    assert report_data["timeline"]["duration"] > 0

    draft_data = json.loads(draft.read_text(encoding="utf-8"))
    assert draft_data["_format"] == "vae-placeholder/v0"


def test_srt_writer_formats_timestamps(tmp_path: Path):
    subs = [
        Subtitle(
            text="안녕하세요",
            start=0.0,
            end=1.5,
            words=[Word(text="안녕하세요", start=0.0, end=1.5)],
        ),
        Subtitle(
            text="반갑습니다",
            start=2.0,
            end=3.25,
            words=[Word(text="반갑습니다", start=2.0, end=3.25)],
        ),
    ]
    target = tmp_path / "subs.srt"
    write_srt(subs, target)
    content = target.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,500" in content
    assert "00:00:02,000 --> 00:00:03,250" in content
    assert "안녕하세요" in content
