from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import HealthCheckWorkflowTag, FactsPhaseTag, ChecksPhaseTag, ReportPhaseTag


class HealthCheckWorkflow(Workflow):
    name = 'health_check'
    tag = HealthCheckWorkflowTag
    short_name = 'health'
    description = '''No description has been provided for the health_check workflow.'''

    class FactsCollectionPhase(Phase):
        '''Get information (facts) about the system (e.g. installed packages, configuration, ...).

        No decision should be done in this phase. Scan the system to get information you need and provide
        it to other actors in the following phases.
        '''
        name = 'FactsCollection'
        filter = TagFilter(FactsPhaseTag)
        policies = Policies(Policies.Errors.FailPhase,
                            Policies.Retry.Phase)
        flags = Flags()

    class ChecksPhase(Phase):
        '''Check upgradability of the system, produce user question if needed and produce output for the report.

        Check whether it is possible to upgrade the system and detect potential risks. It is not expected to get
        additional information about the system in this phase, but rather work with data provided by the actors from
        the FactsCollection. When a potential risk is detected for upgrade, produce messages for the Reports phase.
        '''
        name = 'Checks'
        filter = TagFilter(ChecksPhaseTag)
        policies = Policies(Policies.Errors.FailPhase,
                            Policies.Retry.Phase)
        flags = Flags()

    class ReportsPhase(Phase):
        '''Provide user with the result of the checks.'''
        name = 'Reports'
        filter = TagFilter(ReportPhaseTag)
        policies = Policies(Policies.Errors.FailPhase,
                            Policies.Retry.Phase)
        flags = Flags()
