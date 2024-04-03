from configparser import ConfigParser
import json
import logging

_logger = logging.getLogger(__name__)


class Persistence:
    _options: dict = {
        # config (section, option): (varname, type conversion function)
        ('main', 'settings'): ('templates', json.loads),
        ('main', 'output_dest_dir'): ('output_path', None),
        ('main', 'enabled_templates'): ('enabled_templates', lambda s: [x for x in s.split(',') if x]),
        ('main', 'disabled_templates'): ('disabled_templates', lambda s: [x for x in s.split(',') if x]),
        ('main', 'create_svg'): ('create_svg', lambda x: x == "True"),
        ('main', 'del_temp_files'): ('del_temp_files', lambda x: x == "True"),
        ('main', 'delete_single_page_files'): ('del_single_page_files', lambda x: x == "True"),
        ('main', 'assembly_file_extension'): ('assembly_file_extension', None),
    }
    _typeconv: dict = {
        bool: lambda x: "True" if x else "False",
        (list, tuple): lambda x: ",".join(x),
        dict: lambda x: json.dumps(x),
        (int, float): lambda x: str(x),
        str: lambda x: x,
    }

    def __init__(self, configfile: str):
        self._config: ConfigParser = ConfigParser()
        self._configfile: str = configfile

        self.templates: dict = {}
        self.output_path: str = ''
        self.enabled_templates: list = []
        self.disabled_templates: list = []
        self.create_svg: bool = False
        self.del_temp_files: bool = False
        self.del_single_page_files: bool = False
        self.assembly_file_extension: str = "__Assembly"

    def save(self):
        _logger.debug(f"save config")
        self._config.read(self._configfile)

        # `value` type conversion to string
        for (section, option), (varname, str2type) in self._options.items():
            value = getattr(self, varname)
            for _types, convert in self._typeconv.items():
                _logger.info(f"{section},{option}: {varname}")
                if isinstance(value, _types):
                    value = convert(value)
                    break
            else:
                raise Exception(f"unknown value type {type(value)}")

            if not self._config.has_section(section):
                self._config.add_section(section)
            self._config.set(section, option, value)

        with open(self._configfile, 'w') as f:
            self._config.write(f)

    def load(self) -> dict:
        self._config.read(self._configfile)

        values = {}  # alternative output
        for (section, option), (varname, post_action) in self._options.items():
            if self._config.has_option(section, option):
                val = self._config.get(section, option)
                values[varname] = post_action(val) if post_action else val
                setattr(self, varname, values[varname])
                _logger.info(f"{values[varname]=}")

        return values
