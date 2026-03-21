from ofxstatement.parser import StatementParser
from ofxstatement.plugin import Plugin

from ofxstatement_rs_altabanka.pdf_parser import RsAltabankaPdfParser
from ofxstatement_rs_altabanka.xml_parser import RsAltabankaXmlParser


class RsAltabankaPlugin(Plugin):
    """Plugin for parsing AltaBanka statements"""

    def get_parser(self, filename: str) -> "StatementParser":
        if filename.endswith(".xml"):
            return RsAltabankaXmlParser(filename)
        if filename.endswith(".pdf"):
            return RsAltabankaPdfParser(filename)
        raise Exception("Unrecognized file type")
