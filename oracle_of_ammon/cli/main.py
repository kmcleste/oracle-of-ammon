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
        default=None, help="Path of file used to pre-index document store."
    ),
    sheet_name: Union[str, None] = typer.Option(
        default=None,
        help="If using an excel file, select which sheet(s) to load. If none provided, all sheets will be loaded. Expects a comma-separated list.",
    ),
    title: Union[str, None] = typer.Option(
        default=None, help="API documentation title."
    ),
    index: Union[str, None] = typer.Option(default=None, help="Default index name."),
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


@app.command()
def stream(
    api_url: Union[str, None] = typer.Option(
        default="http://127.0.0.1", help="URL of REST API."
    ),
    api_port: Union[str, None] = typer.Option(default="8000", help="Port of REST API."),
    port: Union[str, None] = typer.Option(default="8501", help="Port of Streamlit UI."),
) -> None:
    """
    Test out your search engine through the Streamlit Web UI. Default port: 8501
    """
    if api_url is not None:
        os.environ["API_URL"] = api_url
    if api_port is not None:
        os.environ["API_PORT"] = api_port

    proc_cmd: list = ["streamlit", "run", "oracle_of_ammon/ui/01_🏠_Home.py"]

    if port is not None:
        proc_cmd: list = [
            "streamlit",
            "run",
            "oracle_of_ammon/ui/01_🏠_Home.py",
            "--server.port",
            port,
        ]

    subprocess.call(proc_cmd, env=os.environ, shell=False)
