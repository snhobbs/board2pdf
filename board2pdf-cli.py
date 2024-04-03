#!/usr/bin/env python3

import argparse
import logging
import os
import sys

import plot

_logger = logging.getLogger(__name__)
_ini_default = 'board2pdf.config.ini'
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


def parse_args():
    parser = argparse.ArgumentParser(description='Board2Pdf CLI.')
    parser.add_argument('kicad_pcb', type=shell_path(), help='.kicad_pcb file')
    parser.add_argument('--ini', default=_ini_default, type=shell_path(False, False), required=False,
                        help=f'`{_ini_default}` to use')
    parser.add_argument('--log', default='NOTSET', choices=_log_levels.keys(), required=False,
                        help='Enables logging with given log-level')
    parser.add_argument('--merge', default=None, choices=_pdf_libs, required=False,
                        help='PDF merge processor library')
    parser.add_argument('--colorize', default=None, choices=_pdf_libs, required=False,
                        help='PDF colorize processor library')
    parser.add_argument('--ext', default=None, required=False,
                        help='File extension to use for the merged PDF. Default is `__Assembly`.')
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

    ini_path = os.path.abspath(args.ini)
    if not os.path.exists(ini_path):
        _logger.info(f'{ini_path=} not found, use pcb path')
        ini_path = os.path.join(os.path.dirname(pcb_path), args.ini)
        if not os.path.exists(ini_path):
            _logger.error(f'{ini_path=} not found, terminate')
            print(f"Error: ini file `{args.ini}` not found.", sys.stderr)
            sys.exit(1)

    _logger.info(f'{pcb_path=}')
    _logger.info(f'{ini_path=}')

    optional = {}
    if args.colorize:
        optional['colorize_lib'] = args.colorize
    if args.merge:
        optional['merge_lib'] = args.merge
    if args.ext:
        optional['assembly_file_extension'] = args.ext
    _logger.info(f'{optional=}')

    sys.exit(0 if plot.cli(pcb_path, ini_path, **optional) else 1)


if __name__ == "__main__":
    main()
