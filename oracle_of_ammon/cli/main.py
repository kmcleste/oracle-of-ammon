import logging
import os
import pathlib
import subprocess  # nosec
from typing import Union

import typer

from oracle_of_ammon.utils.logger import configure_logger

logger: logging.Logger = configure_logger()

description = """
    Oracle of Ammon

    Ammon was orginally a Libyan deity. His oracle, located in the Siwa oasis, became known by the Egyptians as "Amun of Siwa" -- Lord of Good Counsel.
    The oracle became famous after Alexander the Great made a detour to consult the god. May Ammon help you find what you seek...
"""

app = typer.Typer(help=description)


@app.command()
def summon(
    path: Union[str, None] = typer.Option(
        default=None, help="Filepath of file used to pre-index document store."
    ),
    sheet_name: Union[str, None] = typer.Option(
        default=None,
        help="If using an excel file, select which sheet(s) to load. If none provided, all sheets will be loaded. Expects a comma-separated list.",
    ),
    title: Union[str, None] = typer.Option(
        default=None, help="API documentation title."
    ),
    index: Union[str, None] = typer.Option(
        default=None, help="Default index name to upload documents to."
    ),
    faq: Union[bool, None] = typer.Option(
        default=True, help="Designation for content preloaded into the document store."
    ),
) -> None:
    """
    Summon the Oracle of Ammon. Default port: 8000
    """
    if path is not None:
        os.environ["OASIS_OF_SIWA"] = path
    if sheet_name is not None:
        os.environ["SHEET_NAME"] = sheet_name
    if title is not None:
        os.environ["API_TITLE"] = title
    if index is not None:
        os.environ["INDEX"] = index
    if faq is not None:
        os.environ["IS_FAQ"] = str(faq)

    logger.debug("Summoning Ammon 🔮")
    subprocess.call(
        ["python3", "-m", "oracle_of_ammon.api.ammon"],
        env=os.environ,
        shell=False,
    )


@app.command()
def locust() -> None:
    """
    Stress test your Search API with a swarm of Locusts. Default port: 8089
    """
    logger.debug("Initializing locust...")
    path: str = str(
        pathlib.Path(
            pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent,
            "locust",
            "locust.py",
        )
    )
    subprocess.call(
        ["python3", "-m", "locust", "-f", path],
        env=os.environ,
        shell=False,
    )
