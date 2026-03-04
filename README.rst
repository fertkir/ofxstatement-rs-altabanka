=========================================
ofxstatement-rs-altabanka
=========================================

OFXStatement plugin for AltaBanka (Serbia)

``ofxstatement-rs-altabanka`` is a plugin for ``ofxstatement`` that converts
AltaBanka (Serbia) bank statements to OFX format, suitable for importing to
accounting software like GnuCash.

.. _ofxstatement: https://github.com/kedder/ofxstatement


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
