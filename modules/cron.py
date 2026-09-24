import re
import shlex
import os
from datetime import datetime, timedelta

from croniter import croniter

from .common.module import BotModule


class MatrixModule(BotModule):
    """Schedule room messages / bot commands with cron expressions."""

    daily_commands = dict()  # room_id -> list of job dicts
    _last_fired = dict()  # job_key -> YYYYMMDDHHMM

    async def matrix_message(self, bot, room, event):
        bot.must_be_admin(room, event)

        args = shlex.split(event.body)
        args.pop(0)

        if not args:
            await bot.send_text(room, self.long_help(), event=event)
            return

        cmd = args[0]

        if cmd == 'add' and len(args) >= 3:
            # !cron add "<expr>" "<command>"
            # !cron add <min> <hour> <dom> <mon> <dow> <command>
            if len(args) == 3:
                expr, command = args[1], args[2]
            elif len(args) >= 7:
                expr = ' '.join(args[1:6])
                command = ' '.join(args[6:])
            else:
                await bot.send_text(
                    room,
                    'Usage: !cron add "<min hour dom mon dow>" "<command>"',
                    event=event,
                )
                return

            if not self._valid_cron(expr):
                await bot.send_text(room, f'Invalid cron expression: {expr}', event=event)
                return

            self._jobs(room.room_id).append({'cron': expr, 'command': command})
            bot.save_settings()
            await bot.send_text(room, f'Cron job added: `{expr}` → {command}', event=event)
            return

        if cmd == 'once' and len(args) >= 3:
            # !cron once 10m "reminder"
            # !cron once "2026-09-24 15:30" "reminder"
            when_raw, command = args[1], ' '.join(args[2:])
            try:
                when = self._parse_once(when_raw)
            except ValueError as exc:
                await bot.send_text(room, str(exc), event=event)
                return

            if when <= datetime.now():
                await bot.send_text(room, 'Time must be in the future.', event=event)
                return

            self._jobs(room.room_id).append({
                'once': when.isoformat(timespec='seconds'),
                'command': command,
            })
            bot.save_settings()
            await bot.send_text(
                room,
                f'One-shot reminder set for {when.isoformat(sep=" ", timespec="seconds")} → {command}',
                event=event,
            )
            return

        if cmd == 'daily' and len(args) == 3:
            # Backwards compatible: !cron daily 19 "msg" → 0 19 * * *
            try:
                hour = int(args[1])
            except ValueError:
                await bot.send_text(room, 'Hour must be an integer 0-23', event=event)
                return
            if hour < 0 or hour > 23:
                await bot.send_text(room, 'Hour must be 0-23', event=event)
                return

            expr = f'0 {hour} * * *'
            command = args[2]
            self._jobs(room.room_id).append({'cron': expr, 'command': command, 'time': hour})
            bot.save_settings()
            await bot.send_text(
                room,
                f'Daily command added (cron `{expr}`): {command}',
                event=event,
            )
            return

        if cmd == 'remove' and len(args) == 2:
            jobs = self._jobs(room.room_id)
            try:
                idx = int(args[1])
            except ValueError:
                await bot.send_text(room, 'Usage: !cron remove <index>', event=event)
                return
            if idx < 0 or idx >= len(jobs):
                await bot.send_text(room, f'No job at index {idx}', event=event)
                return
            removed = jobs.pop(idx)
            if not jobs:
                self.daily_commands.pop(room.room_id, None)
            bot.save_settings()
            await bot.send_text(
                room,
                f'Removed job {idx}: `{self._describe(removed)}` → {removed.get("command")}',
                event=event,
            )
            return

        if cmd == 'list' and len(args) == 1:
            jobs = self.daily_commands.get(room.room_id) or []
            if not jobs:
                await bot.send_text(room, 'No cron jobs in this room.', event=event)
                return
            lines = []
            for i, job in enumerate(jobs):
                lines.append(f'{i}: `{self._describe(job)}` → {job.get("command")}')
            await bot.send_text(room, 'Cron jobs in this room:\n' + '\n'.join(lines), event=event)
            return

        if cmd == 'clear' and len(args) == 1:
            self.daily_commands.pop(room.room_id, None)
            bot.save_settings()
            await bot.send_text(room, 'Cleared cron jobs in this room.', event=event)
            return

        if cmd == 'time' and len(args) == 1:
            await bot.send_text(
                room,
                '{datetime} {timezone}'.format(
                    datetime=datetime.now(),
                    timezone=os.environ.get('TZ'),
                ),
                event=event,
            )
            return

        await bot.send_text(room, self.long_help(), event=event)

    def help(self):
        return 'Runs scheduled commands (cron expressions)'

    def long_help(self, bot=None, room=None, event=None, args=[]):
        return (
            'Schedule commands with standard 5-field cron (min hour dom mon dow).\n'
            '!cron add "*/5 * * * *" "hello" — every 5 minutes\n'
            '!cron add "0 9 * * 1-5" "!echo weekday morning" — weekdays 09:00\n'
            '!cron once 10m "drink water" — one-shot in 10 minutes\n'
            '!cron once "2026-12-24 18:00" "party" — one-shot at absolute time\n'
            '!cron daily 19 "It is 19 o clock" — shorthand for 0 19 * * *\n'
            '!cron list — show jobs\n'
            '!cron remove <index> — remove job by index from !cron list\n'
            '!cron clear / !cron time\n'
            'Timezone from TZ env (see !cron time). Room admin required.'
        )

    def get_settings(self):
        data = super().get_settings()
        data['daily_commands'] = self.daily_commands
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('daily_commands'):
            self.daily_commands = data['daily_commands']

    async def matrix_poll(self, bot, pollcount):
        now = datetime.now()
        now_minute = now.replace(second=0, microsecond=0)
        minute_key = now_minute.strftime('%Y%m%d%H%M')
        delete_rooms = []
        settings_dirty = False

        for room_id, jobs in list(self.daily_commands.items()):
            if room_id not in bot.client.rooms:
                delete_rooms.append(room_id)
                continue

            room = bot.get_room_by_id(room_id)
            remaining = []

            for idx, job in enumerate(jobs):
                if job.get('once'):
                    try:
                        when = datetime.fromisoformat(job['once'])
                    except ValueError:
                        self.logger.error('Invalid once timestamp in %s: %s', room_id, job)
                        continue

                    if now < when:
                        remaining.append(job)
                        continue

                    try:
                        await bot.send_text(room, job['command'], msgtype='m.text')
                    except Exception:
                        self.logger.exception('Failed to run once job in %s: %s', room_id, job)
                        remaining.append(job)
                        continue

                    settings_dirty = True
                    continue

                expr = self._expr(job)
                remaining.append(job)
                if not self._valid_cron(expr):
                    continue
                if not croniter.match(expr, now_minute):
                    continue

                key = f'{room_id}:{idx}:{expr}:{job.get("command")}'
                if self._last_fired.get(key) == minute_key:
                    continue
                self._last_fired[key] = minute_key

                try:
                    await bot.send_text(room, job['command'], msgtype='m.text')
                except Exception:
                    self.logger.exception('Failed to run cron job in %s: %s', room_id, job)

            if len(remaining) != len(jobs):
                settings_dirty = True
            if remaining:
                self.daily_commands[room_id] = remaining
            else:
                self.daily_commands.pop(room_id, None)
                settings_dirty = True

        for room_id in delete_rooms:
            self.daily_commands.pop(room_id, None)
            settings_dirty = True

        if settings_dirty:
            bot.save_settings()

    def _jobs(self, room_id):
        if room_id not in self.daily_commands:
            self.daily_commands[room_id] = []
        return self.daily_commands[room_id]

    @staticmethod
    def _expr(job):
        if job.get('cron'):
            return job['cron']
        # Legacy daily jobs: {"time": hour, "command": "..."}
        if 'time' in job:
            return f'0 {int(job["time"])} * * *'
        return ''

    @classmethod
    def _describe(cls, job):
        if job.get('once'):
            return f'once @ {job["once"]}'
        return cls._expr(job)

    @staticmethod
    def _valid_cron(expr):
        try:
            croniter(expr)
            return True
        except (ValueError, KeyError, TypeError):
            return False

    @staticmethod
    def _parse_once(when_raw):
        """Parse relative (10m, 1h30m, 45s) or absolute datetime."""
        relative = re.fullmatch(
            r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?',
            when_raw.strip(),
            re.IGNORECASE,
        )
        if relative and when_raw.strip() and any(relative.groups()):
            days, hours, minutes, seconds = (int(x or 0) for x in relative.groups())
            delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            if delta.total_seconds() <= 0:
                raise ValueError('Duration must be > 0 (e.g. 10m, 1h, 30s)')
            return datetime.now() + delta

        formats = (
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%H:%M:%S',
            '%H:%M',
        )
        for fmt in formats:
            try:
                parsed = datetime.strptime(when_raw, fmt)
            except ValueError:
                continue
            if fmt in ('%H:%M', '%H:%M:%S'):
                today = datetime.now()
                parsed = parsed.replace(
                    year=today.year, month=today.month, day=today.day
                )
                if parsed <= today:
                    parsed += timedelta(days=1)
            return parsed

        raise ValueError(
            'Usage: !cron once 10m "msg" or !cron once "YYYY-MM-DD HH:MM" "msg"'
        )
