import os

from ofxstatement.ui import UI

from ofxstatement_rs_altabanka.plugin import RsAltabankaPlugin


def test_sample() -> None:
    plugin = RsAltabankaPlugin(UI(), {})
    here = os.path.dirname(__file__)
    sample_filename = os.path.join(here, "sample-statement.xml")

    parser = plugin.get_parser(sample_filename)
    statement = parser.parse()

    assert statement is not None
