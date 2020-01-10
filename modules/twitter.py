from twitterscraper import query_tweets_from_user
from modules.common.pollingservice import PollingService

# https://github.com/taspinar/twitterscraper/tree/master/twitterscraper

class MatrixModule(PollingService): 
    service_name = 'Twitter'

    async def poll_implementation(self, bot, account, roomid, send_messages):
        try:
            for tweet in query_tweets_from_user(account, limit=1):
                if tweet.tweet_id not in self.known_ids:
                    if send_messages:
                        await bot.send_html(bot.get_room_by_id(roomid), f'Twitter <a href="https://twitter.com{tweet.tweet_url}">{account}</a>: {tweet.text}', f'Twitter {account}: {tweet.text} - https://twitter.com{tweet.tweet_url}')
                self.known_ids.add(tweet.tweet_id)
        except Exception:
            print('Polling twitter account failed:')
            traceback.print_exc(file=sys.stderr)