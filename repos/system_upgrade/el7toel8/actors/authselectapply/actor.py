from leapp.actors import Actor
from leapp.libraries.stdlib import run
from leapp.models import Authselect, AuthselectDecision, Report
from leapp.tags import IPUWorkflowTag, ApplicationsPhaseTag


class AuthselectApply(Actor):
    """
    Apply changes suggested by AuthselectScanner.
    
    If confirmed by admin in AuthselectDecision, call suggested authselect
    command to configure the system using this tool.
    """
    name = 'authselect_apply'
    consumes = (Authselect, AuthselectDecision,)
    produces = (Report,)
    tags = (IPUWorkflowTag, ApplicationsPhaseTag)

    def process(self):
        model = next(self.consume(Authselect))
        decision = next(self.consume(AuthselectDecision))

        if not decision.confirmed or model.profile is None:
            return

        self.command = 'authselect select {0} {1} --force'.format(
            model.profile,
            ' '.join(model.features)
        )

        try:
            run(self.command.split(' '))
        except Exception as err:
            self.failure(err)
            return

        self.success()

    def failure(self, err):
        self.produce(
            Report(
                severity='Error',
                result='Fail',
                summary='Authselect call failed.',
                details=str(err),
                solutions=self.command
            )
        )

    def success(self):
        self.produce(
            Report(
                severity='Info',
                result='Fixed',
                summary='System was converted to authselect.',
                details='System was converted to authselect with the '
                        'following call: %s' % self.command,
                solutions=None
            )
        )
