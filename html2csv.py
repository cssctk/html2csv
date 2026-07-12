#!/usr/bin/env python3

import argparse
import codecs
import csv
import html
import os
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


def parse_tables_from_stream(stream, encoding="utf-8", errors="replace", chunk_size=65536):
    parser = TableHTMLParser()
    reader = codecs.getreader(encoding)(stream, errors=errors)
    while True:
        chunk = reader.read(chunk_size)
        if not chunk:
            break
        parser.feed(chunk)
    parser.close()
    return [table["rows"] for table in parser.tables if table["rows"]]


def write_csv(rows, output_file):
    writer = csv.writer(output_file, delimiter=",", lineterminator="\n")
    for row in rows:
        writer.writerow(row)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert HTML <table> to CSV.",
        add_help=True,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Path to the HTML file, or '-' to read from stdin.",
    )
    parser.add_argument(
        "-c",
        "--charset",
        default="utf-8",
        help="Source HTML character set. Defaults to utf-8.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    script_name = os.path.basename(__file__)

    if args.input is None:
        print("No input provided. Usage:", file=sys.stderr)
        print(f"  python {script_name} input.html", file=sys.stderr)
        sys.exit(1)

    if args.input == "-":
        stream = sys.stdin.buffer if hasattr(sys.stdin, "buffer") else sys.stdin
        tables = parse_tables_from_stream(stream, encoding=args.charset)
        default_output = None
    else:
        with open(args.input, "rb") as f:
            tables = parse_tables_from_stream(f, encoding=args.charset)
        default_output = args.input.rsplit(".", 1)[0] + ".csv" if "." in args.input else args.input + ".csv"

    if not tables:
        print("No <table> elements found in input.", file=sys.stderr)
        sys.exit(1)

    if args.input == "-":
        if len(tables) > 1:
            for idx, table in enumerate(tables, start=1):
                if idx > 1:
                    print(file=sys.stdout)
                print(f"# Table {idx}", file=sys.stdout)
                write_csv(table, sys.stdout)
        else:
            write_csv(tables[0], sys.stdout)
        return

    if len(tables) > 1:
        base, ext = default_output.rsplit(".", 1) if "." in default_output else (default_output, "")
        for idx, table in enumerate(tables, start=1):
            suffix = f"{idx:02d}"
            if ext:
                path = f"{base}-{suffix}.{ext}"
            else:
                path = f"{base}-{suffix}"
            with open(path, "w", encoding=args.charset, newline="") as f:
                write_csv(table, f)
        return

    with open(default_output, "w", encoding=args.charset, newline="") as f:
        write_csv(tables[0], f)


if __name__ == "__main__":
    main()
