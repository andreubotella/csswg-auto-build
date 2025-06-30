"""Builds the CSSWG directory index.

It also sets up redirects from shortnames to the current work spec, by building
an index.html with a <meta refresh>.
"""

import json
import os
import os.path
import re
import sys
import subprocess
from collections import defaultdict

from html.parser import HTMLParser

import jinja2

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=jinja2.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)


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


def get_date_authored_timestamp_from_git(path):
    source = os.path.realpath(path)
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%at", source],
        cwd="csswg-drafts",
        capture_output=True,
        encoding="utf_8",
    )
    return int(proc.stdout.splitlines()[-1])


def get_bs_spec_metadata(folder_name, path):
    proc = subprocess.run(
        ["bikeshed", "-f", "--silent", "debug", "--print-metadata", path],
        capture_output = True, encoding = "utf_8")
    metadata = json.loads(proc.stdout)
    
    if metadata["document"]["Level"][0] in ["", "none"]:
        level = 0
    else:
        level = int(metadata["document"]["Level"][0])

    shortname = metadata["document"]["Shortname"][0]
    if shortname == "css-animations-2":
        shortname = "css-animations"
    elif shortname == "css-gcpm-4":
        shortname = "css-gcpm"
    elif shortname == "css-transitions-2":
        shortname = "css-transitions"
    elif shortname == "scroll-animations-1":
        shortname = "scroll-animations"
    else:
        # Fix CSS snapshots (e.g. "css-2022")
        snapshot_match = re.match("^css-(20[0-9]{2})$", shortname)
        if snapshot_match:
            shortname = "css-snapshot"
            level = int(snapshot_match.group(1))

    return {
        "timestamp": get_date_authored_timestamp_from_git(path),
        "shortname": shortname,
        "level": level,
        "title": metadata["document"]["Title"][0],
        "workStatus": metadata["document"]["Work Status"][0].lower(),
    }


def get_html_spec_metadata(folder_name, path):
    match = re.match("^([a-z0-9-]+)-([0-9]+)$", folder_name)
    if match and match.group(1) == "css":
        shortname = "css-snapshot"
        title = f"CSS Snapshot {match.group(2)}"
    else:
        shortname = match.group(1) if match else folder_name
        title = title_from_html(path)

    return {
        "shortname": shortname,
        "level": int(match.group(2)) if match else 0,
        "title": title,
        "workStatus": "completed"  # It's a good heuristic
    }


def create_symlink(shortname, spec_folder):
    """Creates a <shortname> symlink pointing to the given <spec_folder>.
    """

    if spec_folder in timestamps:
        timestamps[shortname] = timestamps[spec_folder]

    shortname_folder = os.path.join("./csswg-drafts", shortname)
    try:
        os.symlink(spec_folder, shortname_folder)
    except OSError:
        pass


CURRENT_WORK_EXCEPTIONS = {
    "css-conditional": 5,
    "css-easing": 2,
    "css-grid": 2,
    "css-snapshot": None,  # always choose the last spec
    "css-values": 4,
    "css-writing-modes": 4,
    "web-animations": 2
}

# ------------------------------------------------------------------------------

specgroups = defaultdict(list)
timestamps = defaultdict(list)

for entry in os.scandir("./csswg-drafts"):
    if entry.is_dir(follow_symlinks=False):
        # Not actual specs, just examples.
        if entry.name in ["css-module"]:
            continue

        bs_file = os.path.join(entry.path, "Overview.bs")
        html_file = os.path.join(entry.path, "Overview.html")
        if os.path.exists(bs_file):
            metadata = get_bs_spec_metadata(entry.name, bs_file)
            timestamps[entry.name] = metadata["timestamp"]
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
    if len(specgroup) == 1:
        if shortname != specgroup[0]["dir"]:
            create_symlink(shortname, specgroup[0]["dir"])
    else:
        specgroup.sort(key=lambda spec: spec["level"])

        # TODO: This algorithm for determining which spec is the current work
        # is wrong in a number of cases. Try and come up with a better
        # algorithm, rather than maintaining a list of exceptions.
        for spec in specgroup:
            if shortname in CURRENT_WORK_EXCEPTIONS:
                if CURRENT_WORK_EXCEPTIONS[shortname] == spec["level"]:
                    spec["currentWork"] = True
                    currentWorkDir = spec["dir"]
                    break
            elif spec["workStatus"] != "completed":
                spec["currentWork"] = True
                currentWorkDir = spec["dir"]
                break
        else:
            specgroup[-1]["currentWork"] = True
            currentWorkDir = specgroup[-1]["dir"]

        if shortname != currentWorkDir:
            create_symlink(shortname, currentWorkDir)
        if shortname == "css-snapshot":
            create_symlink("css", currentWorkDir)


with open('./csswg-drafts/timestamps.json', 'w') as f:
    json.dump(dict(sorted(timestamps.items())), f, indent=2)


with open("./csswg-drafts/index.html", mode='w', encoding="UTF-8") as f:
    template = jinja_env.get_template("index.html.j2")
    f.write(template.render(specgroups=specgroups))
