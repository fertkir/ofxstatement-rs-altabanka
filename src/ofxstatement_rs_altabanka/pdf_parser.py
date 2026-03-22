import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Any, Optional

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


def parse_date(value: str, obj: Optional[object] = None) -> datetime:
    if value is None or value == "":
        raise ValidationError(f"The value is empty, but expected date", obj)
    try:
        return datetime.strptime(value, "%d.%m.%Y")
    except ValueError:
        raise ValidationError(f"Couldn't parse date: {value}", obj)


def _get_or_error(d: dict[Any, Any], key: Any) -> Any:
    value = d.get(key)
    if value is None:
        raise ParseError(0, f'"{key}" not found')
    return value


def build_statement_line(tx_rows: pd.DataFrame):
    first_row = tx_rows.iloc[0]
    second_row = tx_rows.iloc[1]
    first_column_str = re.sub(r"^\d+\.\n", "", "".join(tx_rows.iloc[:, 0].dropna().astype(str)))
    first_column_values = [s.strip() for s in first_column_str.split("/")]

    line = StatementLine(
        id=first_column_values[0],
        date=parse_date(first_row.iloc[1]),
        memo=first_column_str,
    )

    line.date_user = parse_date(first_row.iloc[2])
    line.payee = first_column_values[3]

    debit = parse_amount(second_row.iloc[3])
    credit = parse_amount(second_row.iloc[4])

    if credit is None or credit == Decimal(0):
        line.trntype = "DEBIT"
        line.amount = -debit
    elif debit is None or debit == Decimal(0):
        line.trntype = "CREDIT"
        line.amount = credit
    else:
        raise ValidationError("Couldn't find amount", line)

    return line


def df_to_statement_lines(df: pd.DataFrame, transaction_starts: list[int]):
    # split into chunks
    transactions = []
    for idx, start in enumerate(transaction_starts):
        end = transaction_starts[idx + 1] if idx + 1 < len(transaction_starts) else len(df)
        transactions.append(df.iloc[start:end])

    # build objects
    result = [build_statement_line(tx) for tx in transactions]

    return result


def _parse_currency(value: str) -> str:
    match = re.search(r"\b[A-Z]{3}\b", value)
    if match is None:
        raise ParseError(0, f"Couldn't parse currency: {value}")
    return match.group()


@dataclass
class Structure:
    transaction_start_row_ids: list[int]
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
            currency=_parse_currency(_get_or_error(header, "Valuta:")),
        )
        statement.start_date = parse_date(_get_or_error(header, "Datum izrade izvoda:"), header)
        statement.start_balance = structure.start_balance
        statement.end_date = statement.start_date
        statement.end_balance = structure.end_balance
        statement.lines = df_to_statement_lines(tables[1].df, structure.transaction_start_row_ids)
        return statement

    @staticmethod
    def _get_header(df: pd.DataFrame) -> dict[str, str]:
        return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))

    @staticmethod
    def __get_stmt_structure(df: pd.DataFrame) -> Structure:
        transaction_start_row_ids = []
        start_balance = None
        end_balance = None

        for i in range(len(df)):
            row = df.iloc[i]
            if start_balance is None and re.match(r"^Prethodni saldo u valuti", str(row.iloc[1])):
                start_balance = parse_amount(str(row.iloc[4]))
            elif re.match(r"\d+\.\n", str(row.iloc[0])):
                transaction_start_row_ids.append(int(i))
            elif end_balance is None and re.match(r"^Novi saldo u valuti", str(row.iloc[1])):
                end_balance = parse_amount(str(row.iloc[4]))

        if start_balance is None:
            raise ValidationError("Couldn't parse start balance", None)
        if end_balance is None:
            raise ValidationError("Couldn't parse end balance", None)

        return Structure(
            transaction_start_row_ids=transaction_start_row_ids,
            start_balance=start_balance,
            end_balance=end_balance,
        )

    def read_pdf(self) -> TableList:
        return camelot.read_pdf(
            self.filename,
            flavor="stream",
            table_areas=["10,610,250,680", "10,10,600,600"],
            columns=["110", "190,300,410,510"],
            split_text=True,
        )

    def split_records(self) -> Iterable[str]:
        """Return iterable object consisting of a line per transaction"""
        return []

    def parse_record(self, line: str) -> StatementLine:
        """Parse given transaction line and return StatementLine object"""
        return StatementLine()
