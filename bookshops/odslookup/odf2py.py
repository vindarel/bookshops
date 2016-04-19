#!/bin/env python
# -*- coding: utf-8 -*-

import sys
from json import dumps

import odf.opendocument
from odf.table import *
from odf.text import P


def translateHeader(tag, base_lang="frFR", to="enEN"):
    """The ods file will be in whatever language possible and the data
    retrieved from the scrapers are dictionnaries with english field
    names. We need the same in both.

    takes a tag and returns its translation (english by default).
    """
    def cleanText(tag):
        return tag.strip().strip(":")

    if base_lang == "frFR":
        if cleanText(tag.upper()) in ["TITRE",]:
            return "title"
        elif tag.upper() in ["PRIX",]:
            return "price"
        elif cleanText(tag.upper()) in ["AUTEUR",]:
            return "authors"  # mind the plurial
        elif cleanText(tag) in ["EDITEUR", "ÉDITEUR", u"\xe9diteur"]: # warning utf8 !
            return "publisher"
        else:
            # print "translation to finish for ", tag
            return tag
    else:
        print "todo: others header translations"

    return tag

class ODSReader(object):

    """Read an ods file (OpenDocumentSheet) and provide functions to get the content.

    usage:
    >> doc = ODSReader("file.ods")
    >> doc.read()
    >> # access the data:
    >> doc.sheets
    >> doc.data(sheet=0, json=True)  # get the first sheet in json
    """

    def __init__(self, odsfile):
        """
        """
        self.doc = odf.opendocument.load(odsfile)
        self.sheets = []        # list of dict(name, data)
        # TODO: we want json

    def read(self):
        """Read all the sheets.
        """
        for sheet in self.doc.spreadsheet.getElementsByType(Table):
            self.readSheet(sheet)

    def readSheet(self, sheet):
        """Read a sheet, store the values in a Sheet object.
        """
        name = sheet.getAttribute("name")
        rows = sheet.getElementsByType(TableRow)
        self.sheets.append({"sheet": name, "rows": self.readRows(rows)})

    def readRows(self, rows):
        """Read rows' cells. The first row is the title of each column. A
        column without title won't get exported.

        """
        datarows = []
        ignored_rows = []
        is_first_line = True
        first_line = []
        for row in rows:
            datacells = []
            # cells = row.getElementsByType(TableCell)
            cells = row.childNodes

            for cell in cells:
                textContent = self.readCell(cell)
                # if textContent.startswith("Clio"):
                datacells.append(textContent)

            if len(datacells):
                if is_first_line:
                    # clean up all occurences of "" (have often one in the end)
                    # first_line = filter(lambda x: x != "", datacells)
                    first_line = datacells
                    if first_line[-1] == "":
                        first_line = first_line[:-1]
                    is_first_line = False
                else:
                    # a row with data to look for has the same amount
                    # of information than the line defining the
                    # headlines.
                    if datacells[-1] == "":
                        # not good... a row must end with a value.
                        datacells = datacells[:-1]
                    if len(datacells) == len(first_line):
                        # get a dict {"author": "foo", "title": "bar", etc}
                        new_row = {translateHeader(first_line[ind]): datacells[ind] for ind in range(len(first_line))}
                        datarows.append(new_row)
                    else:
                        if datacells not in [ [""], ["", ""], [] ]:
                            print "the following row was ignored because shorter:", datacells
                            ignored_rows.append(datacells)

        return datarows

    def readCell(self, cell):
        """read a cell.
        return the text."""
        textContent = ""
        # repeated value?
        # repeat_count = cell.getAttribute("numbercolumnsrepeated") if not None else "1"
        ps = cell.getElementsByType(P)

        # for each text node
        for p in ps:
            for n in p.childNodes:
                if (n.nodeType == 3):
                    textContent = textContent + unicode(n.data)
        # if textContent.startswith("5"):

        # if(textContent):
            # if not textContent.startswith("#"): # ignore comments cells
                # textContent = textContent * int(repeat_count)
            # else:
                # print "row is commented: ", textContent

        return textContent

    def nbSheets(self):
        """return the nb of sheets in the document.
        """
        return len(self.sheets.keys())

    def data(self, sheet="all", json=False):
        if sheet == "all":
            return self.sheets
        else:
            data = self.sheets[sheet]["rows"]
            print "nb rows found: ", len(data)
            if json:
                return dumps(data, indent=4)
            return data


def main():
    if len(sys.argv) > 1:
        odsfile = sys.argv[1]
        doc = ODSReader(odsfile)
        doc.read()
        data = doc.data(sheet=0, json=True)
        print "json data from %s:\n" % odsfile
        print "\n".join([l.rstrip() for l in data.splitlines()])
    else:
        print "Usage: odf2py.py file.ods"

if __name__ == '__main__':
    exit(main())
