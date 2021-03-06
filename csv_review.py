"""CSV review tool."""

import csv
import os.path
import sys
import textwrap

import click
import colorama
from colorama import Fore, Back, Style


def print_row(d):
    print(f"\n\n\n\n\n\n\n\n{Fore.YELLOW}{Style.BRIGHT}{'#'*100}{Style.RESET_ALL}{Fore.RESET}")
    prev_post = ""
    for k, v in d.items():
        v = "\n".join(textwrap.fill(p, width=100) for p in v.splitlines())
        v = v.strip()
        if "\n" in v:
            pre = "\n"
            sep = "\n"
        else:
            pre = ""
            sep = ":\t"

        if v:
            print(f"{prev_post or pre}{Style.BRIGHT}{k}{Style.NORMAL}{sep}{v}")
            prev_post = pre

COMMENTS_FILE = "comments.csv"

def read_comments():
    comments = {}
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE) as f:
            for r in csv.reader(f):
                comments[int(r[0])] = r[1]
    return comments

def write_comments(comments):
    with open(COMMENTS_FILE, "w") as f:
        writer = csv.writer(f, lineterminator="\n")
        for k in sorted(comments):
            writer.writerow((k, comments[k]))

def add_comment(comments, rownum, comment):
    old_comment = comments.get(rownum, '')
    if old_comment:
        old_comment += "\n"
    comment = old_comment + comment
    comments[rownum] = comment.strip()
    write_comments(comments)

class MultiHeadDictReader:
    """A simple DictReader-like thing that can use a few rows for the headers."""
    def __init__(self, csvfile, header=1):
        self.reader = csv.reader(csvfile)
        self.fieldnames = next(self.reader)
        for _ in range(header-1):
            self.fieldnames = [(a + " " + b).strip() for a, b in zip(self.fieldnames, next(self.reader))]

    def __iter__(self):
        for row in self.reader:
            yield dict(zip(self.fieldnames, row))


@click.command()
@click.option('--header', default=1, help="Row number with headers")
@click.argument('csvfile', type=click.File('r'))
def main(header, csvfile):
    colorama.init()

    rows = list(MultiHeadDictReader(csvfile, header=header))

    for _ in range(header):
        rows.insert(0, {})  # Fieldnames
    rows.insert(0, {})  # 1-origin

    print(f"{len(rows)-1} rows, numbered 2-{len(rows)-1}")

    comments = read_comments()

    row = header+1
    last_shown = None

    while True:
        if row != last_shown:
            print_row(rows[row])
            comment = comments.get(row, "")
            if comment:
                print(f"\n{Fore.YELLOW}Comment:{Fore.RESET} {comment}\n")
            last_shown = row

        try:
            # XXX: Workaround `input` not displaying ANSI on Windows
            # https://bugs.python.org/issue17337
            print(f"{Style.BRIGHT}{row}{Style.NORMAL} >> ", end="")
            cmd = input().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break
        if not cmd:
            continue
        elif cmd == "q":
            # Quit.
            break
        elif cmd == "s":
            # Show the row again.
            last_shown = None
        elif cmd == "n":
            # Next row.
            if row >= len(rows)-1:
                print("@end")
            else:
                row += 1
        elif cmd == "p":
            # Previous row.
            if row == 2:
                print("@begin")
            else:
                row -= 1
        elif cmd.startswith("c"):
            # Write a comment.
            comment = cmd.partition(" ")[-1]
            add_comment(comments, row, comment)
        else:
            # A number to jump to.
            try:
                nrow = int(cmd)
            except ValueError:
                print(f"Didn't understand {cmd!r}")
            else:
                if 2 <= nrow <= len(rows)-1:
                    row = nrow
                else:
                    print(f"Rows are numbered {header+1}-{len(rows)-1}")

main()
