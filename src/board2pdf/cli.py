#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from pathlib import Path

try:
    from . import plot
except ImportError:
    import plot

_logger = logging.getLogger(__name__)
_ini_default = Path(__file__).parent / 'board2pdf.config.ini'
_log_levels = {'NOTSET': logging.NOTSET, 'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARN': logging.WARN,
               'ERROR': logging.ERROR, 'FATAL': logging.FATAL}
_pdf_libs = ['pypdf', 'fitz']


def shell_path(abspath: bool = True, exists: bool = True):
    def path_expand(arg: str) -> str:
        path = os.path.expanduser(os.path.expandvars(arg))
        if abspath:
            path = os.path.abspath(path)
        if exists and not os.path.exists(path):
            raise argparse.ArgumentTypeError(f'{path} must be an existing file')
        return path

    return path_expand


def num_range(arg_type, min_val, max_val):
    def range_check(arg: str):
        try:
            f = arg_type(arg)
        except ValueError:
            raise argparse.ArgumentTypeError(f'must be a valid {arg_type}')
        if not min_val <= f <= max_val:
            raise argparse.ArgumentTypeError(f'must be within [{min_val}, {max_val}]')
        return f

    return range_check


def parse_args():
    parser = argparse.ArgumentParser(description='Board2Pdf CLI.')
    parser.add_argument('kicad_pcb', type=shell_path(), help='.kicad_pcb file')
    parser.add_argument('--ini', default=str(_ini_default), type=shell_path(False, False), required=False,
                        help=f'`{_ini_default}` to use')
    parser.add_argument('--log', default='NOTSET', choices=_log_levels.keys(), required=False,
                        help='Enables logging with given log-level')
    parser.add_argument('--scale', default=None, type=num_range(float, 1.0, 10.0), required=False,
                        help='Scale non-frame layers')
    parser.add_argument('--merge', default=None, choices=_pdf_libs, required=False,
                        help='PDF merge processor library')
    parser.add_argument('--colorize', default=None, choices=_pdf_libs, required=False,
                        help='PDF colorize processor library')
    parser.add_argument('--ext', default=None, required=False,
                        help='File extension to use for the merged PDF. Default is `__Assembly`.')
    parser.add_argument('--output', default=None, required=False,
                        help='Output file name. Takes precedent over --ext argument if set.')
    return parser.parse_args()


def main():
    args = parse_args()

    pcb_path = args.kicad_pcb
    log_level = _log_levels[args.log]

    if log_level:
        # use the path of the board for the log file
        log_file = os.path.join(os.path.dirname(pcb_path), 'board2pdf.log')
        logging.basicConfig(filename=log_file, level=log_level)
        _logger.info(f'starting logging with level: {_log_levels[args.log]}')

    ini_path = Path(args.ini).absolute()

    if not ini_path.exists():
        _logger.info(f'{ini_path=} not found, use pcb path')
        ini_path = (Path(pcb_path).parent / args.ini).absolute()
        if not ini_path.exists():
            _logger.error(f'{ini_path=} not found, terminate')
            print(f"Error: ini file `{args.ini}` not found.", sys.stderr)
            sys.exit(1)

    _logger.info(f'{pcb_path=}')
    _logger.info(f'{ini_path=}')

    optional = {}
    if args.scale:
        optional['layer_scale'] = args.scale
    if args.colorize:
        optional['colorize_lib'] = args.colorize
    if args.merge:
        optional['merge_lib'] = args.merge
    if args.ext:
        optional['assembly_file_extension'] = args.ext
    if args.output:
        optional['assembly_file_output'] = args.output
    _logger.info(f'{optional=}')

    sys.exit(0 if plot.cli(pcb_path, ini_path, **optional) else 1)


if __name__ == "__main__":
    main()
