from leapp.actors import Actor
from leapp.models import SCTPConfig, SystemFacts
from leapp.tags import FactsPhaseTag, IPUWorkflowTag


class SCTPConfigRead(Actor):
    name = 'sctp_read_status'
    description = 'This actor reads SCTP status, if it was/is used.'
    consumes = (SystemFacts,)
    produces = (SCTPConfig,)
    tags = (FactsPhaseTag, IPUWorkflowTag)

    def is_module_loaded(self, module):
        for fact in self.consume(SystemFacts):
            for active_module in fact.kernel_modules:
                if active_module.filename == module:
                    return True
        return False

    def is_sctp_used(self):
        # If anything is using SCTP, be it for listening on new connections or
        # connecting somewhere else, the module will be loaded. Thus, no need to
        # also probe on sockets.
        if self.is_module_loaded('sctp'):
            return True

        # Basic files from lksctp-tools. This check is enough and checking RPM
        # database is an overkill here and this allows for checking for
        # manually installed ones, which is possible.
        from leapp.libraries.actor import sctplib
        lksctp_files = [ '/usr/lib64/libsctp.so.1',
                         '/usr/lib/libsctp.so.1',
                         '/usr/bin/sctp_test' ]
        if sctplib.anyfile(lksctp_files):
            self.log.debug('At least one of lksctp files is present.')
            return True

        from leapp.libraries.actor import sctpdlm
        if sctpdlm.is_dlm_using_sctp(self.log):
            return True

        return False

    def was_sctp_used(self):
        from leapp.libraries.stdlib import call

        output = call(['check_syslog_for_sctp.sh'])
        if len(output):
            self.log.debug('Found logs regarding SCTP on journal.')
            return True

        self.log.debug('Nothing regarding SCTP was found on journal.')
        return False

    def is_sctp_wanted(self):
        if self.is_sctp_used():
            self.log.info('SCTP is being used.')
            return True

        if self.was_sctp_used():
            self.log.info('SCTP was used.')
            return True

        self.log.info('SCTP is not being used and neither wanted.')
        return False

    def process(self):
        sctpconfig = SCTPConfig()
        sctpconfig.wanted = self.is_sctp_wanted()
        self.log.info('Finished reading SCTP status')
        self.produce(sctpconfig)
