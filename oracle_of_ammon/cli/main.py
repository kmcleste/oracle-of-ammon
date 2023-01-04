import os
import pathlib
import subprocess  # nosec
import sys
from typing import Union

import typer

sys.path.append(
    str(
        pathlib.Path(
            pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent, "common"
        )
    )
)
from logger import logger

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
        "oracle_of_ammon/api/Ammon.py", env=os.environ, shell=False  # nosec
    )
