import json
import logging
import os
import pathlib
from tempfile import SpooledTemporaryFile, tempdir

import pandas as pd

from oracle_of_ammon.utils.logger import configure_logger


logger: logging.Logger = configure_logger()


class FileHandler:
    @classmethod
    def file_clean_up(cls, path: str) -> None:
        try:
            if (os.path.exists(path=path)) and (tempdir in path):
                os.unlink(path=path)
            else:
                return
        except Exception as e:
            logger.error(f"Unable to delete file: {e}")

    @classmethod
    def read_data(
        cls, filepath_of_buffer: SpooledTemporaryFile | str, filename: str | None = None
    ):
        try:
            if isinstance(filepath_of_buffer, SpooledTemporaryFile):
                try:
                    path = os.path.join(tempdir, filename)
                    logger.debug(path)
                    with open(file=path, mode="wb") as f:
                        f.write(filepath_of_buffer.read())
                except Exception as e:
                    logger.error(f"Unable to write to temporary file: {e}")
            else:
                path = filepath_of_buffer

            if path.endswith(".csv"):
                return cls.read_csv(path=path)
            if path.endswith(".xlsx"):
                return cls.read_excel(path=path)
            if path.endswith(".txt"):
                return cls.read_text(path=path)
            if path.endswith(".tsv"):
                return cls.read_tsv(path=path)
            if path.endswith(".json"):
                return cls.read_json(path=path)
            else:
                logger.error("This filetype is not currently supported.")
        except Exception as e:
            logger.error(f"Unable to read file: {e}")

    @classmethod
    def read_csv(cls, path: str | pathlib.Path) -> pd.DataFrame:
        try:
            return pd.read_csv(filepath_or_buffer=path)
        except Exception as e:
            logger.error(f"Unable to convert CSV to DataFrame: {e}")
        finally:
            cls.file_clean_up(path=path)

    @classmethod
    def read_excel(
        cls,
        path: str | pathlib.Path,
        sheet_name: str | None = os.environ.get("SHEET_NAME", None),
        merge_sheets: bool = os.environ.get("MERGE_SHEETS", True),
    ) -> pd.DataFrame | dict[pd.DataFrame]:
        try:
            xls = pd.ExcelFile(path_or_buffer=path, engine="openpyxl")
            df: pd.DataFrame | dict[pd.DataFrame] = xls.parse(sheet_name=sheet_name)
            if not merge_sheets:
                return df
            else:
                if len(xls.sheet_names) <= 1:
                    logger.debug("Only 1 sheet was provided. Skipping merge.")
                    df: pd.DataFrame
                    return df
                else:
                    logger.debug("Merging DataFrames...")
                    combined: pd.DataFrame = pd.concat(
                        objs=df, axis=0, ignore_index=True
                    )
                    return combined

        except Exception as e:
            logger.error(f"Unable to convert XLSX file to DataFrame: {e}")
        finally:
            cls.file_clean_up(path=path)

    @classmethod
    def read_text(cls, path: str | pathlib.Path) -> pd.DataFrame:
        questions: list = []
        answers: list = []
        try:
            with open(path, "r") as f:
                for idx, line in enumerate(f):
                    if not idx == 0:
                        parsed = [word.strip() for word in line.split("|")]
                        questions.append(parsed[0])
                        answers.append(parsed[1])
            return pd.DataFrame(
                data=zip(questions, answers), columns=["question", "answer"]
            )
        except Exception as e:
            logger.error(f"Unable to convert text file to DataFrame: {e}")
        finally:
            cls.file_clean_up(path=path)

    @classmethod
    def read_tsv(cls, path: str | pathlib.Path) -> pd.DataFrame:
        try:
            return pd.read_csv(filepath_or_buffer=path, sep="\t")
        except Exception as e:
            logger.error(f"Unable to convert CSV to DataFrame: {e}")
        finally:
            cls.file_clean_up(path=path)

    @classmethod
    def read_json(cls, path: str | pathlib.Path) -> pd.DataFrame:
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Unable to load JSON file: {e}")

        try:
            if not isinstance(data, list):
                raise TypeError(
                    "Data should consist of a list of dictionaries. No list found."
                )
            else:
                questions: list = []
                answers: list = []
                for element in data:
                    element: dict
                    questions.append(element.get("question"))
                    answers.append(element.get("answer"))

            return pd.DataFrame(
                data=zip(questions, answers), columns=["question", "answer"]
            )
        except Exception as e:
            logger.error(f"Unable to convert JSON to DataFrame: {e}")
        finally:
            cls.file_clean_up(path=path)
