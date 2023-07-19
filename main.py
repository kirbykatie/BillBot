import os
import discord
from dotenv import load_dotenv
import time
import asyncio
from parse_message import parse_message

from discord.ext import commands, tasks

"""
TODO - so it looks like using Schedule with Discord wont work: 
https://stackoverflow.com/questions/64167141/how-do-i-schedule-a-function-to-run-everyday-at-a-specific-time-in-discord-py
But, the Python Discord bot has Tasks (which are supposed to be used with "Cogs", which idk what those are
https://discordpy.readthedocs.io/en/latest/ext/tasks/
So 1) need to learn about how to use Tasks, but before that, 0.5) I need to get a better understanding of asyncronous processing
This could be a good start: https://realpython.com/async-io-python
"""

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def setup():
    print('Setting up...')
    # Connect to DB and get any tasks that haven't elapsed yet
    # then when the bot is ready, co-currently schedule all the open tasks with asyncio.gather:
    #   https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently


async def main():
    await setup()
    await bot.start(TOKEN)


@bot.command()
async def insult(ctx, request=""):
    if request == "please":
        await ctx.channel.send("Well since you asked so nicely...")
    await ctx.channel.send("Your mother was a hamster and your father smelt of elderberries")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.event
async def on_message(message):
    print(message)
    if message.author == bot.user:
        return
    if message.content[0] == "!":
        await bot.process_commands(message)
        return
    if 'remind me' in message.content.lower():
        parsed_reminder = parse_message(message.content)
        if parsed_reminder is not None:
            msg = await message.channel.send(f"Reminder {parsed_reminder.task} set at {time.strftime('%X (%d/%m/%y)')}")
            print(msg)
            print(parsed_reminder.time_type)
            # define_seconds will return the value of when
            seconds = parsed_reminder.time_type * parsed_reminder.numeral
            asyncio.create_task(task(seconds, parsed_reminder, message))
    else:
        return


async def task(seconds, item, message):
    await asyncio.sleep(seconds)
    print(item.task, time.strftime('%X (%d/%m/%y)'))
    await message.channel.send(f"{item.task}, {time.strftime('%X (%d/%m/%y)')}", reference=message)



asyncio.run(main())
