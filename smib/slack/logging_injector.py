from injectable import inject



def inject_logger_to_slack_context(context, next):
    context['logger'] = inject("plugin_logger", lazy=True)
    next()
