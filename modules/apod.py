import json
import os

import requests
from dateutil import parser
from nio import AsyncClient, UploadError
from nio import UploadResponse

from modules.common.module import BotModule


class Apod:
    def __init__(self, title, explanation, date, hdurl, media_type, url):
        self.hdurl = hdurl
        self.title = title
        self.explanation = explanation
        self.date = date
        self.media_type = media_type
        self.url = url

    @staticmethod
    def create_from_json(json):
        return Apod(json.get("title"), json.get("explanation"), json.get("date"), json.get("hdurl"),
                    json.get("media_type"), json.get("url"))

    def __str__(self):
        return "title: {} || explanation: {} || date: {} || original-url: {}".format(self.title,
                                                                                     self.explanation,
                                                                                     self.date,
                                                                                     self.hdurl)


class MatrixModule(BotModule):

    def __init__(self, name):
        super().__init__(name)
        self.api_key = os.getenv("APOD_API_KEY", "DEMO_KEY")
        self.apod_api_url = f"https://api.nasa.gov/planetary/apod?api_key={self.api_key}&hd=true"
        self.last_update = None
        self.last_apod = None
        self.last_matrix_uri = None

    async def matrix_message(self, bot, room, event):
        self.logger.debug(f"room: {room.name} sender: {event.sender} wants latest astronomy picture of the day")
        await self.send_apod(bot, room)

    async def send_apod(self, bot, room):
        response = requests.get(self.apod_api_url)
        if response.status_code == 200:
            apod = Apod.create_from_json(response.json())
            current_date = parser.parse(apod.date).date()
            self.logger.debug(apod)

            if (self.last_apod is None) or (current_date > self.last_update):
                self.last_apod = apod
                self.last_update = current_date

                if apod.media_type == "image":
                    await self.upload_and_send_image(room, bot, apod)
                else:
                    await self.send_unknown_mediatype(room, bot, apod)
            else:
                self.logger.debug("latest apod already requested. sending last response: %s", self.last_apod)
                if self.last_apod.media_type == "image":
                    await bot.send_image(room, self.last_matrix_uri, self.last_apod.__str__())
                else:
                    await self.send_unknown_mediatype(room, bot, self.last_apod)

        else:
            self.logger.error("unable to request apod api. response: %s", response.text)
            await bot.send_text(room, "sorry. something went wrong accessing the api :(")

    async def send_unknown_mediatype(self, room, bot, apod):
        await bot.send_text(room, f"unsupported media_type: {apod.media_type}")
        await bot.send_text(room, f"title: {apod.title}\n\nexplanation:\n{apod.explanation}\n\nurl: {apod.url}")

    async def upload_and_send_image(self, room, bot, apod):
        url = apod.hdurl if apod.hdurl is not None else apod.url
        matrix_uri = await self.upload_image(bot, url)
        if matrix_uri is not None:
            self.last_matrix_uri = matrix_uri
            bot.save_settings()
            await bot.send_image(room, matrix_uri, apod.__str__())
        else:
            await bot.send_text(room, "sorry. something went wrong uploading the image to matrix server :(")

    async def upload_image(self, bot, url):
        self.client: AsyncClient
        response: UploadResponse
        url_response = requests.get(url)

        if url_response.status_code == 200:
            content_type = url_response.headers.get("content-type")
            (response, alist) = await bot.client.upload(lambda a, b: url_response.content, content_type)

            if isinstance(response, UploadResponse):
                self.logger.debug("uploaded file to %s", response.content_uri)
                return response.content_uri
            else:
                response: UploadError
                self.logger.error("unable to upload file. msg: %s", response.message)
        else:
            self.logger.error("unable to request url: %s", url_response)

        return None

    def get_settings(self):
        data = super().get_settings()
        data["last_update"] = self.last_update.__str__()
        data["last_matrix_uri"] = self.last_matrix_uri
        data["last_apod"] = json.dumps(self.last_apod.__dict__)
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get("last_update"):
            self.last_update = parser.parse(data["last_update"]).date()
        if data.get("last_matrix_uri"):
            self.last_matrix_uri = data["last_matrix_uri"]
        if data.get("last_apod"):
            self.last_apod = Apod.create_from_json(json.loads(data["last_apod"]))

    def help(self):
        return 'Sends latest Astronomy Picture of the Day to the room. (https://apod.nasa.gov/apod/astropix.html)'
