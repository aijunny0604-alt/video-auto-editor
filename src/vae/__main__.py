"""CLI entry point."""

from __future__ import annotations

from pathlib import Path

import click

from vae.analyzers.stt import words_to_subtitles
from vae.pipeline.orchestrator import run_pipeline
from vae.pipeline.subtitles import words_on_timeline
from vae.utils.bgm import find_bgm
from vae.writers.capcut import write_draft
from vae.writers.renderer import RenderOptions, render_timeline
from vae.writers.report import write_report
from vae.writers.srt import write_srt


@click.group()
def cli() -> None:
    """video-auto-editor — auto cut-editing pipeline."""


@cli.command()
@click.option("--mode", type=click.Choice(["vlog", "shorts"]), required=True)
@click.option(
    "--input",
    "input_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--stt/--no-stt",
    default=False,
    help="Run Whisper STT (slow; requires faster-whisper).",
)
@click.option(
    "--whisper-model",
    default="large-v3",
    help="Whisper model size (tiny/base/small/medium/large-v3).",
)
@click.option(
    "--shorts-count",
    default=3,
    show_default=True,
    help="Number of shorts to extract per clip (shorts mode only).",
)
@click.option(
    "--shorts-length",
    default=30.0,
    show_default=True,
    help="Target length of each short in seconds.",
)
@click.option(
    "--render/--no-render",
    default=True,
    show_default=True,
    help="Render final mp4 via ffmpeg (default). --no-render keeps only JSON/SRT.",
)
@click.option(
    "--bgm",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="BGM audio file. If omitted, auto-detect first audio file in input_dir.",
)
@click.option(
    "--bgm-volume",
    default=0.18,
    show_default=True,
    help="BGM mix level 0.0~1.0.",
)
@click.option(
    "--transition",
    type=click.Choice(["fade", "none"]),
    default="fade",
    show_default=True,
)
def run(
    mode: str,
    input_dir: Path,
    output_dir: Path,
    stt: bool,
    whisper_model: str,
    shorts_count: int,
    shorts_length: float,
    render: bool,
    bgm: Path | None,
    bgm_volume: float,
    transition: str,
) -> None:
    """Run the auto-edit pipeline over a folder of clips."""
    transcribe_fn = None
    if stt:
        from vae.analyzers.stt import transcribe as _transcribe

        def transcribe_fn(p: Path):
            return _transcribe(p, model_size=whisper_model)

    click.echo(f"[vae] mode={mode}  input={input_dir}  output={output_dir}")
    ctx, timelines = run_pipeline(
        mode,
        input_dir,
        transcribe_fn=transcribe_fn,
        shorts_count=shorts_count,
        shorts_length=shorts_length,
    )
    click.echo(f"[vae] analyzed {len(ctx.clips)} clip(s)")
    click.echo(f"[vae] produced {len(timelines)} timeline(s)")

    output_dir.mkdir(parents=True, exist_ok=True)
    bgm_path = bgm or find_bgm(input_dir)
    if bgm_path:
        click.echo(f"[vae] BGM: {bgm_path.name}")

    for i, tl in enumerate(timelines, start=1):
        suffix = "" if len(timelines) == 1 else f"_{i:02d}"
        report_path = write_report(ctx, tl, output_dir / f"analysis_report{suffix}.json")
        draft_path = write_draft(tl, output_dir / f"capcut_project{suffix}")
        click.echo(f"[vae] #{i} duration={tl.duration:.2f}s  -> {draft_path.name}/")
        click.echo(f"[vae]      {report_path.name}")

        if render:
            tl_words = words_on_timeline(tl, ctx.speech_words) if ctx.speech_words else []
            tl_subs = words_to_subtitles(tl_words) if tl_words else []
            opts = RenderOptions(
                burn_subtitles=bool(tl_subs),
                transition=transition,
                bgm_path=bgm_path,
                bgm_volume=bgm_volume,
            )
            out_mp4 = output_dir / f"final{suffix}.mp4"
            try:
                render_timeline(tl, out_mp4, subtitles=tl_subs, options=opts)
                msg = f"[vae]      [render] {out_mp4.name}  ({out_mp4.stat().st_size // 1024}KB)"
                click.echo(msg)
            except Exception as exc:  # noqa: BLE001
                click.echo(f"[vae][!] render failed: {exc}")

    if stt:
        subs_by_clip = {p: words_to_subtitles(w) for p, w in ctx.speech_words.items()}
        all_subs = [s for subs in subs_by_clip.values() for s in subs]
        srt_path = write_srt(all_subs, output_dir / "subtitles.srt")
        click.echo(f"[vae] wrote {srt_path.name}  ({len(all_subs)} subs)")


@cli.command("inspect-draft")
def inspect_draft() -> None:
    """List CapCut draft folders on this machine."""
    from vae.utils.paths import list_capcut_projects

    projects = list_capcut_projects()
    if not projects:
        click.echo("No CapCut projects found (or CapCut not installed).")
        return
    for p in projects[:10]:
        click.echo(str(p))


if __name__ == "__main__":
    cli()
