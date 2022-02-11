import os
import os.path

print("""
<!DOCTYPE html>
<meta charset="utf-8">
<title>CSS Working Group Specifications</title>
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
</style>

<h1>CSS Working Group Specifications</h1>
<ul>
""")

specs = []

for entry in os.scandir("./csswg-drafts"):
    if entry.is_dir():
        index = os.path.join(entry.path, "index.html")
        if os.path.exists(index):
            name = entry.name.replace("-", " ").title()
            name = name.replace("Css", "CSS")
            name = name.replace("CSSom", "CSSOM")
            name = name.replace("Tv", "TV")
            name = name.replace("Hdr", "HDR")
            name = name.replace("Ui", "UI")
            name = name.replace("Gcpm", "GCPM")
            name = name.replace("Mediaqueries", "Media Queries")
            specs.append((entry.name, name))

specs.sort(key=lambda a: a[0])

for (spec_dir, spec_name) in specs:
    print('  <li><a href="./{}">{}</a></li>'.format(spec_dir, spec_name))

print("</ul>")
