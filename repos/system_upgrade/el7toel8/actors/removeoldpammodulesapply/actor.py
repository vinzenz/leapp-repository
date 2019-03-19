import re

from leapp.actors import Actor
from leapp.libraries.common.pam import PAM
from leapp.models import RemovedPAMModules
from leapp.tags import IPUWorkflowTag, PreparationPhaseTag


class RemoveOldPAMModulesApply(Actor):
    """
    Remove old PAM modules that are no longer available in RHEL-8 from
    PAM configuration to avoid system lock out.
    """
    name = 'removed_pam_modules_apply'
    consumes = (RemovedPAMModules,)
    produces = ()
    tags = (IPUWorkflowTag, PreparationPhaseTag)

    def process(self):
        model = next(self.consume(RemovedPAMModules))
        files = {}
        
        # Read files
        for file in PAM.files:
            try:
                with open(file, 'r') as f:
                    files[file] = f.read()
            except IOError as err:
                if err.errno == errno.ENOENT:
                    pass
                else:
                    raise 

        # Comment modules
        for file, content in files.items():
            for module in model.modules:
                content = re.sub(
                    r'^([ \t]*[^#\s]+.*{0}\.so.*)$'.format(module),
                    r'#\1',
                    content,
                    flags=re.MULTILINE
                )
            files[file] = content

        # Write new content
        for file, content in files.items():
            with open(file, 'w') as f:
                f.write(content)
