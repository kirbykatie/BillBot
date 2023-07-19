import os
from dotenv import load_dotenv
import time
from datetime import date, datetime, timedelta
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import discord
from discord.ext import commands, tasks
from parse_message import parse_message


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

sched = AsyncIOScheduler()


async def setup():
    print('Setting up...')
    sched.start()
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
            scheduled_time = get_task_run_date(parsed_reminder.time_type, parsed_reminder.numeral)
            sched.add_job(task, 'date', run_date=scheduled_time,
                          args=[parsed_reminder, message])
    else:
        return


def get_task_run_date(time_type, numeral):
    current_datetime = datetime.now()
    future_datetime = current_datetime + timedelta(seconds=time_type * numeral)
    formatted_datetime = future_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_datetime


async def task(item, message):
    print(item.task, time.strftime('%X (%d/%m/%y)'))
    await message.channel.send(f"{item.task}, {time.strftime('%X (%d/%m/%y)')}", reference=message)


asyncio.run(main())