#!/usr/bin/env python
""" Build OKpy exercise directory from directory template.

Depends on `hub` command line utility.

On Mac:

    brew install hub
"""

import os
import os.path as op
import shutil
import re
from argparse import ArgumentParser
from functools import partial
from subprocess import check_call, check_output, run, PIPE


from .cutils import (cd, proc_config, build_url, check_repo, process_dir,
                     write_ipynb, grade_path, write_dir, get_exercise_fnames)


def push_dir(path, site_dict, strip=False, force=False):
    with cd(path):
        do_push_dir(site_dict, strip, force)


quiet_run = partial(run, stdout=PIPE, text=True)


def get_default_branch(gh_url):
    out = check_output(['git', 'remote', 'show', gh_url], text=True)
    branch = re.search('HEAD branch: (.*)', out, re.M).groups()[0]
    return None if branch == '(unknown)' else branch


def check_hub():
    if shutil.which('hub') is not None:
        return
    raise RuntimeError(
        '"hub" binary is not on the PATH. '
        'See https://github.com/github/hub#installation '
        'for instructions')


def do_push_dir(site_dict, strip=False, force=False):
    ex_name = op.basename(os.getcwd())
    gh_root = site_dict['git_root']
    gh_path = f"{site_dict['org_name']}/{ex_name}"
    gh_url = f"{gh_root}/{gh_path}"
    repo_exists = run(['git', 'ls-remote', gh_url],
                      stdout=PIPE, stderr=PIPE).returncode == 0
    if strip and op.isdir('.git'):
        shutil.rmtree('.git')
    if not op.isdir('.git'):
        quiet_run(['git', 'init'], check=True)
    if repo_exists:
        quiet_run(['git', 'remote', 'remove', 'origin'])
        quiet_run(['git', 'remote', 'add', 'origin', gh_url],
                  check=True)
        if not strip:
            quiet_run(['git', 'fetch', 'origin'], check=True)
    else:  # Repo does not exist, create it.
        check_hub()
        quiet_run(['hub', 'create', gh_path], check=True)
    # We now have an origin, and we can get the default branch.
    gh_branch = get_default_branch(gh_url)
    local_branch = 'main' if gh_branch is None else gh_branch
    check_call(['git', 'checkout', '-B', local_branch])
    if not strip and gh_branch:
        quiet_run(
            ['git', 'reset', '--soft', f'origin/{gh_branch}'],
            check=True)
    check_call(['git', 'add', '.'])
    if len(check_output(['git', 'diff', '--staged'])) == 0:
        print('No changes to commit')
        return
    check_call(['git', 'commit', '-m', 'Update from template'])
    check_call(['git', 'push', 'origin', local_branch] +
                (['--force'] if (strip or force) else []))


def main():
    parser = ArgumentParser()
    parser.add_argument('dir', help="Directory of exercise", nargs='?',
                        default=os.getcwd())
    parser.add_argument('--out-path',
                        help='Output path for exercise directory'
                        '(default from course config below)'
                       )
    parser.add_argument('--no-grade', action='store_true',
                        help='If specified, do not grade solution notebook')
    parser.add_argument('--with-solution', action='store_true',
                        help='If specified, also upload solution')
    parser.add_argument('--with-extras', action='store_true',
                        help='If specified, also include extra witheld tests')
    parser.add_argument('--rmd', action='store_true',
                        help='If specified, use Rmd exercise file rather than '
                        'ipynb (for now, implies --no-grade)')
    parser.add_argument('--push', action='store_true',
                        help='If specified, push exercise to remote')
    parser.add_argument('--strip', action='store_true',
                        help='If specified, strip exercise history')
    parser.add_argument('--force', action='store_true',
                        help='If specified, force push exercise repository')
    parser.add_argument('--no-clean', action='store_true',
                        help='If specified, do not delete existing exercise '
                             'files in output directory')
    parser.add_argument('--no-check-files', action='store_true',
                        help='If specified, do not check repository for '
                             'untracked / ignore files in output directory')
    parser.add_argument('--site-config',
                        help='Path to configuration file for course '
                        '(default finds {course,_config}.yml, in dir, parents)'
                       )
    args = parser.parse_args()
    if args.rmd:  # We can't grade rmds, thus far.
        args.no_grade = True
    site_dict, out_path = proc_config(args.dir,
                                      args.site_config,
                                      args.out_path)
    in_dir = op.abspath(args.dir)
    process_dir(in_dir, site_dict=site_dict)
    check_repo(in_dir, not args.rmd, not args.no_check_files)
    ex_fname = get_exercise_fnames(in_dir)['exercise']
    if not args.rmd:
        ex_fname = write_ipynb(in_dir, 'exercise')
        if args.with_solution:
            write_ipynb(in_dir, 'solution', execute=True)
    if not args.no_grade:
        grade_path(in_dir)
    out_path = op.abspath(op.join(out_path, op.basename(in_dir)))
    write_dir(args.dir, out_path, clean=not args.no_clean,
              exclude_exts=() if args.rmd else ('.Rmd',),
              with_solution=args.with_solution,
              with_extras=args.with_extras)
    if args.push:
        push_dir(out_path, site_dict, args.strip, args.force)
    if site_dict.get('jh_root'):
        ex_out = op.join(out_path, op.basename(ex_fname))
        print(build_url(ex_out, site_dict))


if __name__ == '__main__':
    main()
