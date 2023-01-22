import json
import logging
import os
import pathlib
from tempfile import SpooledTemporaryFile, tempdir

import pandas as pd
from haystack import Document
from haystack.nodes import PreProcessor

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
    def read_documents(
        cls,
        preprocessor: PreProcessor,
        filepath_or_buffer: SpooledTemporaryFile | str,
        filename: str | None = None,
        **kwargs,
    ) -> list[Document]:
        try:
            if isinstance(filepath_or_buffer, SpooledTemporaryFile):
                try:
                    path = os.path.join(tempdir, filename)
                    logger.debug(path)
                    with open(file=path, mode="wb") as f:
                        f: SpooledTemporaryFile
                        f.write(filepath_or_buffer.read())
                except Exception as e:
                    logger.error(f"Unable to write to temporary file: {e}")
            else:
                path = filepath_or_buffer

            try:
                with open(file=path, mode="r") as f:
                    content = f.read()
                logger.debug(content)

                meta: dict = {
                    "filepath_of_buffer": filepath_or_buffer,
                    "filename": filename,
                }

                doc: Document = preprocessor.process(
                    Document(content=content, meta=meta)
                )

                return doc

            except Exception as e:
                logger.error(f"Unable to read from file: {e}")

        except Exception as e:
            logger.error(f"Unable to read file: {e}")

    @classmethod
    def read_faq(
        cls,
        filepath_or_buffer: SpooledTemporaryFile | str,
        filename: str | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        try:
            if isinstance(filepath_or_buffer, SpooledTemporaryFile):
                try:
                    path = os.path.join(tempdir, filename)
                    logger.debug(path)
                    with open(file=path, mode="wb") as f:
                        f: SpooledTemporaryFile
                        f.write(filepath_or_buffer.read())
                except Exception as e:
                    logger.error(f"Unable to write to temporary file: {e}")
            else:
                path = filepath_or_buffer

            if path.endswith(".csv"):
                return cls.read_csv(path=path)
            if path.endswith(".xlsx"):
                return cls.read_excel(path=path, sheet_name=kwargs.get("sheet_name"))
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
        cls, path: str | pathlib.Path, sheet_name: list[str] | None = None
    ) -> pd.DataFrame:
        try:
            xls = pd.ExcelFile(path_or_buffer=path, engine="openpyxl")
            df: dict[pd.DataFrame] = xls.parse(sheet_name=sheet_name)

            if len(df.keys()) == 1:
                return list(df.values())[0]

            else:
                logger.debug("Merging DataFrames...")
                combined: pd.DataFrame = pd.concat(objs=df, axis=0, ignore_index=True)
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
            logger.error(f"Unable to convert TSV to DataFrame: {e}")
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