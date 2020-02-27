from modules.common.module import BotModule
import subprocess
import shlex


class MatrixModule(BotModule):
    commands = dict()  # cmd name -> shell command

    async def matrix_message(self, bot, room, event):
        args = shlex.split(event.body)
        args.pop(0)

        if len(args) == 2:
            if args[0] == 'run':
                bot.must_be_owner(event)
                out = self.run_command(args[1], event.sender, room.display_name)
                await self.send_output(bot, room, out)
            if args[0] == 'remove':
                bot.must_be_owner(event)
                cmdname = args[1]
                self.commands.pop(cmdname, None)
                bot.save_settings()
                await bot.send_text(room, 'Command removed.')
        elif len(args) == 3:
            if args[0] == 'add':
                bot.must_be_owner(event)
                cmdname = args[1]
                self.commands[cmdname] = args[2]
                bot.save_settings()
                await bot.send_text(room, 'Command added.')
        elif len(args) == 1:
            if args[0] == 'list':
                await bot.send_text(room, 'Known commands: ' + str(self.commands))
            elif args[0] in self.commands:
                self.logger.debug(f"room: {room.display_name} sender: {event.sender} wants to run cmd {args[0]}")
                out = self.run_command(self.commands[args[0]], event.sender, room.display_name)
                await self.send_output(bot, room, out)
            else:
                await bot.send_text(room, 'Unknown command.')

    def help(self):
        return 'Runs shell commands'

    def get_settings(self):
        data = super().get_settings()
        data['commands'] = self.commands
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('commands'):
            self.commands = data['commands']

    def run_command(self, command, user, roomname):
        self.logger.info(f"Running command {command}..")
        environment = {'MATRIX_USER': user, 'MATRIX_ROOM': roomname}
        processout = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, text=True, env=environment)
        return processout.stdout

    async def send_output(self, bot, room, output):
        html = output
        if output.count('\n') > 1:
            html = "<pre>" + output + "</pre>"
        if len(output) == 0:
            output = html = '(No output returned)'
        await bot.send_html(room, html, output)
