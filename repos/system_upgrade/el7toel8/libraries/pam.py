import re


class PAM(object):
    files = [
        '/etc/pam.d/system-auth',
        '/etc/pam.d/smartcard-auth',
        '/etc/pam.d/password-auth',
        '/etc/pam.d/fingerprint-auth',
        '/etc/pam.d/postlogin'
    ]

    def __init__(self, config):
        self.modules = []
        self.parse(config)

    def parse(self, config):
        result = re.findall(
            r"^[ \t]*[^#\s]+.*(pam_\S+)\.so.*$",
            config,
            re.MULTILINE
        )

        self.modules = result

    def has(self, module):
        return module in self.modules

    def has_unknown_module(self, known_modules):
        for module in self.modules:
            if module not in known_modules:
                print(module)
                return True

        return False
    
    @staticmethod
    def read_file(file):
        try:
            with open(file, "r") as f:
                return f.read()
        except OSError as err:
            if err.errno == errno.ENOENT:
                return ""
            else:
                raise 

    @staticmethod
    def from_system_configuration():
        config = ""
        for file in PAM.files:
            config += PAM.read_file(file)

        return PAM(config)
