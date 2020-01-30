import subprocess
import os

class MatrixModule:
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        encoding="utf-8"
        forbidden_args = ['help', 'edit', 'command', 'stats', 'config', 'ghistory', 'burndown']

        # wrap task
        if not args:
                args=['list']

        if args[0] in forbidden_args:
                 print(args[0], "found in List: " , forbidden_args)
                 await bot.send_text(room, "command not allowed")
                 return()

        result = subprocess.check_output(
                ["task", 
                "rc.confirmation:no", 
                "rc.verbose:list", 
                "rc.bulk:0", 
                "rc.recurrence.confirmation:yes"] 
                + args, stderr=subprocess.DEVNULL)
        await bot.send_text(room, result.decode(encoding))

    def help(self):
        return('taskwarrior')
