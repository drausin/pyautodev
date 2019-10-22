import click
from typing import Tuple

from processor import Processor


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, readable=True, allow_dash=True
    ),
    is_eager=True,
)
def main(src: Tuple[str]):
    p = Processor()
    msgs = p.process([str(s) for s in src])
    for m in msgs:
        print(m)


if __name__ == "__main__":
    main()
