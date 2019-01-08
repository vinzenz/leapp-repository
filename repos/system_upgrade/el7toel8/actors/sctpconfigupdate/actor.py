from leapp.actors import Actor
from leapp.models import SCTPConfig
from leapp.tags import ApplicationsPhaseTag, IPUWorkflowTag

class SCTPConfigUpdate(Actor):
    name = 'sctp_config_update'
    description = 'This actor updates SCTP configuration for RHEL8.'
    consumes = (SCTPConfig,)
    produces = ()
    tags = (ApplicationsPhaseTag, IPUWorkflowTag)

    def enable_sctp(self):
        from leapp.libraries.stdlib import call
        self.log.info('Enabling SCTP.')
        call(['/usr/bin/sed', '-i', 's/^\s*blacklist.*sctp/#&/',
              '/etc/modprobe.d/sctp_diag-blacklist.conf',
              '/etc/modprobe.d/sctp-blacklist.conf'])
        self.log.info('Enabled SCTP.')

    def process(self):
        for sctpconfig in self.consume(SCTPConfig):
            self.log.info('Consuming sctp={}'.format(sctpconfig.wanted))
            if sctpconfig.wanted:
                self.enable_sctp()
            break
