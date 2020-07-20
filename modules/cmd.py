from modules.common.module import BotModule
import subprocess
import shlex


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.enabled = False
        self.commands = {}

    async def matrix_message(self, bot, room, event):
        args = shlex.split(event.body)
        args.pop(0)
        # Message body possibilities:
        #   ["run", "echo", "Hello", "world"]
        if args[0] == 'run':
            command_body = MatrixModule.stitch(args[1:])
            bot.must_be_owner(event)
            out = self.run_command(command_body, event.sender, room.display_name)
            await self.send_output(bot, room, out)
        # Message body possibilities:
        #   ["remove", "command_name"]
        elif args[0] == 'remove':
            command_name = args[1]
            bot.must_be_owner(event)
            if command_name in self.commands:
                await bot.send_text(room, f'Removed "{self.commands[command_name]}"')
                del self.commands[command_name]
                bot.save_settings()
            else:
                await bot.send_text(room, f'Could not find command "{command_name}"')
        # Message body possibilities:
        #   ["add", "command_name", "echo", "Hello", "world"]
        elif args[0] == 'add':
            command_name = args[1]
            command_body = MatrixModule.stitch(args[2:])
            bot.must_be_owner(event)
            self.commands[command_name] = command_body
            bot.save_settings()
            await bot.send_text(room, f'Added "{command_name}" -> "{command_body}".')
        # Message body possibilities:
        #   ["list"]
        elif args[0] == 'list':
            if len(self.commands) == 0:
                await bot.send_text(room, "No known commands")
            else:
                known_commands = "Known commands:\n"
                for command_name in self.commands.keys():
                    command_body = self.commands[command_name]
                    known_commands += f' - "{command_name}" -> "{command_body}"\n'
                await bot.send_text(room, known_commands)
        # Message body possibilities:
        #   ["command_name"]
        else:
            command_name = args[0]
            if command_name in self.commands:
                target_command = self.commands[command_name]
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

    @staticmethod
    def stitch(body: list) -> str:
        """
        This is used for stitching arguments again
        Examples:
            ["echo", "Hello", "world"] -> "echo Hello world"
        Args:
            body: str[]

        Returns: str
        """
        return " ".join(body)

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
