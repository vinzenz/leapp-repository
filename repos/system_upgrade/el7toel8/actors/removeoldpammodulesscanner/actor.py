from leapp.actors import Actor
from leapp.libraries.common.pam import PAM
from leapp.models import RemovedPAMModules, Report
from leapp.tags import IPUWorkflowTag, FactsPhaseTag


class RemoveOldPAMModulesScanner(Actor):
    """
    Scan PAM configuration for modules that are not available in RHEL-8.
    
    PAM module pam_krb5 and pam_pkcs11 are no longer present in RHEL-8
    and must be removed from PAM configuration, otherwise it may lock out
    the system.
    """
    name = 'removed_pam_modules_scanner'
    consumes = ()
    produces = (RemovedPAMModules)
    tags = (IPUWorkflowTag, FactsPhaseTag)

    modules = []

    def process(self):
        self.pam = PAM.from_system_configuration()

        # PAM modules pam_pkcs11 and pam_krb5 are no longer available in
        # RHEL8. We must remove them because if they are left in PAM
        # configuration it may lock out the system.
        for module in ['pam_krb5', 'pam_pkcs11']:
            if self.pam.has(module):
                self.modules.append(module)

        self.produce(RemovedPAMModules(
            modules=self.modules
        ))
