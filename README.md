# OKtools

Tools to work with OKpy exercises and solutions.

Requires:

* Git
* [Hub utility](https://hub.github.com).  On Mac `brew install hub`.

See the [rmdex README](https://github.com/matthew-brett/rmdex) for
documentation of the markup for the exercises.

The tools need a configuration file in YaML format.  Here is an example:

```yaml
# Configuration for cfd2021 exercise builds
# Save as _course.yml in home directory.

# Top-level URL for built book.
url : "https://uob-ds.github.io"
# The subpath of built book under URL.
# Full book URL will then be {url}{base_url}
baseurl : "/cfd2021"
# Local output path for exercise dirs.
# Built exercise directories / repositories will appear here.
org_path : "~/dev_trees/uob-cfd"
# Github organization name to house built repositories.
org_name : "uob-cfd"
# Git base URL for exercise dirs.
git_root : "https://github.com"
# If using JupyterHub, URL of JupyterHub instance.
# Uncomment and edit if using a JupyterHub.
# jh_root : "https://uobhub.org"
```

Save this file as `_course.yml` in the directory with the exercise templates,
or in some directory higher up the file hierarchy (nearer the root directory) — for example, your home directory (if that is on the same filesystem as your exercise templates).

Example command to check exercise build and test, run from the directory containing the exercise template files:

```
# You can omit site-config if _course.yml is in a suitable location.
okt-dir2exercise --site-config=$HOME/my_dir/_course.yml .
```

Then, when satisfied, use the ``--push`` flag to push up the built exercise to a matching repository:

```
# You can omit site-config if _course.yml is in a suitable location.
okt-dir2exercise --site-config=$HOME/my_dir/_course.yml . --push
```
