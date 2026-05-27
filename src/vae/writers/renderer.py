"""FFmpeg-based final video renderer.

Turns a Timeline + (optional) SRT + (optional) BGM into a finished mp4 ready
for upload — vlog (16:9) or shorts (9:16). Pure ffmpeg subprocess; no external
libs.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from vae.models.subtitle import Subtitle
from vae.models.timeline import Segment, Timeline
from vae.writers.srt import write_srt


@dataclass
class RenderOptions:
    burn_subtitles: bool = True
    transition: str = "fade"           # "fade", "none"
    transition_seconds: float = 0.25
    bgm_path: Path | None = None
    bgm_volume: float = 0.18           # 0.0 = mute, 1.0 = original
    video_bitrate: str = "6M"
    audio_bitrate: str = "192k"
    crf: int = 20


def render_timeline(
    timeline: Timeline,
    output: Path,
    subtitles: list[Subtitle] | None = None,
    options: RenderOptions | None = None,
    ffmpeg_bin: str = "ffmpeg",
) -> Path:
    """Render a Timeline to a finished mp4.

    Pipeline: per-segment extract -> concat (optional fade) -> burn subs
    -> mix BGM. Each step uses ffmpeg subprocess; intermediate files live
    in a temp folder that's cleaned up after.

    Args:
        timeline: Edited timeline (vlog or shorts).
        output: Destination .mp4 path.
        subtitles: Optional subtitles (timeline coordinates) to burn in.
        options: RenderOptions; defaults if None.
    """
    opt = options or RenderOptions()
    output.parent.mkdir(parents=True, exist_ok=True)
    video_track = next((t for t in timeline.tracks if t.kind == "video"), None)
    if video_track is None or not video_track.segments:
        raise ValueError("timeline has no video segments")

    with tempfile.TemporaryDirectory(prefix="vae_render_") as tmp:
        work = Path(tmp)

        # 1. extract per-segment clips (with crop+scale applied)
        segment_files = _extract_segments(
            video_track.segments, timeline, work, opt, ffmpeg_bin
        )

        # 2. concat (with optional fade between)
        concat_out = work / "concat.mp4"
        if opt.transition == "fade" and len(segment_files) > 1 and opt.transition_seconds > 0:
            _concat_with_fade(segment_files, concat_out, timeline, opt, ffmpeg_bin)
        else:
            _concat_simple(segment_files, concat_out, work, ffmpeg_bin)

        # 3. burn subtitles
        post_subs = concat_out
        if opt.burn_subtitles and subtitles:
            post_subs = work / "with_subs.mp4"
            srt_path = work / "subs.srt"
            write_srt(subtitles, srt_path)
            _burn_subtitles(concat_out, srt_path, post_subs, timeline, ffmpeg_bin)

        # 4. mix BGM
        if opt.bgm_path is not None and opt.bgm_path.exists():
            _mix_bgm(post_subs, opt.bgm_path, output, opt, ffmpeg_bin)
        else:
            shutil.copy2(post_subs, output)

    return output


# ---------------------------------------------------------------------------
# Internal steps
# ---------------------------------------------------------------------------

def _extract_segments(
    segments: list[Segment],
    timeline: Timeline,
    work: Path,
    opt: RenderOptions,
    ffmpeg_bin: str,
) -> list[Path]:
    """Cut each Segment from its source, applying crop+scale to canvas size."""
    out_files: list[Path] = []
    for i, seg in enumerate(segments):
        out = work / f"seg_{i:04d}.mp4"
        vf_parts = []
        if seg.crop is not None:
            c = seg.crop
            vf_parts.append(
                f"crop=in_w*{c.width}:in_h*{c.height}:in_w*{c.x}:in_h*{c.y}"
            )
        vf_parts.append(f"scale={timeline.width}:{timeline.height}:flags=lanczos")
        vf_parts.append("setsar=1")
        vf = ",".join(vf_parts)

        cmd = [
            ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{seg.source_range.start:.3f}",
            "-i",
            str(seg.source),
            "-t",
            f"{seg.source_range.duration:.3f}",
            "-vf",
            vf,
            "-r",
            f"{timeline.fps}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "fast",
            "-crf",
            str(opt.crf),
            "-c:a",
            "aac",
            "-b:a",
            opt.audio_bitrate,
            "-ar",
            "44100",
            "-ac",
            "2",
            str(out),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        out_files.append(out)
    return out_files


def _concat_simple(
    parts: list[Path],
    output: Path,
    work: Path,
    ffmpeg_bin: str,
) -> None:
    """Concatenate identically-encoded parts via the concat demuxer."""
    list_file = work / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in parts),
        encoding="utf-8",
    )
    subprocess.run(
        [
            ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(output),
        ],
        check=True,
        capture_output=True,
    )


def _concat_with_fade(
    parts: list[Path],
    output: Path,
    timeline: Timeline,
    opt: RenderOptions,
    ffmpeg_bin: str,
) -> None:
    """Concatenate with xfade transitions between adjacent clips."""
    inputs: list[str] = []
    for p in parts:
        inputs.extend(["-i", str(p)])

    # Build cumulative offsets for xfade: each transition starts at
    # (sum of previous durations) - (transition_seconds * already_done)
    durations: list[float] = []
    for p in parts:
        meta = subprocess.run(
            [
                ffmpeg_bin,
                "-hide_banner",
                "-i",
                str(p),
            ],
            capture_output=True,
            text=True,
            check=False,
        ).stderr
        dur = _parse_duration(meta) or 1.0
        durations.append(dur)

    filter_parts: list[str] = []
    v_label = "[0:v]"
    a_label = "[0:a]"
    cum = durations[0]
    for i in range(1, len(parts)):
        next_v = f"[v{i}]"
        next_a = f"[a{i}]"
        offset = max(0.0, cum - opt.transition_seconds)
        filter_parts.append(
            f"{v_label}[{i}:v]xfade=transition=fade:duration={opt.transition_seconds}:offset={offset}{next_v}"
        )
        filter_parts.append(
            f"{a_label}[{i}:a]acrossfade=d={opt.transition_seconds}{next_a}"
        )
        v_label = next_v
        a_label = next_a
        cum = cum + durations[i] - opt.transition_seconds

    filter_complex = ";".join(filter_parts)

    cmd = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        v_label,
        "-map",
        a_label,
        "-r",
        f"{timeline.fps}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "fast",
        "-crf",
        str(opt.crf),
        "-b:v",
        opt.video_bitrate,
        "-c:a",
        "aac",
        "-b:a",
        opt.audio_bitrate,
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _burn_subtitles(
    src: Path,
    srt: Path,
    output: Path,
    timeline: Timeline,
    ffmpeg_bin: str,
) -> None:
    """Burn an .srt into the video using the subtitles filter."""
    style = _ass_style_for_mode(timeline)
    # ffmpeg subtitles filter requires Windows path massaging in filtergraph
    srt_for_filter = str(srt).replace("\\", "/").replace(":", r"\:")
    vf = f"subtitles='{srt_for_filter}':force_style='{style}'"
    cmd = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-c:a",
        "copy",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _mix_bgm(
    src: Path,
    bgm: Path,
    output: Path,
    opt: RenderOptions,
    ffmpeg_bin: str,
) -> None:
    """Mix BGM track under the main audio.

    Re-encodes video with -c:v copy when possible; falls back to libx264 if
    the source stream isn't compatible (e.g. came from xfade filter pipe).
    """
    base = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-stream_loop",
        "-1",
        "-i",
        str(bgm),
        "-filter_complex",
        (
            f"[1:a]volume={opt.bgm_volume}[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[a]"
        ),
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:a",
        "aac",
        "-b:a",
        opt.audio_bitrate,
        "-shortest",
        str(output),
    ]
    # Try -c:v copy first (fast).
    copy_cmd = base[:-1] + ["-c:v", "copy", str(output)]
    result = subprocess.run(copy_cmd, capture_output=True)
    if result.returncode == 0:
        return
    # Fallback: re-encode video.
    reenc_cmd = base[:-1] + [
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "fast",
        "-crf",
        str(opt.crf),
        str(output),
    ]
    subprocess.run(reenc_cmd, check=True, capture_output=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_duration(stderr_text: str) -> float | None:
    """Extract Duration: HH:MM:SS.xx seconds from ffmpeg -i stderr."""
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_text)
    if not m:
        return None
    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mi * 60 + s


def _ass_style_for_mode(timeline: Timeline) -> str:
    """Pick an ASS force_style string based on the timeline's subtitle preset."""
    sub_track = next((t for t in timeline.tracks if t.kind == "subtitle"), None)
    style = sub_track.subtitle_style if sub_track else None

    if style is None or timeline.mode == "vlog":
        # vlog: bottom-centered, smaller
        return (
            "FontName=Malgun Gothic,FontSize=24,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=40"
        )
    # shorts: center, larger, accented
    return (
        "FontName=Malgun Gothic,FontSize=42,"
        "PrimaryColour=&H0000D4FF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=4,Shadow=0,Alignment=5"
    )
