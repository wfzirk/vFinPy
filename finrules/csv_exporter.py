# finrules/csv_exporter.py

import csv
from logging_manager import get_logger
log = get_logger(__name__)

def export_transactions_csv(
    filename,
    transactions,
    account_info=None,
    columns=None,
):
    """
    Export transactions to CSV.

    Parameters
    ----------
    filename : str
    transactions : list[dict]
    account_info : dict | None
    columns : list[str] | None
    """

    account_info = account_info or {}

    if columns is None:
        columns = [
            "date",
            "amount",
            "description",
            "fitid",
            "type",
            "number",
        ]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        # Account metadata

        for key, value in account_info.items():
            if value:
                f.write(f"# {key}: {value}\n")

        if account_info:
            f.write("\n")

        writer = csv.DictWriter(
            f,
            fieldnames=columns,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(transactions)