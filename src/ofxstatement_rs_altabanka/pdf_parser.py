import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Hashable, Any

import camelot
import pandas as pd
from camelot.core import TableList
from ofxstatement.exceptions import ValidationError, ParseError
from ofxstatement.parser import StatementParser
from ofxstatement.statement import Statement, StatementLine


def parse_amount(val):
    if pd.isna(val) or val == "" or val == "0.00":
        return None
    # convert "1,000.00" -> Decimal
    return Decimal(val.replace(",", ""))


def parse_date(value: str, obj: object | None = None) -> datetime:
    if value is None or value == "":
        raise ValidationError(f"The value is empty, but expected date", obj)
    try:
        return datetime.strptime(value, "%d.%m.%Y")
    except ValueError:
        raise ValidationError(f"Couldn't parse date: {value}", obj)


def extract_ref_and_id(text):
    # example: "1.\n0101010101010101 / ref: 232323223232323"
    match = re.search(r"(\d+)\s*/\s*ref:\s*([\w\-]+)", text)
    if match:
        return match.group(1), match.group(2)
    return None, None


def _get_or_error(d: dict[Any, Any], key: Any) -> Any:
    value = d.get(key)
    if value is None:
        raise ParseError(0, f"\"{key}\" not found")
    return value


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


@dataclass
class Structure:
    transaction_start_row_ids: list[Hashable]
    start_balance: Decimal
    end_balance: Decimal


class RsAltabankaPdfParser(StatementParser[str]):
    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename

    def parse(self) -> Statement:
        tables = self.read_pdf()
        if len(tables) != 2:
            raise ParseError(0, f"Expected to parse 2 tables on the pdf, but found {len(tables)}")

        header = self._get_header(tables[0].df)
        structure = self.__get_stmt_structure(tables[1].df)

        statement = Statement(
            account_id=_get_or_error(header, "IBAN:"),
            currency=re.search(r"\b[A-Z]{3}\b", _get_or_error(header, "Valuta:")).group()
        )

        statement.start_date = parse_date(_get_or_error(header, "Datum izrade izvoda:"), header)
        statement.start_balance = structure.start_balance

        statement.end_date = statement.start_date
        statement.end_balance = structure.end_balance

        statement.lines = self.df_to_statement_lines(tables[1].df, structure.transaction_start_row_ids)

        return statement

    @staticmethod
    def _get_header(df: pd.DataFrame) -> dict[str, str]:
        return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))

    @staticmethod
    def __get_stmt_structure(df: pd.DataFrame) -> Structure:
        transaction_start_row_ids = []
        start_balance = None
        end_balance = None

        for i, row in df.iterrows():
            if start_balance is None and re.match(r"^Prethodni saldo u valuti", str(row.iloc[1])):
                start_balance = parse_amount(row.iloc[4])
            elif re.match(r"\d+\.\n", str(row.iloc[0])):
                transaction_start_row_ids.append(i)
            elif end_balance is None and re.match(r"^Novi saldo u valuti", str(row.iloc[1])):
                end_balance = parse_amount(row.iloc[4])

        if start_balance is None:
            raise ValidationError("Couldn't parse start balance", None)
        if end_balance is None:
            raise ValidationError("Couldn't parse end balance", None)

        return Structure(
            transaction_start_row_ids=transaction_start_row_ids,
            start_balance=start_balance,
            end_balance=end_balance
        )

    @staticmethod
    def df_to_statement_lines(df: pd.DataFrame, transaction_starts: list[Hashable]):
        # split into chunks
        transactions = []
        for idx, start in enumerate(transaction_starts):
            end = transaction_starts[idx + 1] if idx + 1 < len(transaction_starts) else len(df)
            transactions.append(df.iloc[start:end])

        # build objects
        result = [build_statement_line(tx) for tx in transactions]

        return result

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
