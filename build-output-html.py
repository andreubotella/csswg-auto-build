import io
import sys
import json
import os.path
from datetime import datetime, timezone

import jinja2

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    autoescape=jinja2.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)


input = sys.stdin.read()
if input == "":
    messages = []
else:
    input = input.rstrip()
    # Bikeshed's JSON output is not always valid
    if not input.endswith("]"):
        if input.endswith(","):
            input = input[:-1]
        input += "]"
    messages = json.loads(input)

with open(sys.argv[2], mode="w") as f:
    template = jinja_env.get_template("build-output.html.j2")
    f.write(template.render(
        spec_file=sys.argv[1],
        messages=messages,
        now=datetime.now(timezone.utc)
    ))
