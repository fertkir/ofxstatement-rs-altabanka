import re
from datetime import datetime
from decimal import Decimal
from typing import Iterable

import camelot
import pandas as pd
from camelot.core import TableList
from ofxstatement.parser import StatementParser
from ofxstatement.statement import Statement, StatementLine


def parse_amount(val):
    if pd.isna(val) or val == "" or val == "0.00":
        return None
    # convert "1,000.00" -> Decimal
    return Decimal(val.replace(",", ""))


def parse_date(val):
    if pd.isna(val) or val == "":
        return None
    return datetime.strptime(val, "%d.%m.%Y")


def extract_ref_and_id(text):
    # example: "1.\n0101010101010101 / ref: 232323223232323"
    match = re.search(r"(\d+)\s*/\s*ref:\s*([\w\-]+)", text)
    if match:
        return match.group(1), match.group(2)
    return None, None


def build_statement_line(tx_rows: pd.DataFrame):
    first_row = tx_rows.iloc[0]

    raw_text = str(first_row.iloc[0])
    txn_id, ref = extract_ref_and_id(raw_text)

    date = parse_date(first_row.iloc[1])
    date_user = parse_date(first_row.iloc[2])

    debit = parse_amount(first_row.iloc[3])
    credit = parse_amount(first_row.iloc[4])

    # debit = negative, credit = positive
    amount = None
    if debit:
        amount = -debit
    elif credit:
        amount = credit

    # collect memo + payee info
    memo_parts = []
    payee = None

    for _, row in tx_rows.iterrows():
        text = str(row.iloc[1]).strip()

        if not text or text == 'nan':
            continue

        # detect payee (heuristic)
        if "/" in text and not payee:
            payee = text

        # ignore noise
        if any(skip in text for skip in ["KURS", "Tiket", "ref:", "KOMITENTA"]):
            continue

        memo_parts.append(text)

    memo = " | ".join(memo_parts)

    line = StatementLine(
        id=txn_id,
        date=date,
        memo=memo,
        amount=amount,
    )

    line.date_user = date_user
    line.payee = payee
    line.refnum = ref

    return line


def df_to_statement_lines(df: pd.DataFrame):
    transaction_starts = []

    # detect transaction start rows
    for i, row in df.iterrows():
        val = str(row.iloc[0])
        if re.match(r"\d+\.\n", val):
            transaction_starts.append(i)

    # split into chunks
    transactions = []
    for idx, start in enumerate(transaction_starts):
        end = transaction_starts[idx + 1] if idx + 1 < len(transaction_starts) else len(df)
        transactions.append(df.iloc[start:end])

    # build objects
    result = [build_statement_line(tx) for tx in transactions]

    return result


class RsAltabankaPdfParser(StatementParser[str]):
    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename

    def parse(self) -> Statement:
        tables = self.read_pdf()
        header = self._get_header(tables)

        statement = Statement(
            account_id=header["IBAN:"], currency=re.search(r"\b[A-Z]{3}\b", header["Valuta:"]).group()
        )

        statement.start_date = parse_date(header["Datum izrade izvoda:"])
        statement.start_balance = Decimal("0.00")

        statement.end_date = statement.start_date
        statement.end_balance = Decimal("1000.00")

        statement.lines = df_to_statement_lines(tables[1].df)

        return statement

    @staticmethod
    def _get_header(tables: TableList) -> dict[str, str]:
        df = tables[0].df
        return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))

    def read_pdf(self) -> TableList:
        return camelot.read_pdf(self.filename,
                                flavor='stream',
                                table_areas=['10,610,250,680', '10,10,600,600'],
                                columns=['110', '190,300,410,510'],
                                split_text=True)

    def split_records(self) -> Iterable[str]:
        """Return iterable object consisting of a line per transaction"""
        return []

    def parse_record(self, line: str) -> StatementLine:
        """Parse given transaction line and return StatementLine object"""
        return StatementLine()
