# csswg-auto-build

A proof of concept to show how the Editor's Drafts for the CSS Working Group
specifications can be automatically built via Github Actions and served via
Github Pages.

The official server for the CSSWG draft specs, https://drafts.csswg.org, is
often down lately, particularly on European mornings. This repo serves as a
mirror that updates every 3 hours, as well as a proof of concept setup for how
those specs can be built and served using only Github.

The mirror is available at https://andreubotella.com/csswg-auto-build

## High-level build description

All CSS specifications (except for a few which are no longer updated) are built
with [Bikeshed](https://github.com/tabatkins/bikeshed). To build them, we find
every file named `Overview.bs` and build them to generate an `Overview.html`
output file. Since the few non-Bikeshed specs all have the `Overview.html`
output file checked into the repo, those can be served as well. Note that we
currently generate every Bikeshed spec, not only those that changed recently,
and that we don't use the `Makefile`s.

We run the Bikeshed build with the
[`--die-on=nothing`](https://tabatkins.github.io/bikeshed/#cli-options) flag,
which means a build output will be generated even in the presence of fatal
errors. This is needed because some of the Bikeshed CSSWG specs haven't been
updated in a while and might contain broken links or syntax that no longer
works. After all, a slightly broken output is better than the spec not being
served at all.

Since Github Pages can't be configured to serve a directory default other than
`index.html`, in order to make links like
https://andreubotella.com/csswg-auto-build/css-text-3 work, we copy every
`Overview.html` file – generated or not – into an `index.html` that Github Pages
will serve as the default. As a special case, for `css-fonts-3`,
[`Fonts.html` is used rather than `Overview.html`
](https://github.com/w3c/csswg-drafts/blob/main/css-fonts-3/README).

We build an index of specs with `build-index.py`. We do this by getting some
pieces of metadata from the spec, which we do by parsing the spec with Bikeshed,
or for non-Bikeshed specs by parsing the HTML to get the `<title>` and applying
heuristics for the rest. We then use that metadata to group specs by their
shortname (i.e. by CSS module) and to sort them by level. We also have an
algorithm to determine which level spec in a shortname represents the current
work, but it is a heuristic that sometimes gets things wrong and needs a set of
exceptions.

In `build-index.py` we also add redirects from a level-less shortname
(https://andreubotella.com/csswg-auto-build/css-grid) to the spec that
represents the current work for that module (`css-grid-2` in this case). Since
Github Actions doesn't support specifying server-side redirects, we create a
`css-grid/index.html` file that uses a [`<meta http-equiv="refresh">`
](https://html.spec.whatwg.org/multipage/semantics.html#attr-meta-http-equiv-refresh)
pragma to achieve that redirect.

After this, the `csswg-drafts` git submodule folder now has additional
`Overview.html` and `index.html` files. In order to publish this build with
Github Pages, the contents of the folder must be pushed to the `gh-pages` branch
in this repo. However, the git history of `csswg-drafts` does not need to be
pushed, and the existing `.gitignore` must not be heeded, since otherwise the
generated `Overview.html` files would not be included in the commit. Therefore,
we delete the `.git` folder and `.gitignore` file from the `csswg-drafts`
submodule folder, and we use the
[peaceiris/actions-gh-pages](https://github/peaceiris/actions-gh-pages) action
to publish the result into the `gh-pages` branch.

## Setup specific to this mirror

Since this repo is meant as a setup for an auto-updating mirror for when
https://drafts.csswg.org is down, there are a few things set in place that
wouldn't be if the build mentioned above was used on the
[w3c/csswg-drafts](https://github.com/w3c/csswg-drafts) repo or on other mirrors
with different goals.

Since this mirror is meant to be auto-updating, we have a Github Actions
workflow with a cronjob that runs every 3 hours, which checks out the
`csswg-drafts` submodule to the current main and, if the current commit has
changed, it pushes a commit to this repo updating the submodule. This, however,
cannot be done with the `GITHUB_TOKEN` that Github Actions makes available to
workflows, because pushes with that token will prevent follow-up actions from
running (to avoid endless Github Action loops), which means the updates won't be
built or deployed. To prevent that, we use a bot user to commit and push
updates. This is of course not a problem for mirrors that aren't auto-updating,
or for running this build setup on the official repo.

This mirror is also meant to serve as a replacement for when
https://drafts.csswg.org is down, which means having links to the specs in that
site is not ideal. Rather than replace links with regex, which would be very
easy to break, we instead change the [Bikeshed spec
database](https://github.com/tabatkins/bikeshed-data) with the
`configure-spec-data.py` script. That turns out to be much easier, since that
database is mostly made of line-delimited plain text files. This might still
leave any manual link, but the bulk of intra-spec cross-references are correctly
handled.

### Possible issues when adopting this build setup for drafts.csswg.org

- Currently the algorithms in `build-index.py` use heuristics and hardcoded
  exceptions for things like grouping specs by shortname (since the shortname of
  Transitions Level 1 is `css-transitions` but for Level 2 it's
  `css-transitions-2`), or for determining which level of a module is the
  current work. These exceptions would have to be maintained by hand, and
  checked every time a spec is added or metadata is changed. And considering
  that specs like `css-easing-2` or `css-scoping-2` are not listed as specs in
  the drafts.csswg.org index, but as "other documents", it's doubtful that those
  exceptions would be carefully maintained.

- The Bikeshed spec database is built by scraping the specs and processing the
  results, so if a new commit adds a definition in a spec and modifies a
  different spec to use that definition, the data for that definition won't be
  available on the database when that commit gets built. With `--die-on=nothing`
  this wouldn't break the build, it would just result in a missing link, but
  that missing link would stay there until the next build. It's not clear how
  this could be fixed.

## Follow-up work

It would be interesting to detect build warnings and errors, and automatically
file an issue on the w3c/csswg-draft repo. How to deduplicate warnings and
errors, though?