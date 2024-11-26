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
_log_levels = {'NOTSET': logging.NOTSET, 'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARN': logging.WARN,
               'ERROR': logging.ERROR, 'FATAL': logging.FATAL}
_pdf_libs_merge = ['pypdf', 'pymupdf']
_pdf_libs_color = ['pypdf', 'pymupdf']


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


def cli(board_filepath: str, configfile: str, **kwargs) -> bool:
    import pcbnew
    try:
        from . import persistence
    except ImportError:
        import persistence

    board = pcbnew.LoadBoard(board_filepath)
    config = persistence.Persistence(configfile)
    config_vars = config.load()
    # note: cli parameters override config.ini values
    config_vars.update(kwargs)
    return plot.plot_pdfs(board, **config_vars)


def parse_args():
    parser = argparse.ArgumentParser(description='Board2Pdf CLI.')
    parser.add_argument('kicad_pcb', type=shell_path(), help='.kicad_pcb file')
    parser.add_argument('--ini', default=None, type=shell_path(False, False), required=False,
                        help=f'Path to `board2pdf.config.ini` to use')
    parser.add_argument('--log', default='NOTSET', choices=_log_levels.keys(), required=False,
                        help='Enables logging with given log-level')
    parser.add_argument('--merge', default=None, choices=_pdf_libs_merge, required=False,
                        help='PDF merge processor library')
    parser.add_argument('--colorize', default=None, choices=_pdf_libs_color, required=False,
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

    # Check for the ini file specified with the --ini argument
    # Terminate if the file is not found
    # If no ini file is specified, look for an ini file in the pcb path, then the globally saved ini
    # file, and last for the default ini file.
    if args.ini:
        ini_path = Path(args.ini).absolute()
        if not ini_path.exists():
            _logger.error(f'{ini_path=} specified with --ini argument not found, terminate')
            print(f"Error: ini file `{args.ini}` specified with --ini argument not found.", sys.stderr)
            sys.exit(1)
    else:
        ini_path = Path(os.path.join(os.path.dirname(pcb_path), 'board2pdf.config.ini'))
        if not ini_path.exists():
            _logger.info(f'{ini_path=} not found, use global path')
            ini_path = Path(__file__).parent / 'board2pdf.config.ini'
            if not ini_path.exists():
                _logger.info(f'{ini_path=} not found, use default path')
                ini_path = Path(__file__).parent / 'default_config.ini'
                if not ini_path.exists():
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
    if args.output:
        optional['assembly_file_output'] = args.output
    _logger.info(f'{optional=}')

    sys.exit(0 if cli(pcb_path, ini_path, **optional) else 1)


if __name__ == "__main__":
    main()
