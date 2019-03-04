from leapp.models import Model, fields
from leapp.topics import SystemFactsTopic, SystemInfoTopic


class Authselect(Model):
    """
    Suggested changes that will convert the system to authselect.
    
    This model describes the authselect call that can be used to convert
    existing configuration into a equivalent or similar configuration
    that is generated by authselect.
    """
    topic = SystemFactsTopic

    profile = fields.Nullable(fields.String(default=None))
    """
    Suggested authselect profile name.
    """

    features = fields.List(fields.String())
    """
    Suggested authselect profile features.
    """

    confirm = fields.Boolean(default=True)
    """
    Changes to the system requires admin confirmation.
    """


class AuthselectDecision(Model):
    """
    Confirmation of changes suggested in Authselect model.
    
    If confirmed is True, the changes will be applied on RHEL-8 machine.
    """
    topic = SystemInfoTopic

    confirmed = fields.Boolean(default=False)
    """
    If true, authselect should be called after upgrade.
    """
