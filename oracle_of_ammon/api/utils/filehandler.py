import logging
import os
import pathlib

import pandas as pd

from oracle_of_ammon.utils.logger import configure_logger


logger: logging.Logger = configure_logger()


class FileHandler:
    def load_dataframe():
        pass

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
            logger.error(f"Unable to convert XLSX files to DataFrame: {e}")

    def read_text() -> pd.DataFrame:
        pass

    def read_tsv() -> pd.DataFrame:
        pass

    def read_json() -> pd.DataFrame:
        pass

    def read_squad() -> pd.DataFrame:
        pass
