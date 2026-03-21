=========================================
ofxstatement-rs-altabanka
=========================================

.. _ofxstatement: https://github.com/kedder/ofxstatement

OFXStatement plugin for AltaBanka (Serbia)

``ofxstatement-rs-altabanka`` is a plugin for ofxstatement_ that converts
AltaBanka (Serbia) bank statements to OFX format, suitable for importing to
accounting software like GnuCash.


Installation
============

Install from PyPI::

    pip install ofxstatement-rs-altabanka


Usage
=====

After installation, the plugin will be automatically registered with
ofxstatement. Convert a bank statement with::

    ofxstatement convert -t rs-altabanka input.xml output.ofx

List available plugins to confirm installation::

    ofxstatement list-plugins


Development
===========

Clone the repository and install dependencies::

    git clone https://github.com/fertkir/ofxstatement-rs-altabanka
    cd ofxstatement-rs-altabanka
    pip install -e ".[dev]"

Run tests::

    make test

If pdf parser adjustments needed:

.. code-block:: python

    from ofxstatement_rs_altabanka.pdf_parser import RsAltabankaPdfParser
    import os.path

    from matplotlib import pyplot as plt
    import camelot

    plt.rcParams["figure.figsize"] = (20, 15)

    parser = RsAltabankaPdfParser(os.path.expanduser("~/Downloads/1.pdf"))
    tables = parser.read_pdf()
    camelot.plot(tables[0], kind='grid').show()
