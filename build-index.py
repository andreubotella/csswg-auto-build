import json
import os
import os.path
import re
import sys
from collections import defaultdict

from html.parser import HTMLParser

from bikeshed import Spec, constants


def html_file_for_spec(spec):
    if spec == "css-fonts-3":
        return "Fonts.html"
    return "Overview.html"


def title_from_html(file):
    class HTMLTitleParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_title = False
            self.title = ""
            self.done = False

        def handle_starttag(self, tag, attrs):
            if tag == "title":
                self.in_title = True

        def handle_data(self, data):
            if self.in_title:
                self.title += data

        def handle_endtag(self, tag):
            if tag == "title" and self.in_title:
                self.in_title = False
                self.done = True
                self.reset()

    parser = HTMLTitleParser()
    with open(file, encoding="UTF-8") as f:
        for line in f:
            parser.feed(line)
            if parser.done:
                break
    if not parser.done:
        parser.close()

    return parser.title if parser.done else None


def get_bs_spec_metadata(folder_name, path):
    spec = Spec(path)
    spec.assembleDocument()

    level = int(spec.md.level) if spec.md.level else 0

    if spec.md.shortname == "css-animations-2":
        shortname = "css-animations"
    elif spec.md.shortname == "css-gcpm-4":
        shortname = "css-gcpm"
    elif spec.md.shortname == "css-transitions-2":
        shortname = "css-transitions"
    else:
        # Fix CSS snapshots (e.g. "css-2022")
        snapshot_match = re.match(
            "^css-(20[0-9]{2})$", spec.md.shortname)
        if snapshot_match:
            shortname = "css-snapshot"
            level = int(snapshot_match.group(1))
        else:
            shortname = spec.md.shortname

    return {
        "shortname": shortname,
        "level": level,
        "title": spec.md.title,
        "workStatus": spec.md.workStatus
    }


def get_html_spec_metadata(folder_name, path):
    match = re.match("^([a-z0-9-]+)-([0-9]+)$", entry.name)
    if match and match.group(1) == "css":
        shortname = "css-snapshot"
        title = f"CSS Snapshot {match.group(2)}"
    else:
        shortname = match.group(1) if match else entry.name
        title = title_from_html(html_file)

    return {
        "shortname": shortname,
        "level": int(match.group(2)) if match else 0,
        "title": title,
        "workStatus": "completed"  # It's a good heuristic
    }


CURRENT_WORK_EXCEPTIONS = {
    "css-conditional": 5,
    "css-grid": 2,
    "css-snapshot": None,  # always choose the last spec
    "css-values": 4,
    "css-writing-modes": 4,
    "web-animations": 2
}

# ------------------------------------------------------------------------------


constants.setErrorLevel("nothing")
constants.quiet = float("infinity")

specgroups = defaultdict(list)

for entry in os.scandir("./csswg-drafts"):
    if entry.is_dir():
        # Not actual specs, just examples.
        if entry.name in ["css-module-bikeshed", "css-module"]:
            continue

        bs_file = os.path.join(entry.path, "Overview.bs")
        html_file = os.path.join(entry.path, html_file_for_spec(entry.name))
        if os.path.exists(bs_file):
            metadata = get_bs_spec_metadata(entry.name, bs_file)
        elif os.path.exists(html_file):
            metadata = get_html_spec_metadata(entry.name, html_file)
        else:
            # Not a spec
            continue

        metadata["dir"] = entry.name
        metadata["currentWork"] = False
        specgroups[metadata["shortname"]].append(metadata)

# Reorder the specs with common shortname based on their level (or year, for
# CSS snapshots), and determine which spec is the current work.
for shortname, specgroup in specgroups.items():
    if len(specgroup) > 1:
        specgroup.sort(key=lambda spec: spec["level"])

        # TODO: This algorithm for determining which spec is the current work
        # is wrong in a number of cases. Try and come up with a better
        # algorithm, rather than maintaining a list of exceptions.
        for spec in specgroup:
            if shortname in CURRENT_WORK_EXCEPTIONS:
                if CURRENT_WORK_EXCEPTIONS[shortname] == spec["level"]:
                    spec["currentWork"] = True
                    break
            elif spec["workStatus"] != "completed":
                spec["currentWork"] = True
                break
        else:
            specgroup[-1]["currentWork"] = True

print("""
<!DOCTYPE html>
<meta charset="utf-8">
<title>CSS Working Group Draft Specifications</title>
<style>
    :root {
        color-scheme: light dark;
        --text: black;
        --bg: #f7f8f9;
        --a-normal-text: #034575;
        --a-normal-underline: #707070;

        background-color: var(--bg);
        color: var(--text);
    }
    h1 {
        text-align: center;
    }
    a[href] {
        color: var(--a-normal-text);
        text-decoration-color: var(--a-normal-underline);
        text-decoration-skip-ink: none;
    }
    a[href]:focus, a[href]:hover {
        text-decoration-thickness: 2px;
        text-decoration-skip-ink: none;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --text: #ddd;
            --bg: #080808;
            --a-normal-text: #6af;
            --a-normal-underline: #555;
        }
    }

    li {
        margin-block-start: 1em;
        margin-block-end: 1em;
    }
    li p, li ul, li ul li {
        margin-block-start: 0;
        margin-block-end: 0;
    }
</style>

<h1>CSS Working Group Draft Specifications</h1>
<ul>
""")

for shortname, specgroup in sorted(specgroups.items(), key=lambda x: x[0]):
    if len(specgroup) == 1:
        spec = specgroup[0]
        print(f'  <li><a href="./{spec["dir"]}">{spec["title"]}</a></li>')
    else:
        print('  <li>')
        print(f'    <p>{shortname}</p>')
        print('    <ul>')
        for spec in specgroup:
            paren = " (current work)" if spec["currentWork"] else ""
            print(
                f'      <li><a href="./{spec["dir"]}">{spec["title"]}</a>{paren}</li>')
        print('    </ul>')
        print('  </li>')

print("</ul>")
