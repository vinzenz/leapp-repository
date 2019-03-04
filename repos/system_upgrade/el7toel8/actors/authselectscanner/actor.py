import os
import re

from leapp.actors import Actor
from leapp.libraries.actor.library import *
from leapp.libraries.common.pam import PAM
from leapp.models import Authselect
from leapp.tags import IPUWorkflowTag, FactsPhaseTag


class AuthselectScanner(Actor):
    """
    Detect what authselect configuration should be suggested to administrator.

    1. Detect possible authselect profile by looking up modules in PAM
       or by checking that daemon is enabled.
       - pam_sss -> sssd
       - pam_winbind -> winbind
       - ypbind enabled -> nis

       If more then one module/daemon is detected that we will keep the
       configuration intact. No authselect profile can be applied.

    2. Detect authselect profile features by looking up modules in PAM
       or nsswitch.conf.
       - pam_faillock => with-faillock
       - pam_fprintd => with-fingerprint
       - pam_access => with-pamaccess
       - pam_mkhomedir => with-mkhomedir
       - pam_oddjob_mkhomedir => with-mkhomedir

    3. Check if there are any unknown PAM modules.
       If there are used PAM modules not used in authselect (such as pam_ldap),
       we must keep the configuration intact.

    4. Check if authconfig was used to create current configuration.
       If yes, we can automatically convert the configuration to authselect.
       If no, we need admin's confirmation.

       - Check that /etc/sysconfig/authconfig exists.
       - Check that PAM configuration uses authconfig files.
       - Check that PAM configuration was not touch after sysconfig file
         was created.
    """

    name = 'authselect_scanner'
    consumes = ()
    produces = (Authselect,)
    tags = (IPUWorkflowTag, FactsPhaseTag)

    profile = None
    features = []
    confirm = True
    
    known_modules = [
        'pam_access',
        'pam_deny',
        'pam_ecryptfs',
        'pam_env',
        'pam_faildelay',
        'pam_faillock',
        'pam_fprintd',
        'pam_keyinit',
        'pam_krb5',
        'pam_lastlog',
        'pam_limits',
        'pam_localuser',
        'pam_mkhomedir',
        'pam_oddjob_mkhomedir',
        'pam_permit',
        'pam_pkcs11',
        'pam_pwquality',
        'pam_sss',
        'pam_succeed_if',
        'pam_systemd',
        'pam_u2f',
        'pam_umask',
        'pam_unix',
        'pam_winbind'
    ]
    """
    List of PAM modules that are known by authselect.
    """

    def process(self):
        # Load configuration
        self.ac = Authconfig.from_system_configuration()
        self.dconf = DConf.from_system_configuration()
        self.pam = PAM.from_system_configuration()

        # Detect possible authselect configuration
        self.step_detect_profile()
        self.step_detect_features()
        self.step_detect_sssd_features()
        self.step_detect_winbind_features()

        # Check if there is any module that is not known by authselect.
        # In this case we must left existing configuration intact.
        if self.pam.has_unknown_module(self.known_modules):
            self.profile = None
            self.features = []

        # Check if the proposed authselect configuration can be activated
        # automatically or admin's confirmation is required.
        self.step_detect_if_confirmation_is_required()

        # Remove duplicates
        self.features = sorted(set(self.features))

        self.produce(Authselect(
            profile=self.profile,
            features=self.features,
            confirm=self.confirm
        ))

    def step_detect_profile(self):
        """
        Authselect supports three different profiles:
          - sssd
          - winbind
          - nis

        Only one of these profiles can be selected therefore if existing
        configuration contains combination of these daemons we can not
        suggest any profile and must keep existing configuration.
        """
        enabled_no = 0
        profile = None

        if self.pam.has('pam_sss'):
            profile = 'sssd'
            enabled_no += 1

        if self.pam.has('pam_winbind'):
            profile = 'winbind'
            enabled_no += 1

        if is_service_enabled('ypbind'):
            profile = 'nis'
            enabled_no += 1

        self.profile = profile if enabled_no == 1 else None

    def step_detect_features(self):
        pam_map = {
            'pam_faillock': 'with-faillock',
            'pam_fprintd': 'with-fingerprint',
            'pam_access': 'with-pamaccess',
            'pam_mkhomedir': 'with-mkhomedir',
            'pam_oddjob_mkhomedir': 'with-mkhomedir'
        }

        for module, feature in pam_map.items():
            if self.pam.has(module):
                self.features.append(feature)

    def step_detect_sssd_features(self):
        if self.profile != "sssd":
            return

        # sudoers: sss
        result = re.search(
            "^[ \t]*sudoers[ \t]*:.*sss.*$",
            read_file("/etc/nsswitch.conf"),
            re.MULTILINE
        )

        if result is not None:
            self.features.append("with-sudo")

        # SSSD Smartcard support
        # We enable smartcard support only if it was not handled by pam_pkcs11.
        # Otherwise pam_pkcs11 configuration must be converted manually.
        if not self.pam.has('pam_pkcs11'):
            if self.ac.get_bool('USESMARTCARD'):
                self.features.append("with-smartcard")

            if self.ac.get_bool('FORCESMARTCARD'):
                self.features.append("with-smartcard-required")

            if self.dconf.get_string('removal-action') == 'lock-screen':
                self.features.append("with-smartcard-lock-on-removal")

    def step_detect_winbind_features(self):
        if self.profile != "winbind":
            return

        if self.ac.get_bool('WINBINDKRB5'):
            self.features.append("with-krb5")

    def step_detect_if_confirmation_is_required(self):
        sysconfig = '/etc/sysconfig/authconfg'
        links = {
            '/etc/pam.d/fingerprint-auth': '/etc/pam.d/fingerprint-auth-ac',
            '/etc/pam.d/password-auth': '/etc/pam.d/password-auth-ac',
            '/etc/pam.d/postlogin': '/etc/pam.d/postlogin-ac',
            '/etc/pam.d/smartcard-auth': '/etc/pam.d/smartcard-auth-ac',
            '/etc/pam.d/system-auth': '/etc/pam.d/system-auth-ac'
        }

        self.confirm = True

        # Check that authconfig was used to create the configuration
        if not os.path.isfile(sysconfig):
            return

        # Check that all files are symbolic links to authconfig files
        for name, target in links.items():
            if not os.path.islink(name):
                return

            if os.readlink(name) != target:
                return

        # Check that all file were not modified after
        # /etc/sysconfig/authconfig was created.
        mtime = os.path.getmtime(sysconfig)
        for f in links.values():
            if os.path.getmtime(f) > mtime:
                return

        self.confirm = False
