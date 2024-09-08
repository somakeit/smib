import inspect
from pprint import pprint

from slack_bolt.kwargs_injection.async_args import AsyncArgs


slack_args_signature = inspect.signature(AsyncArgs)
pprint(dict(slack_args_signature.parameters), sort_dicts=False)