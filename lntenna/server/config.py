import os
from configparser import RawConfigParser
from shutil import copyfile


home = os.path.expanduser("~")
config_path = home + "/.lntenna/"
if not os.path.exists(config_path):
    print(f"Config file not found, copying example config... to {config_path}")
    os.makedirs(config_path)
    copyfile("example_config.ini", config_path + "config.ini")

DEFAULT_CONFIG_FILE = config_path + "config.ini"


def get_config_file():
    return os.environ.get("CONFIG_FILE", DEFAULT_CONFIG_FILE)


CONFIG_FILE = get_config_file()


def create_config(config_file=None):
    parser = RawConfigParser()
    parser.read(config_file or CONFIG_FILE)
    return parser


CONFIG = create_config()
