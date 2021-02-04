from github import Github

from modules.common.module import BotModule


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.repo_rooms = dict()
        self.machine_prefix = "M: "
        self.space_prefix = "S: "

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)

        if len(args) == 1:
            if args[0] == 'rmrepo':
                bot.must_be_admin(room, event)
                del self.repo_rooms[room.room_id]
                await bot.send_text(room, 'Github repo removed from this room.')
                bot.save_settings()
                return
            if args[0] == 'repo':
                await bot.send_text(room, f'Github repo for this room is {self.repo_rooms.get(room.room_id, "not set")}.')
                return
            if args[0] == 'machines':
                reponame = self.repo_rooms.get(room.room_id, None)
                if reponame:
                    await self.get_machine_status(bot, room, reponame, self.machine_prefix)
                else:
                    await bot.send_text(room, f'No github repo set for this room. Use setrepo to set it.')
                return
            if args[0] == 'spaces':
                reponame = self.repo_rooms.get(room.room_id, None)
                if reponame:
                    await self.get_machine_status(bot, room, reponame, self.space_prefix)
                else:
                    await bot.send_text(room, f'No github repo set for this room. Use setrepo to set it.')
                return

        if len(args) == 2:
            if args[0] == 'setrepo':
                bot.must_be_admin(room, event)

                reponame = args[1]
                self.logger.info(f'Adding repo {reponame} to room id {room.room_id}')

                self.repo_rooms[room.room_id] = reponame
                await bot.send_text(room, f'Github repo {reponame} set to this room.')
                bot.save_settings()
                return

        await bot.send_text(room, 'Unknown command')

    async def get_machine_status(self, bot, room, reponame, prefix):
        g = Github()
        repo = g.get_repo(reponame)
        open_issues = repo.get_issues(state='open')
        labels = repo.get_labels()
        machine_status = dict()
        working_machines = []
        for label in labels:
            if prefix in label.name:
                machine_name = label.name[len(prefix):]
                machine_status[machine_name] = []
                for issue in open_issues:
                    if label in issue.labels:
                        machine_status[machine_name].append(issue)
                if not machine_status[machine_name]:
                    working_machines.append(machine_name)
                    del machine_status[machine_name]

        text_out = reponame + ":\n"
        html_out = f'<b>{reponame}:</b> <br/>'
        for machine in machine_status.keys():
            text_out = text_out + f'{machine}: '
            html_out = html_out + f'🚧 {machine}: '
            for issue in machine_status[machine]:
                text_out = text_out + f'{issue.title} ({issue.html_url}) '
                html_out = html_out + f'<a href="{issue.html_url}">{issue.title}</a> '
            text_out = text_out + f'\n'
            html_out = html_out + f'<br/>'

        text_out = text_out + " OK : " + ', '.join(working_machines)
        html_out = html_out + " OK ☑️ " + ', '.join(working_machines)
        await bot.send_html(room, html_out, text_out)


    def help(self):
        return 'Github hacklab asset management'

    def get_settings(self):
        data = super().get_settings()
        data["repo_rooms"] = self.repo_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("repo_rooms"):
            self.repo_rooms = data["repo_rooms"]
