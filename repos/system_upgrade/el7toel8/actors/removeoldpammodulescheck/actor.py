from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.libraries.common.pam import PAM
from leapp.models import RemovedPAMModules, Report, Inhibitor
from leapp.tags import IPUWorkflowTag, ChecksPhaseTag


class RemoveOldPAMModulesCheck(Actor):
    """
    Check if it is all right to disable PAM modules that are not in RHEL-8.
    
    If admin will refuse to disable these modules (pam_pkcs11 and pam_krb5),
    upgrade will be stopped. Otherwise we would risk locking out the system
    once these modules are removed.
    """
    name = 'removed_pam_modules_check'
    consumes = (RemovedPAMModules,)
    produces = (Report,Inhibitor)
    tags = (IPUWorkflowTag, ChecksPhaseTag)
    dialogs = (
        Dialog(
            scope='remove_old_pam_modules_check',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Disable pam_pkcs11 module in PAM configuration? '
                          'If no, the upgrade process will be interrupted.',
                    default=False,
                    description='PAM module pam_pkcs11 is no longer available '
                                'in RHEL-8 since it was replaced by SSSD.',
                    reason='Leaving this module in PAM configuration may '
                           'lock out the system.'
                ),
            )
        ),
        Dialog(
            scope='remove_old_pam_modules_check',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Disable pam_krb5 module in PAM configuration? '
                          'If no, the upgrade process will be interrupted.',
                    default=False,
                    description='PAM module pam_krb5 is no longer available '
                                'in RHEL-8 since it was replaced by SSSD.',
                    reason='Leaving this module in PAM configuration may '
                           'lock out the system.'
                ),
            )
        ),
    )

    modules = []

    def process(self):
        model = next(self.consume(RemovedPAMModules))
        self.pam = PAM.from_system_configuration()
        
        for module in model.modules:
            result = self.confirm(module)
            if result:
                self.produce_report(module)
            else:
                self.produce(Inhibitor(
                    summary='Upgrade process was interrupted because there are '
                            'some unsupported PAM modules in configuration.',
                    details='SA user chose to interrupt the upgrade.',
                    solutions='Remove pam_pkcs11 and pam_krb5 from PAM '
                              'configuration and replace them with SSSD.'
                ))
            pass
    
    def confirm(self, module):
        map = {
            'pam_pkcs11': self.dialogs[0],
            'pam_krb5'  : self.dialogs[1]
        }
        
        return self.request_answers(map[module]).get('confirm', False)

    def produce_report(self, module):
        summary = 'Module {0} will be removed from PAM configuration'
        details = ('Module {0} was surpassed by SSSD and therefore it was '
                   'removed from RHEL-8. Keeping it in PAM configuration may '
                   'lock out the system thus it will be automatically removed '
                   'from PAM configuration before upgrading to RHEL-8. '
                   'Please switch to SSSD to recover the functionality '
                   'of {0}.')
        solutions = 'Configure SSSD to replace {0}'
        self.produce(
            Report(
                severity='Info',
                result='Pass',
                summary=summary.format(module),
                details=details.format(module),
                solutions=solutions.format(module)
            )
        )
    
    def produce_inhibitor(self, module):
        summary = ('Upgrade process was interrupted because {0} is enabled in '
                   'PAM configuration and SA user refused to disable it '
                   'automatically.')
        details = ('Module {0} was surpassed by SSSD and therefore it was '
                   'removed from RHEL-8. Keeping it in PAM configuration may '
                   'lock out the system thus it is necessary to disable it '
                   'before the upgrade process can continue.')
        solutions = ('Disable {0} module and switch to SSSD to recover '
                     'its functionality.')
        self.produce(Inhibitor(
            summary=summary.format(module),
            details=details.format(module),
            solutions=solutions.format(module)
        ))
