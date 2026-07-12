# html2csv

html2csv converts HTML tables into CSV files.

## Features

- Parses HTML tables from a file or from stdin
- Supports source HTML character sets via `-c/--charset`
- Writes CSV output using the same character set as the source HTML
- Writes one CSV file per table when multiple tables are found
- Uses the input filename as the default output basename, replacing the extension with `.csv`

## Usage

```bash
python html2csv.py input.html
```

This creates a file named like `input.csv`.

If the HTML contains multiple tables, the script writes multiple files with numeric suffixes such as:

```text
input-01.csv
input-02.csv
```

### Read from stdin

```bash
cat input.html | python html2csv.py -
```

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

produces a CSV file similar to:

```csv
Name,Age
Alice,30
```
