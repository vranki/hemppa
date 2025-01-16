import asyncio
import functools
import signal
import sys
import traceback

from . import Bot


async def main():
    bot = Bot()
    bot.init()

    loop = asyncio.get_running_loop()

    for signame in {'SIGINT', 'SIGTERM'}:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(bot.handle_exit, signame, loop))

    await bot.run()
    await bot.shutdown()


try:
    asyncio.run(main())
except Exception as e:
    traceback.print_exc(file=sys.stderr)
