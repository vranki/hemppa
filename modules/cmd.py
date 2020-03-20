from modules.common.module import BotModule
import subprocess
import shlex


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.commands = []

    async def matrix_message(self, bot, room, event):
        args = shlex.split(event.body)
        args.pop(0)
        if len(args) >= 2:
            # Get full command without using quotation marks
            command = f"{args[1]}"
            for part_of_command in args[2:]:
                command += f" {part_of_command}"

        if len(args) == 2:
            if args[0] == 'run':
                bot.must_be_owner(event)
                out = self.run_command(args[1], event.sender, room.display_name)
                await self.send_output(bot, room, out)
            if args[0] == 'remove':
                bot.must_be_owner(event)
                command_number = int(args[1])
                if self.commands[command_number] is not None:
                    await bot.send_text(room, f'Removed "{self.commands[command_number]}"')
                    self.commands.pop(command_number)
                    bot.save_settings()
                else:
                    await bot.send_text(room, f'Could not find command #{command_number}')
        elif len(args) == 3:
            if args[0] == 'add':
                bot.must_be_owner(event)
                self.commands.append(command)
                bot.save_settings()
                await bot.send_text(room, 'Command added.')
        elif len(args) == 1:
            if args[0] == 'list':
                if len(self.commands) == 0:
                    await bot.send_text(room, "No known commands")
                else:
                    list_commands = ""
                    i = 0
                    for command_name in self.commands:
                        list_commands += f"\n - {i}. \"{command_name}\""
                        i += 1
                    await bot.send_text(room, 'Known commands: ' + list_commands)
            else:
                command_number = int(args[0])
                target_command = self.commands[command_number]
                if target_command is not None:
                    self.logger.debug(
                        f"room: {room.display_name} sender: {event.sender} wants to run cmd {target_command}"
                    )
                    out = self.run_command(target_command, event.sender, room.display_name)
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
