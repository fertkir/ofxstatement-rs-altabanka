import xml.etree.ElementTree as ET
from datetime import datetime, date
from decimal import Decimal
from typing import Iterable, Optional

from ofxstatement.parser import StatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, StatementLine


class RsAltabankaPlugin(Plugin):
    """Plugin for parsing AltaBanka statements"""

    def get_parser(self, filename: str) -> "RsAltabankaParser":
        return RsAltabankaParser(filename)


def get_text(element: Optional[ET.Element], tag: str) -> str:
    child = element.find(tag) if element is not None else None
    return child.text.strip() if child is not None and child.text else ""


def get_decimal(element: Optional[ET.Element], tag: str) -> Decimal:
    text = get_text(element, tag)
    return Decimal(text) if text else Decimal("0.0")


def get_date(element: Optional[ET.Element], tag: str) -> Optional[date]:
    text = get_text(element, tag)
    if not text:
        return None
    return datetime.strptime(text[:10], "%Y-%m-%d").date()


class RsAltabankaParser(StatementParser[str]):
    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename

    def parse(self) -> Statement:
        tree = ET.parse(self.filename)
        root = tree.getroot()

        statement = Statement(
            account_id=get_text(root, "acctid"),
            currency=get_text(root, "curdef")
        )

        ledgerbal = root.find("ledgerbal")
        statement.start_date = get_date(ledgerbal, "dtasof")
        statement.start_balance = get_decimal(ledgerbal, "balamt")

        availbal = root.find("availbal")
        statement.end_date = get_date(availbal, "dtasof")
        statement.end_balance = get_decimal(availbal, "balamt")

        trnlist = root.find("trnlist")
        if trnlist is not None:
            statement.lines = [self.__parse_transation(trn) for trn in trnlist.findall("stmttrn")]

        return statement

    @staticmethod
    def __parse_transation(stmttrn: ET.Element) -> StatementLine:
        line = StatementLine(
            id=get_text(stmttrn, "fitid"),
            date=get_date(stmttrn, "dtposted"),
            memo=get_text(stmttrn, "purpose"),
            amount=get_decimal(stmttrn, "trnamt"),
        )

        payeeinfo = stmttrn.find("payeeinfo")
        if payeeinfo is not None:
            line.payee = get_text(payeeinfo, "name")

        refnumber = get_text(stmttrn, "refnumber")
        if refnumber:
            line.refnum = refnumber

        if get_text(stmttrn, "benefit") == "debit":
            line.trntype = "DEBIT"
        elif get_text(stmttrn, "benefit") == "credit":
            line.trntype = "CREDIT"

        return line

    def split_records(self) -> Iterable[str]:
        """Return iterable object consisting of a line per transaction"""
        return []

    def parse_record(self, line: str) -> StatementLine:
        """Parse given transaction line and return StatementLine object"""
        return StatementLine()
