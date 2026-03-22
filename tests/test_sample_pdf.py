import os
from datetime import datetime
from decimal import Decimal

import pytest
from ofxstatement.ui import UI

from ofxstatement_rs_altabanka.plugin import RsAltabankaPlugin


@pytest.mark.skip(reason="No sanitized pdf, so keeping the test disabled for development purposes")
def test_sample():
    plugin = RsAltabankaPlugin(UI(), {})
    parser = plugin.get_parser(os.path.expanduser("~/Downloads/1.pdf"))
    statement = parser.parse()

    assert statement is not None
    assert statement.account_id == ""
    assert statement.currency == ""
    assert statement.start_balance == Decimal("")
    assert statement.start_date == datetime(2026, 1, 1)
    assert statement.end_balance == Decimal("")
    assert statement.end_date == datetime(2026, 1, 1)
    assert len(statement.lines) == 2

    txn_1 = statement.lines[0]
    assert txn_1.id == ""
    assert txn_1.date == datetime(2026, 1, 1)
    assert txn_1.memo == ""
    assert txn_1.amount == Decimal("")
    assert txn_1.payee == ""
    assert txn_1.refnum == ""
    assert txn_1.trntype == "DEBIT"

    txn_2 = statement.lines[1]
    assert txn_2.id == ""
    assert txn_2.date == datetime(2026, 1, 1)
    assert txn_2.memo == ""
    assert txn_2.amount == Decimal("")
    assert txn_2.payee == ""
    assert txn_2.refnum == ""
    assert txn_2.trntype == "CREDIT"
