"""CLI entry point. Implementation pending — Phase 3."""

import click


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--mode", type=click.Choice(["vlog", "shorts"]), required=True)
@click.option("--input", "input_dir", type=click.Path(exists=True), required=True)
@click.option("--output", "output_dir", type=click.Path(), required=True)
def run(mode: str, input_dir: str, output_dir: str) -> None:
    raise NotImplementedError("Pipeline implementation pending (Phase 3).")


if __name__ == "__main__":
    cli()
