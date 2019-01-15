from leapp.actors import Actor
from leapp.libraries.common import reporting
from leapp.libraries.stdlib import config
from leapp.models import Report, SkippedRepositories
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag


class CheckSkippedRepositories(Actor):
    """
    Produces a report if any repositories enabled on the system is going to be skipped.

    The report by this actor shall additionally include any package that is affected due to skipping the repository.
    """

    name = 'check_skipped_repositories'
    consumes = (SkippedRepositories,)
    produces = (Report,)
    tags = (IPUWorkflowTag, ChecksPhaseTag)

    def process(self):
        repos = set()
        packages = set()

        for message in self.consume(SkippedRepositories):
            repos.update(message.repos)
            packages.update(message.packages)

        if repos:
            title = 'Some enabled RPM repositories are unknown to Leapp'
            summary_data = []
            summary_data.append('The following repositories with Red Hat-signed packages are unknown to Leapp:')
            summary_data.extend(['- ' + r for r in repos])
            summary_data.append('And the following packages installed from those repositories may not be upgraded:')
            summary_data.extend(['- ' + p for p in packages])
            summary = '\n'.join(summary_data)
            reporting.report_with_remediation(
                title=title,
                summary=summary,
                remediation='You can file a request to add this repository to the scope of in-place upgrades '
                            'by filing a support ticket',
                severity='low')

            if config.is_verbose():
                self.log.info('\n'.join([title, summary]))
