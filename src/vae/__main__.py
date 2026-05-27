"""CLI entry point."""

from __future__ import annotations

from pathlib import Path

import click

from vae.analyzers.stt import words_to_subtitles
from vae.pipeline.orchestrator import run_pipeline
from vae.writers.capcut import write_draft
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
def run(
    mode: str,
    input_dir: Path,
    output_dir: Path,
    stt: bool,
    whisper_model: str,
) -> None:
    """Run the auto-edit pipeline over a folder of clips."""
    transcribe_fn = None
    if stt:
        from vae.analyzers.stt import transcribe as _transcribe

        def transcribe_fn(p: Path):
            return _transcribe(p, model_size=whisper_model)

    click.echo(f"[vae] mode={mode}  input={input_dir}  output={output_dir}")
    ctx, timeline = run_pipeline(mode, input_dir, transcribe_fn=transcribe_fn)
    click.echo(f"[vae] analyzed {len(ctx.clips)} clip(s)")
    click.echo(f"[vae] timeline duration: {timeline.duration:.2f}s")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = write_report(ctx, timeline, output_dir / "analysis_report.json")
    draft_path = write_draft(timeline, output_dir / "capcut_project")
    click.echo(f"[vae] wrote {report_path.relative_to(output_dir)}")
    click.echo(f"[vae] wrote {draft_path.relative_to(output_dir)}")

    if stt:
        subs_by_clip = {p: words_to_subtitles(w) for p, w in ctx.speech_words.items()}
        all_subs = [s for subs in subs_by_clip.values() for s in subs]
        srt_path = write_srt(all_subs, output_dir / "subtitles.srt")
        click.echo(f"[vae] wrote {srt_path.relative_to(output_dir)}  ({len(all_subs)} subs)")


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
