import os
from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    ActivityHandler
)
from botbuilder.schema import Activity, ActivityTypes

import openai
import asyncio

# Azure OpenAI configuration
openai.api_type = "azure"
openai.api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"
openai.api_key = os.environ.get("AZURE_OPENAI_KEY")
openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")  # Your deployed model name

# Bot credentials
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

class OpenAIBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        user_message = turn_context.activity.text

        # Call Azure OpenAI
        response = openai.ChatCompletion.create(
            engine=openai_deployment,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message['content']
        await turn_context.send_activity(reply)

# Adapter setup
adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)
bot = OpenAIBot()

# Web server setup
async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def aux_func(turn_context):
        await bot.on_turn(turn_context)

    await adapter.process_activity(activity, auth_header, aux_func)
    return web.Response(status=201)

app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    import sys

    try:
        port = int(os.environ.get("PORT", 3978))
        web.run_app(app, host="0.0.0.0", port=port)
    except Exception as error:
        raise error