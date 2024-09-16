import asyncio
from asyncio import CancelledError

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from smib.plugins import load_plugins


async def main():
    # Standard Slack Bolt Setup - App and Socket Mode Handler
    slack_bolt_app = AsyncApp(token=SLACK_BOT_TOKEN)
    socket_mode_handler = AsyncSocketModeHandler(slack_bolt_app, app_token=SLACK_APP_TOKEN)

    # All async long-running tasks
    async_tasks = [
        asyncio.create_task(socket_mode_handler.start_async())
    ]

    load_plugins()

    try:
        await asyncio.gather(*async_tasks)
    except (KeyboardInterrupt, SystemExit, CancelledError):
        await socket_mode_handler.client.close()
        await socket_mode_handler.close_async()

if __name__ == '__main__':
    asyncio.run(main())