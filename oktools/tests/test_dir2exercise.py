# Test for dir2exercise utilities

from pathlib import Path
import os.path as op
import shutil
from pathlib import Path

HERE = op.realpath(op.dirname(__file__))
DATA_DIR = op.join(HERE, 'data')
THREE_GIRLS = op.join(DATA_DIR, 'three_girls')
THREE_GIRLS_EXTRA = op.join(DATA_DIR, 'three_girls_extra')


from tempfile import TemporaryDirectory
from oktools.cutils import (get_site_dict, write_ipynb, process_dir,
                            grade_path, write_dir)

import pytest


def test_get_site_dict():
    # Check prefer course.yml to _config.yml
    fn1 = op.realpath(op.join(DATA_DIR, 'course.yml'))
    assert get_site_dict(fn1) == {'baseurl': 'https://foo.github.com/bar',
                                  'baz': 'bong'}
    fn2 = op.realpath(op.join(DATA_DIR, '_config.yml'))
    assert (get_site_dict(fn2)['baseurl'] ==
            'https://matthew-brett.github.io/cfd2019')


def test_smoke_and_fails():
    base_nb_root = 'three_girls'
    with TemporaryDirectory() as tmpdir:
        tmp_3g = op.join(tmpdir, 'three_girls')
        shutil.copytree(THREE_GIRLS, tmp_3g)
        tmp_nb_in = op.join(tmp_3g, base_nb_root + '_template.Rmd')
        tmp_ex_out = op.join(tmp_3g, base_nb_root + '.ipynb')
        assert op.isfile(tmp_nb_in)
        assert not op.isfile(tmp_ex_out)
        process_dir(tmp_3g)
        assert not op.isfile(tmp_ex_out)
        write_ipynb(tmp_3g, 'exercise')
        assert op.isfile(tmp_ex_out)
        grade_path(tmp_3g)
        tmp_out = op.join(tmpdir, 'out_path')
        write_dir(tmp_3g, tmp_out)
        assert op.isdir(tmp_out)
        assert op.isdir(op.join(tmp_out, 'tests'))
        all_files = [str(p) for p in Path(tmp_out).rglob('*')]
        z_list = sorted(op.relpath(f, tmp_out) for f in all_files)
        assert z_list == [
            'tests',
            'tests/__init__.py',
            'tests/q_1_no_girls.py',
            'tests/q_2_three_of_five.py',
            'tests/q_3_three_or_fewer.py',
            'tests/q_4_r_three_of_four.py',
            'three_girls.ipynb',
            'three_girls.ok']
        # Test failing exercise causes error.
        bad_ex_fname = op.join(tmp_3g, 'tests', 'q_5.py')
        with open(bad_ex_fname, 'wt') as fobj:
            fobj.write('''
test = {
  'name': 'Question 5',
  'points': 20,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          >>> False
          True
          """,
          'hidden': False,
          'locked': False
        },
      ],
      'scored': True,
      'setup': '',
      'teardown': '',
      'type': 'doctest'
    }
  ]
}''')
        process_dir(tmp_3g)
        write_ipynb(tmp_3g, 'exercise')
        with pytest.raises(RuntimeError):
            grade_path(tmp_3g)


def test_proc_test():
    # Test extras removed
    with TemporaryDirectory() as tmpdir:
        tmp_3g = op.join(tmpdir, 'three_girls')
        shutil.copytree(THREE_GIRLS_EXTRA, tmp_3g)
        tmp_out = op.join(tmpdir, 'out_path')
        write_dir(tmp_3g, tmp_out)
        out_test_pth = Path(tmp_out) / 'tests' / 'q_1_no_girls.py'
        out_test_text = out_test_pth.read_text()
        assert '-extra' not in out_test_text
        assert '>>> True' not in out_test_text
        out_test_pth = Path(tmp_out) / 'tests' / 'q_3_three_or_fewer.py'
        out_test_text = out_test_pth.read_text()
        assert '-extra' not in out_test_text
        assert '>>> False' not in out_test_text
        assert ">>> 'two'" not in out_test_text
