from .common.module import BotModule
import d20

class MatrixModule(BotModule):
  async def matrix_message(self, bot, room, event):
    args = event.body.split()
    args.pop(0)

    if args[0] == 'help':
      await bot.send_text(room, self.long_help())
    else:
      try:
        result = d20.roll(' '.join(args), stringifier=d20.SimpleStringifier())
        await bot.send_text(room, str(result), event=event)
      except:
        await bot.send_text(room, 'Invalid roll syntax', event=event)

  def help(self):
    return 'Rolls dice in XdY format'

  def long_help(self, bot=None, event=None, **kwargs):
    text = self.help() + (
            '\n- "!roll 1d20": roll a single d20'
            '\n- "!roll 1d20+4": A skill check or attack roll'
            '\n- "!roll 1d20+1 adv": A skill check or attack roll with advantage'
            '\n- "!roll 1d20-1 dis": A skill check or attack roll with disadvantage'
            '\n- "!roll help": show this help'
            '\n'
            '\nFor more syntax help, see https://d20.readthedocs.io/en/latest/start.html#dice-syntax')
    return text
