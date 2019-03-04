import errno
import re

from leapp.libraries.stdlib import run, CalledProcessError 


def read_file(file):
    """
        Read file contents. Return empty string if the file does not exist.
    """
    try:
        with open(file, "r") as f:
            return f.read()
    except IOError as err:
        if err.errno == errno.ENOENT:
            return ""
        else:
            raise 


def is_service_enabled(service):
    """
        Return true if @service is enabled with systemd, false otherwise.
    """
    try:
        run(["/usr/bin/systemctl", "is-enabled", service + ".service"])
    except (OSError, CalledProcessError):
        return False

    return True


class ConfigFile(object):
    """
        Base class for config parsers.
    """
    
    def __init__(self, config, value_yes, value_no):
        self.value_yes = value_yes
        self.value_no = value_no
        self.options = {}
        self.parse(config)

    def parse(self, config):
        result = re.findall(
            r"^[ \t]*([^\s=]*)=\"?({0}|{1}|[^\"\n]*)\"?$".format(
                self.value_yes,
                self.value_no
            ),
            config,
            re.MULTILINE
        )

        for key, value in result:
            self.options[key] = value

    def get_string(self, option):
        if option not in self.options:
            return None

        return self.options[option]

    def get_bool(self, options):
        if option not in self.options:
            return False

        if self.options[option] == self.value_yes:
            return True

        return False


class Authconfig(ConfigFile):
    """
        Parse authconfig configuration.
    """

    def __init__(self, config):
        ConfigFile.__init__(self, config, 'yes', 'no')

    @staticmethod
    def from_system_configuration():
        return Authconfig(read_file('/etc/sysconfig/authconfig'))


class DConf(ConfigFile):
    """
        Parse dconf configuration.
    """

    def __init__(self, config):
        ConfigFile.__init__(self, config, 'true', 'false')

    @staticmethod
    def from_system_configuration():
        return DConf(read_file('/etc/dconf/db/distro.d/10-authconfig'))
