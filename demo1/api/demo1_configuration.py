from configparser import ConfigParser
from datetime import datetime
from os import curdir, stat
from os.path import abspath, exists, expanduser, join
from pathlib import Path
from typing import List, Optional


class Demo1Configuration(ConfigParser):

    def __init__(self, ini_file_name: Optional[str] = None):
        super().__init__()
        self.add_section('default')

        self.time_created = None
        self.time_updated = None
        self.ini_file_folder = None
        if ini_file_name:
            ini_file_full_path = abspath(ini_file_name)
            if exists(ini_file_full_path):
                ini_file_stat = stat(ini_file_full_path)
                self.time_created = datetime.utcfromtimestamp(
                    ini_file_stat.st_ctime)  # NO SENSE IN LINUX
                self.time_updated = datetime.utcfromtimestamp(
                    ini_file_stat.st_mtime)
                self.ini_file_folder = str(Path(ini_file_full_path).parent)
                with open(ini_file_full_path, 'r') as f:
                    self._initial_configuration_content = f.read()
            # Store source path value
            self.source_full_file_name = ini_file_full_path

        self.__application_folder = self.ini_file_folder if self.ini_file_folder else curdir

    def set_port(self, value: int) -> None:
        self.set('default', 'port', value=str(value))

    def get_port(self) -> int:
        return self.getint('default', 'port', fallback=8000)

    def set_ssl_enable(self, value: bool) -> None:
        self.set('default', 'ssl_enable', value=str(value))

    def is_ssl_enable(self) -> bool:
        return self.getboolean('default', 'ssl_enable', fallback=False)

    def set_keys_folder(self, value: str) -> None:
        self.set('default', 'keys_folder', value=str(value))

    def get_keys_folder(self) -> bool:
        return self.get('default', 'keys_folder', fallback=join(expanduser("~"), '.ssl'))

    def set_setup_mode(self, value: bool) -> None:
        self.set('default', 'setup_mode', value=str(value))

    def get_setup_mode(self) -> bool:
        return self.getboolean('default', 'setup_mode', fallback=True)

    def get_application_folder(self):
        return self.__application_folder

    def set_application_folder(self, application_folder: str):
        self.__application_folder = application_folder
