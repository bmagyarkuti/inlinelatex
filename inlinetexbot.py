import asyncio
import telepot
import telepot.async
from telepot.namedtuple import InlineQueryResultPhoto, InlineQueryResultArticle
import re

import config_reader
import latex_generator


async def compute_answer(msg):
    def get_error_query():
        return [InlineQueryResultArticle(id="latex_start", title='Invalid LaTex',
                                                description="Couldn't parse your input.",
                                                message_text="Sorry, I lost my way around. Didn't mean to send this.", type='article')]
    if len(msg['query']) < 1:   # TODO: maybe not send anything at all?
        results = [InlineQueryResultArticle(id="latex_start", title='Enter LaTeX',
                                            description="Waiting to process your equation. No need to add math mode,"
                                                        "I'll take care of that.",
                                            message_text="Sorry, I lost my way around. Didn't mean to send this.",
                                            type='article')]
    elif re.match(r"\A\\", msg['query']) and not re.match(r"\A\\[a-zA-Z]+\s", msg['query']):
        results = get_error_query()
    else:
        try:
            jpg_url, width, height = await latex_generator.process(str(msg['from']['id']), msg['query'])
        except UnboundLocalError:   # probably failed to generate file
            results = get_error_query()
        else:
            results = [InlineQueryResultPhoto(id='Formatted equation', photo_url=jpg_url,
                                              thumb_url=jpg_url, photo_height=height, photo_width=width)]
    return results


class TexItBot(telepot.async.Bot):
    async def handle(self, msg):
        flavor = telepot.flavor(msg)
        if flavor == 'normal':
            content_type, chat_type, chat_id = telepot.glance(msg, flavor)
            print("Got message %s %s %s" % (content_type, chat_type, chat_id))
            await bot.sendMessage(int(chat_id), "I'm an inline bot. You cannot speak to me directly")
        elif flavor == 'inline_query':
            answerer.answer(msg)


TOKEN = config_reader.token

bot = TexItBot(TOKEN)
answerer = telepot.async.helper.Answerer(bot, compute_answer)

loop = asyncio.get_event_loop()
loop.create_task(bot.messageLoop())
print("Listening...")

loop.run_forever()
