# OKtools

Tools to work with OKpy exercises and solutions.

Requires:

* Git
* [Hub utility](https://hub.github.com).  On Mac `brew install hub`.

See the [rmdex README](https://github.com/matthew-brett/rmdex) for
documentation of the markup for the exercises.

Example command to check exercise build and test:

```
okt-dir2exercise --site-config=$HOME/dev_trees/cfd2021/_course.yml .
```

Then, when satisfied:

```
okt-dir2exercise --site-config=$HOME/dev_trees/cfd2021/_course.yml . --push
```
