import os
import subprocess  # nosec
from typing import Union

import typer

from oracle_of_ammon.common.logger import logger

app = typer.Typer(help="Oracle of Ammon")


@app.command()
def run(
    path: Union[str, None] = typer.Option(
        default=None, help="Filepath of CSV used to pre-index document store."
    )
) -> None:
    """
    Ammon was orginally a Libyan deity. His oracle, located in the Siwa oasis, became known by the Egyptians as "Amun of Siwa" -- Lord of Good Counsel.
    The oracle became famous after Alexander the Great made a detour to consult the god. May Ammon help you find what you seek...
    """

    if path is not None:
        os.environ["OASIS_OF_SIWA"] = path

    logger.debug("Summoning Ammon 🔮")
    subprocess.call(  # nosec
        ["python3", "-m", "oracle_of_ammon.api.ammon"],
        env=os.environ,
        shell=False,  # nosec
    )
