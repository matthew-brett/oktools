# Test for cutils utilities

import os.path as op
import re
import shutil
from pathlib import Path

from tempfile import TemporaryDirectory

import jupytext

HERE = op.realpath(op.dirname(__file__))
DATA_DIR = op.join(HERE, 'data')
THREE_GIRLS = op.join(DATA_DIR, 'three_girls')


from oktools.cutils import process_nb, find_site_config


HTML_COMMENT_RE = re.compile(r'<!--(.*?)-->', re.M | re.DOTALL)


def test_comment_strip():
    base_nb_root = 'three_girls_template'
    nb_in_fname = op.join(THREE_GIRLS, base_nb_root + '.Rmd')
    nb = jupytext.read(nb_in_fname)
    json = jupytext.writes(nb, fmt='ipynb')
    assert len(HTML_COMMENT_RE.findall(json)) == 4
    clear_nb = process_nb(nb_in_fname)
    json = jupytext.writes(clear_nb, fmt='ipynb')
    assert len(HTML_COMMENT_RE.findall(json)) == 0


def test_find_site_config():
    rp = op.realpath
    eg_config = rp(op.join(DATA_DIR, 'course.yml'))
    with TemporaryDirectory() as tmpdir:
        assert find_site_config(tmpdir) is None
        # Check we can pass Path object
        assert find_site_config(Path(tmpdir)) is None
        # Check preference order
        for fn in ('course.yml', '_course.yml', '_config.yml')[::-1]:
            config_path = rp(op.join(tmpdir, fn))
            shutil.copy(eg_config, config_path)
            sc = find_site_config(tmpdir)
            # Check we can pass Path object
            assert sc == find_site_config(Path(tmpdir))
            # Check for expected config file.
            assert rp(sc) == config_path
    # Check prefer course.yml to _config.yml
    assert rp(find_site_config(DATA_DIR)) == eg_config
    # Starting at an empty directory finds one dir below.
    assert rp(find_site_config(op.join(DATA_DIR, 'empty_dir'))) == eg_config
    # Single config in directory.
    ed_pth = op.join(DATA_DIR, 'exercise_dir')
    assert rp(find_site_config(ed_pth)) == rp(op.join(ed_pth, '_config.yml'))
