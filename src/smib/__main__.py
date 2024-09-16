import asyncio

from smib.main import SMIB


async def main():
    smib = SMIB()
    await smib.start()

if __name__ == '__main__':
    asyncio.run(main())