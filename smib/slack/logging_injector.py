from injectable import inject
from smib.common.logging_.setup import plugin_logger_factory

def inject_logger_to_slack_context(context, next):
    context['logger'] = inject("plugin_logger", lazy=True)
    next()