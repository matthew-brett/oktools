""" OKpy and course utility functions
"""

import os
import os.path as op
from pathlib import Path
import sys
from glob import iglob
import shutil
import re
import urllib.parse
from contextlib import contextmanager
from functools import partial
from subprocess import check_output

import yaml

import nbformat
import jupytext
from nbconvert.preprocessors import ExecutePreprocessor
from jinja2 import Template

from rmdex.exerciser import (make_exercise, make_solution, write_utf8,
                             read_utf8)

HERE = op.dirname(op.realpath(__file__))
SITE_ROOT = op.realpath(op.join(HERE, '..'))
sys.path.append(HERE)

import grade_oknb as gok


TEMPLATE_RE = re.compile(r'_template\.Rmd$')


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def get_site_dict(site_config):
    with open(site_config, 'r') as ff:
        site = yaml.load(ff.read(), Loader=yaml.SafeLoader)
    # Get full baseurl from _config.yml format.
    if not site['baseurl'].startswith('http') and 'url' in site:
        site['baseurl'] = site['url'] + site['baseurl']
    for path_key in ('org_path',):
        if path_key in site:
            site[path_key] = op.expanduser(site[path_key])
    return site


def find_site_config(dir_path, filenames=('course.yml',
                                          '_course.yml',
                                          '_config.yml')):
    """ Iterate to parents to locate one of filenames specified in `filenames`.
    """
    dir_path = Path(dir_path).resolve()
    while True:
        for fn in filenames:
            pth = dir_path / fn
            if pth.is_file():
                return str(pth)
        prev_dir_path = dir_path
        dir_path = (dir_path / '..').resolve()
        if dir_path == prev_dir_path:  # We hit root.
            break
        try:
            prev_dir_path.relative_to(dir_path)
        except ValueError:
            # We hit fs boundary.
            break
    return None


def proc_config(in_path=None, site_config=None, out_path=None):
    if site_config is None:
       site_config = find_site_config(in_path)
    site_dict = get_site_dict(site_config) if site_config else {}
    if out_path is None:
        out_path = site_dict.get('org_path')
    if out_path is None:
        raise RuntimeError(
            'Must specify out path or "org_path" in config file\n'
            f'Config file is {site_config}'
        )
    return site_dict, out_path


def find_notebook(path):
    ipynbs = list(iglob(op.join(path, '*.ipynb')))
    rmds = list(iglob(op.join(path, '*.Rmd')))
    both = ipynbs + rmds
    if len(both) == 0:
        raise RuntimeError(f'Cannot find notebook files in {path}')
    if len(both) == 1:
        return both[0]
    if len(ipynbs) == 1 and len(rmds) == 1:
        # Look for one pair of matching ipynb and Rmd files.
        ipynb, rmd = both
        if op.splitext(ipynb)[0] == op.splitext(rmd)[0]:
            return ipynb
    fns = '\n'.join(both)
    raise RuntimeError(f'Too many notebook files in {path}:\n{fns}')


def build_url(fn, site_dict):
    if op.isdir(fn):
        fn = find_notebook(fn)
    nb_path, nb_basen = op.split(op.abspath(fn))
    root, ext = op.splitext(nb_basen)
    if ext not in ('.Rmd', '.ipynb'):
        raise RuntimeError(f'Is {fn} really a notebook?')
    repo = op.basename(nb_path)
    s_d = site_dict
    repo_url = urllib.parse.quote(
        f'{s_d["git_root"]}/{s_d["org_name"]}/{repo}')
    hub_suffix = 'hub/user-redirect/git-pull?repo='
    return f'{site_dict["jh_root"]}/{hub_suffix}{repo_url}&subPath={nb_basen}'


def execute_nb(nb, path, nbargs=None):
    nbargs = {} if nbargs is None else nbargs
    ep = ExecutePreprocessor(**nbargs)
    ep.preprocess(nb, {'metadata': {'path': path}})
    return nb


def clear_outputs(nb):
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
    return nb


def path_of(fname):
    return op.split(op.abspath(fname))[0]


def clear_directory_for(fname):
    path = path_of(fname)
    for basename in ('.ok_storage',):
        pth = op.join(path, basename)
        if op.exists(pth):
            os.unlink(pth)
    pycache = op.join(path, 'tests', '__pycache__')
    if op.isdir(pycache):
        shutil.rmtree(pycache)


def good_fname(fname, exclude_exts=(), with_solution=False):
    fn = op.basename(fname)
    if fn.endswith('~'):
        return False
    froot, ext = op.splitext(fn)
    if froot.startswith('.'):
        return False
    if ext in ('.pyc', '.swp') + exclude_exts:
        return False
    if froot.startswith('test_'):
        return False
    if froot.startswith('notes'):
        return False
    if froot.endswith('solution') and not with_solution:
        return False
    if froot.endswith('template'):
        return False
    if fname in ('Makefile',):
        return False
    return True


def good_dirname(dname):
    if dname in ('__pycache__',
                 '.ipynb_checkpoints',
                 'tests-extended'):
        return False
    return True


def ipynb_fname(fname):
    froot, ext = op.splitext(fname)
    return froot + '.ipynb'


HTML_COMMENT_RE = re.compile(r'<!--(.*?)-->', re.M | re.DOTALL)


def clear_md_comments(nb):
    """ Strip HTML comments using regexp
    """
    for cell in nb['cells']:
        if cell['cell_type'] != 'markdown':
            continue
        cell['source'] = HTML_COMMENT_RE.sub('', cell['source'])
    return nb


def write_nb(nb, fname):
    with open(fname, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)


def process_nb(fname, execute=False):
    nb = jupytext.read(fname)
    if execute:
        nb = execute_nb(nb, path_of(fname))
    nb = clear_outputs(nb)
    return clear_md_comments(nb)


def process_write_nb(fname, execute=False):
    clear_directory_for(fname)
    write_nb(process_nb(fname, execute), ipynb_fname(fname))


def git_out(cmd):
    return check_output(['git'] + list(cmd), text=True).strip()


def check_repo(path, ipynb_exercise=True, check_files=True):
    top_level = git_out(['rev-parse', '--show-toplevel'])
    out = git_out(
        ['status', '-uall', '--ignored=traditional',
         '--porcelain', path])
    fnames = [fname[3:] for fname in out.splitlines()]
    # Filter fnames in bad directories:
    fnames = [fname for fname in fnames if
              all([good_dirname(pc) for pc in op.split(op.dirname(fname))])]
    ex_fnames = get_exercise_fnames(path)
    ok_untracked = [Path(ex_fnames['exercise']).relative_to(top_level)]
    if ipynb_exercise:
        ok_untracked.append(Path(ipynb_fname(ok_untracked[0])))
    if not check_files:
        return
    scary_fnames = [fname for fname in fnames if good_fname(fname)
                    and not Path(fname) in ok_untracked]
    if len(scary_fnames):
        raise RuntimeError('Scary untracked / ignored files in repo\n'
                           + '\n'.join(scary_fnames))


def get_exercise_fnames(path):
    templates = [fn for fn in os.listdir(path) if TEMPLATE_RE.search(fn)]
    if len(templates) == 0:
        raise RuntimeError('No _template.Rmd in directory')
    if len(templates) > 1:
        raise RuntimeError('More than one _template.Rmd in directory')
    template_fname= op.join(path, templates[0])
    return dict(
        template=template_fname,
        exercise=TEMPLATE_RE.sub('.Rmd', template_fname),
        solution=TEMPLATE_RE.sub('_solution.Rmd', template_fname))


def process_dir(path, site_dict=None):
    site_dict = {} if site_dict is None else site_dict
    fnames = get_exercise_fnames(path)
    template = read_utf8(fnames['template'])
    if site_dict:
        template = Template(template).render(site=site_dict)
    write_utf8(fnames['exercise'], make_exercise(template))
    write_utf8(fnames['solution'], make_solution(template))
    clear_directory_for(fnames['exercise'])


def write_ipynb(path, nb_type, execute=False):
    fnames = get_exercise_fnames(path)
    out_fname = ipynb_fname(fnames[nb_type])
    write_nb(process_nb(fnames[nb_type], execute=execute), out_fname)
    return out_fname


def grade_path(path):
    fnames = get_exercise_fnames(path)
    grades, messages = gok.grade_nb_fname(fnames['solution'], path)
    gok.print_grades(grades)
    gok.print_messages(messages)
    if any(messages.values()):
        raise RuntimeError('One or more failures')


def clean_path(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            os.remove(op.join(root, file))
        for d in dirs:
            if d != '.git':
                shutil.rmtree(op.join(root, d))
        break


EXTRA_BLOCK_RE = re.compile(r'^\s*#:\s*begin-extra\s*$.*?^\s*#:\s*end-extra\s*$',
                            flags=re.M | re.S)

def proc_test_text(test_text):
    test_text = EXTRA_BLOCK_RE.sub('', test_text)
    if (re.search('begin-extra', test_text) or
        re.search('end-extra', test_text)):
        raise ValueError('Found -extra marker in processed test')
    # Screening check for syntax errors.
    exec(test_text)
    return test_text


def proc_test_paths(in_path, out_path):
    in_text = in_path.read_text()
    try:
        out_text = proc_test_text(in_text)
    except SyntaxError as e:
        raise SyntaxError(f'{e} in {in_path}')
    return out_path.write_text(out_text)


def write_dir(path, out_path, clean=True, exclude_exts=('.Rmd',),
              with_solution=False, with_extras=False):
    """ Copy exercise files from `path` to directory `out_path`

    `clean`, if True, will clean all files from the eventual output directory
    before copying.

    `exclude_exts` specifies filename extensions that should be excluded from
    output directory.

    If `with_solution` is True, also copy the solution file.

    If `with_extras` is True, do no strip extra withheld tests.
    """
    path, out_path = (Path(p) for p in (path, out_path))
    filt_func = partial(good_fname,
                        exclude_exts=exclude_exts,
                        with_solution=with_solution)
    if out_path.is_dir() and clean:
        clean_path(out_path)
    else:
        out_path.mkdir(parents=True)
    for dirpath, dirnames, filenames in os.walk(path):
        dirpath = Path(dirpath)
        sub_dir = dirpath.relative_to(path)
        dirnames[:] = [d for d in dirnames if good_dirname(d)]
        filenames[:] = [f for f in filenames if filt_func(f)]
        if len(filenames) == 0:
            continue
        this_out_path = out_path / sub_dir
        if not this_out_path.is_dir():
            this_out_path.mkdir(parents=True)
        strip_tests = not with_extras and dirpath.stem == 'tests'
        for f in filenames:
            this_in = dirpath / f
            this_out = this_out_path / f
            if strip_tests and this_in.suffix == '.py':
                proc_test_paths(this_in, this_out)
            else:
                this_out.write_bytes(this_in.read_bytes())


def has_md_text(nb, cell_regex):
    """ True if notebook `nb` has Markdown text matching `cell_regex`
    """
    regex = re.compile(cell_regex, re.I)
    for cell in nb.cells:
        if cell['cell_type'] != 'markdown' or not 'source' in cell:
            continue
        if regex.search(cell['source'].lower()):
            return True
    return False


def has_md_text_component(nb, nb_path, cell_regex):
    return nb_path if has_md_text(nb, cell_regex) else None


def has_md_checker(cell_regex):
    return partial(has_md_text_component, cell_regex=cell_regex)
