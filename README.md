# html2csv

html2csv converts HTML tables into CSV files.

## Features

- Parses HTML tables from a file or from stdin
- Supports source HTML character sets via `-c/--charset`
- Reads the source HTML using the requested source encoding
- Writes CSV output as UTF-8
- Creates a folder next to the source HTML using the source filename stem, and writes CSV files into it
- Writes one CSV file per table, named `table-01.csv`, `table-02.csv`, and so on

## Usage

```bash
python html2csv.py input.html
```

This creates a folder named after the source file stem (for example, `input`) in the same directory as the source HTML, and writes CSV files into it.

For a single table, the output file is:

```text
input/table-01.csv
```

If the HTML contains multiple tables, the script writes multiple files such as:

```text
input/table-01.csv
input/table-02.csv
```

### Read from stdin

When the input is `-`, the script reads from standard input and writes CSV to standard output.

```bash
cat input.html | python html2csv.py -

python html2csv.py - < sample.html
```

If multiple tables are found, the output is written as separate CSV blocks with a `# Table N` header.

### Specify source charset

```bash
python html2csv.py -c gb2312 input.html
```

### Show usage

```bash
python html2csv.py
```

## Requirements

- Python 3

## Example

Given an HTML file containing a table:

```html
<table>
  <tr><th>Name</th><th>Age</th></tr>
  <tr><td>Alice</td><td>30</td></tr>
</table>
```

Running:

```bash
python html2csv.py sample.html
```

produces a UTF-8 CSV file at:

```text
sample/table-01.csv
```

with content similar to:

```csv
Name,Age
Alice,30
```
