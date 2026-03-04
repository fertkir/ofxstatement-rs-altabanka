import os
from datetime import datetime
from decimal import Decimal

from ofxstatement.ui import UI

from ofxstatement_rs_altabanka.plugin import RsAltabankaPlugin


def test_sample():
    plugin = RsAltabankaPlugin(UI(), {})
    here = os.path.dirname(__file__)
    sample_filename = os.path.join(here, "resources/sample-statement.xml")

    parser = plugin.get_parser(sample_filename)
    statement = parser.parse()

    assert statement is not None
    assert statement.account_id == "190-0000000000101-01"
    assert statement.currency == "RSD"
    assert statement.start_balance == Decimal("100017.74")
    assert statement.start_date == datetime(2026, 3, 2)
    assert statement.end_balance == Decimal("54787.52")
    assert statement.end_date == datetime(2026, 3, 2)
    assert len(statement.lines) == 7

    txn_1 = statement.lines[0]
    assert txn_1.id == "639845723402358"
    assert txn_1.date == datetime(2026, 3, 2)
    assert txn_1.memo == "Obračunata provizija u iznosu od 370.53 RSD"
    assert txn_1.amount == Decimal("0.00")
    assert txn_1.payee == "ALTA BANKA AD-račun provizije"
    assert txn_1.trntype == "DEBIT"

    txn_2 = statement.lines[1]
    assert txn_2.id == "720934865346235"
    assert txn_2.date == datetime(2026, 3, 2)
    assert txn_2.memo == "DIN. PROTIVVREDNOST ZA :EUR 1000 KURS:115.5"
    assert txn_2.amount == Decimal("115500.00")
    assert txn_2.payee == "ALTA banka a.d. Beograd, Bulevar Zorana Đinđića 121,"
    assert txn_2.trntype == "CREDIT"

    txn_3 = statement.lines[2]
    assert txn_3.id == "732098454734646"
    assert txn_3.date == datetime(2026, 3, 2)
    assert txn_3.memo == "Uplata javnih prihoda izuzev poreza i doprinosa po odbitku"
    assert txn_3.amount == Decimal("120760.00")
    assert txn_3.payee == "Poreska uprava, Save Maškovića 3-5,"
    assert txn_3.trntype == "DEBIT"

    txn_4 = statement.lines[3]
    assert txn_4.id == "978324659823745"
    assert txn_4.date == datetime(2026, 3, 2)
    assert txn_4.memo == "POREZ NA PRIHOD 2026"
    assert txn_4.amount == Decimal("25000.00")
    assert txn_4.payee == "Poreska uprava, Save Maškovića 3-5,"
    assert txn_4.trntype == "DEBIT"

    txn_5 = statement.lines[4]
    assert txn_5.id == "908423758493346"
    assert txn_5.date == datetime(2026, 3, 2)
    assert txn_5.memo == "Accounting services"
    assert txn_5.amount == Decimal("10099.69")
    assert txn_5.payee == "ACCOUNTING SERVICES,"
    assert txn_5.trntype == "DEBIT"

    txn_6 = statement.lines[5]
    assert txn_6.id == "938745924653345"
    assert txn_6.date == datetime(2026, 3, 2)
    assert (
        txn_6.memo
        == "Kartica 0000000000000000    : COMPANY.CO.RS               BEOGRAD"
    )
    assert txn_6.amount == Decimal("4500.00")
    assert txn_6.payee == "ALTA BANKA AD BEOGRAD - DINA BUSSINES CA,"
    assert txn_6.trntype == "DEBIT"

    txn_7 = statement.lines[6]
    assert txn_7.id == "623945693245734"
    assert txn_7.date == datetime(2026, 3, 2)
    assert txn_7.memo == "[AutoProv]Obracun provizije za dan 2026.03.02"
    assert txn_7.amount == Decimal("370.53")
    assert txn_7.payee == "ALTA BANKA AD-račun provizije,"
    assert txn_7.trntype == "DEBIT"
