"""Builds a redirect to https://w3c.github.io/csswg-drafts."""

import sys
import os
import os.path

import jinja2

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("test-setup/templates"),
    autoescape=jinja2.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)

OUTPUT_PATH = "./output"
REDIRECT_BASE = "https://w3c.github.io/csswg-drafts"

if not sys.argv[1]:
    raise Exception("Needs argv[1]")

template = jinja_env.get_template("redirect.html.j2")
contents = template.render(
    redirect_base=REDIRECT_BASE, spec_folder=sys.argv[1])

folder = os.path.join(OUTPUT_PATH, sys.argv[1])
os.mkdir(folder)

index = os.path.join(folder, "index.html")
with open(index, mode='w', encoding="UTF-8") as f:
    f.write(contents)
