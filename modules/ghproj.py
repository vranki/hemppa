from github import Github
import re
import json

from modules.common.module import BotModule

# Helper class with reusable code for github project stuff
class GithubProject:
    # New format to support array of colors: domains={"koneet":["#BFDADC","#0CBBF0","#0CBBF0","#E15D19","#ED49CF"],"tilat":["#0E8A16","#1E8A16"]}
    def get_domains(description):
        p = re.compile('domains=\{.*\}')
        matches = json.loads(p.findall(description)[0][8:])
        return matches

    def get_domain(reponame, domain):
        g = Github()
        repo = g.get_repo(reponame)
        domains = GithubProject.get_domains(repo.description)
        if(not len(domains)):
            return None, None
        domain_colors = domains.get(domain, None)
        if not domain_colors:
            return None, None

        open_issues = repo.get_issues(state='open')
        domain_labels = []
        labels = repo.get_labels()
        for label in labels:
            for domain_color in domain_colors:
                if label.color == domain_color[1:]:
                    domain_labels.append(label)

        domain_issues = dict()
        domain_ok = []
        for label in domain_labels:
            label_issues = []
            for issue in open_issues:
                if label in issue.labels:
                    label_issues.append(issue)
            if len(label_issues):
                domain_issues[label.name] = label_issues
            else:
                domain_ok.append(label.name)

        return domain_issues, domain_ok

    def domain_to_string(reponame, issues, ok):
        text_out = reponame + ":\n"
        for label in issues.keys():
            text_out = text_out + f'{label}: '
            for issue in issues[label]:
                # todo: add {issue.html_url} when URL previews can be disabled
                text_out = text_out + f'[{issue.title}] '
            text_out = text_out + f'\n'

        text_out = text_out + " OK : " + ', '.join(ok)
        return text_out

    def domain_to_html(reponame, issues, ok):
        html_out = f'<b>{reponame}:</b> <br/>'
        for label in issues.keys():
            html_out = html_out + f'🚧 {label}: '
            for issue in issues[label]:
                # todo: add {issue.html_url} when URL previews can be disabled
                html_out = html_out + f'[{issue.title}] '
            html_out = html_out + f'<br/>'

        html_out = html_out + " OK ☑️ " + ', '.join(ok)
        return html_out

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.repo_rooms = dict()

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

            domain = args[0]
            reponame = self.repo_rooms.get(room.room_id, None)
            if reponame:
                issues, ok = GithubProject.get_domain(reponame, domain)
                if issues or ok:
                    await self.send_domain_status(bot, room, reponame, issues, ok)
                else:
                    await bot.send_text(room, f'No labels with domain {domain} found.')
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

    async def send_domain_status(self, bot, room, reponame, issues, ok):
        text_out = GithubProject.domain_to_string(reponame, issues, ok)
        html_out = GithubProject.domain_to_html(reponame, issues, ok)
        await bot.send_html(room, html_out, text_out)


    def help(self):
        return 'Github asset management'

    def get_settings(self):
        data = super().get_settings()
        data["repo_rooms"] = self.repo_rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("repo_rooms"):
            self.repo_rooms = data["repo_rooms"]
