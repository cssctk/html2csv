#!/usr/bin/env python3
"""Convert HTML table(s) to CSV.

Usage examples:
  python html2csv.py input.html > output.csv
  python html2csv.py -i input.html -o output.csv
  python html2csv.py -o out-{i}.csv input.html
  python html2csv.py --table 2 input.html
"""
import argparse
import csv
import html
import sys
from html.parser import HTMLParser


class TableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._table_stack = []
        self._row_stack = []
        self._cell_stack = []
        self._text_parts = []
        self._inside_cell = False
        self._inside_table = False
        self._table_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._inside_table = True
                self._start_table()
        elif self._inside_table and tag == "tr" and self._table_depth == 1:
            self._start_row()
        elif self._inside_table and tag in ("td", "th") and self._table_depth == 1:
            self._start_cell()
        elif self._inside_cell and tag == "br":
            self._append_text("\n")

    def handle_endtag(self, tag):
        if tag == "table":
            if self._table_depth == 1:
                self._end_table()
                self._inside_table = False
            self._table_depth = max(self._table_depth - 1, 0)
        elif self._inside_table and tag == "tr" and self._table_depth == 1:
            self._end_row()
        elif self._inside_table and tag in ("td", "th") and self._table_depth == 1:
            self._end_cell()

    def handle_data(self, data):
        if self._inside_cell:
            self._append_text(data)

    def handle_entityref(self, name):
        if self._inside_cell:
            self._append_text(html.unescape(f"&{name};"))

    def handle_charref(self, name):
        if self._inside_cell:
            self._append_text(html.unescape(f"&#{name};"))

    def _start_table(self):
        table = {"rows": []}
        self.tables.append(table)
        self._table_stack.append(table)

    def _end_table(self):
        if self._row_stack:
            self._end_row()
        self._table_stack.pop()

    def _start_row(self):
        self._row_stack.append([])

    def _end_row(self):
        if self._row_stack:
            row = self._row_stack.pop()
            if self._table_stack:
                self._table_stack[-1]["rows"].append(row)

    def _start_cell(self):
        self._inside_cell = True
        self._text_parts = []
        self._cell_stack.append(True)

    def _end_cell(self):
        if self._cell_stack:
            self._cell_stack.pop()
        text = "".join(self._text_parts).strip()
        row = self._row_stack[-1] if self._row_stack else None
        if row is not None:
            row.append(text)
        self._text_parts = []
        self._inside_cell = bool(self._cell_stack)

    def _append_text(self, text):
        self._text_parts.append(text)


def parse_tables(html_text):
    parser = TableHTMLParser()
    parser.feed(html_text)
    parser.close()
    return [table["rows"] for table in parser.tables if table["rows"]]


def write_csv(rows, output_file, delimiter):
    writer = csv.writer(output_file, delimiter=delimiter, lineterminator="\n")
    for row in rows:
        writer.writerow(row)


def parse_args():
    parser = argparse.ArgumentParser(description="Convert HTML <table> to CSV.")
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Path to the HTML file, or '-' to read from stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output CSV path, '-' for stdout. Use '{i}' to write multiple tables to separate files.",
    )
    parser.add_argument(
        "-t",
        "--table",
        type=int,
        default=None,
        help="Select a specific table by 1-based index when multiple tables exist.",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help="CSV delimiter character. Defaults to ','.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Input/output encoding. Defaults to utf-8.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.input == "-":
        html_text = sys.stdin.read()
    else:
        with open(args.input, "r", encoding=args.encoding, errors="replace") as f:
            html_text = f.read()

    tables = parse_tables(html_text)
    if not tables:
        print("No <table> elements found in input.", file=sys.stderr)
        sys.exit(1)

    if args.table is not None:
        index = args.table - 1
        if not 0 <= index < len(tables):
            print(
                f"Table index {args.table} is out of range. {len(tables)} table(s) found.",
                file=sys.stderr,
            )
            sys.exit(2)
        tables = [tables[index]]

    if args.output == "-":
        if len(tables) > 1:
            for idx, table in enumerate(tables, start=1):
                if idx > 1:
                    print(file=sys.stdout)
                print(f"# Table {idx}", file=sys.stdout)
                write_csv(table, sys.stdout, args.delimiter)
        else:
            write_csv(tables[0], sys.stdout, args.delimiter)
        return

    if len(tables) > 1:
        if "{i}" in args.output:
            for idx, table in enumerate(tables, start=1):
                path = args.output.format(i=idx)
                with open(path, "w", encoding=args.encoding, newline="") as f:
                    write_csv(table, f, args.delimiter)
            return
        print(
            "Multiple tables found. Specify --table N or use an output template containing '{i}' to write separate files.",
            file=sys.stderr,
        )
        sys.exit(3)

    with open(args.output, "w", encoding=args.encoding, newline="") as f:
        write_csv(tables[0], f, args.delimiter)


if __name__ == "__main__":
    main()
