import csv
import io

import openpyxl


def parse_uploaded_file(file_bytes: bytes, file_name: str) -> dict:
    """Parse an Excel (.xlsx) or CSV file into a structured dict.

    Returns:
        {
            "file_name": str,
            "sheets": {
                "<sheet_name>": [{"<col>": <value>, ...}, ...]
            }
        }
    """
    if file_name.lower().endswith(".csv"):
        return _parse_csv(file_bytes, file_name)
    return _parse_excel(file_bytes, file_name)


def _parse_excel(file_bytes: bytes, file_name: str) -> dict:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    sheets = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        headers: list[str] | None = None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = [
                    str(c) if c is not None else f"col_{j}"
                    for j, c in enumerate(row)
                ]
            else:
                if any(c is not None for c in row) and headers:
                    rows.append(dict(zip(headers, row)))
        if rows:
            sheets[sheet_name] = rows
    return {"file_name": file_name, "sheets": sheets}


def _parse_csv(file_bytes: bytes, file_name: str) -> dict:
    text = file_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = [dict(row) for row in reader]
    return {"file_name": file_name, "sheets": {"Sheet1": rows}}
