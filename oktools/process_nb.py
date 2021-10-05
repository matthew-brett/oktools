#!/usr/bin/env python
""" Process notebook for distribution
"""

from argparse import ArgumentParser

from .cutils import process_nb, write_nb


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('notebook',
                        help='Notebook to process')
    parser.add_argument('out_notebook',
                        help='Output path for processed notebook')
    parser.add_argument('--execute', action='store_true',
                        help='If specified, execute notebook before processing')
    return parser


def main():
    args = get_parser().parse_args()
    nb = process_nb(args.notebook, execute=args.execute)
    write_nb(nb, args.out_notebook)


if __name__ == '__main__':
    main()
