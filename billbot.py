import asyncio
import math
import os
from datetime import timedelta
from random import random

import arrow
import discord
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
from dotenv import load_dotenv

from bill_responses import reminderAcknowledgement
from parse_message import parse_message

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

jobstores = {
    "default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite", tablename="tasks")
}
sched = AsyncIOScheduler({'apscheduler.timezone': 'US/Central'}, jobstores=jobstores)


async def setup():
    sched.start()
    sched.print_jobs()
    # Connect to DB and get any tasks that haven't elapsed yet
    # then when the bot is ready, co-currently schedule all the open tasks with asyncio.gather:
    #   https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently


@bot.command()
async def insult(ctx, request=""):
    if request == "please":
        await ctx.channel.send("Well, since you asked so nicely...")
    await ctx.channel.send(
        "Your mother was a hamster and your father smelt of elderberries"
    )


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content[0] == "!":
        await bot.process_commands(message)
        return
    if "remind me" in message.content.lower():
        parsed_reminder = parse_message(message.content)
        if parsed_reminder is not None:
            print("Received reminder")
            created_at = arrow.get(message.created_at)
            # TODO - add logic to set timezone based on user
            scheduled_time = get_task_run_date(
                parsed_reminder.time_type, parsed_reminder.numeral, created_at
            ).to("US/Central")
            scheduled_time_str = scheduled_time.format("YYYY-MM-DD HH:mm:ss")
            message_ref = message.to_reference()

            try:
                sched.add_job(
                    task,
                    "date",
                    id=scheduled_time_str,
                    run_date=scheduled_time_str,
                    args=[
                        parsed_reminder,
                        message_ref.message_id,
                        message_ref.channel_id,
                        message_ref.guild_id,
                        created_at.to("US/Central"),
                    ],
                )
                confirmation_response = get_confirmation_response(
                    message.author.name, scheduled_time
                )
                await message.channel.send(confirmation_response)
                print("Reminder made")
            except Exception as e:
                print(f"Error adding job: {e}")
    else:
        return


def get_task_run_date(time_type, numeral, created_at):
    future_datetime = created_at + timedelta(seconds=time_type * numeral)
    future_datetime = arrow.get(future_datetime)
    return future_datetime


def get_confirmation_response(author, reminder_time):
    random_res = reminderAcknowledgement[
        math.floor(random() * len(reminderAcknowledgement))
    ]
    random_res = random_res.replace("<$user$>", author)
    return f"{random_res} ({reminder_time.humanize(only_distance=True)} | <t:{reminder_time.format('X')[:10]}:f>)"


async def task(item, message_id, channel_id, guild_id, original_time):
    message_ref = discord.MessageReference(
        message_id=message_id, channel_id=channel_id, guild_id=guild_id
    )
    channel = bot.get_channel(channel_id)
    await channel.send(
        f"{item.task} ({original_time.humanize()})", reference=message_ref
    )


# Create an event loop and run the bot within it
loop = asyncio.get_event_loop()
try:
    print("Setting up...")
    loop.create_task(setup())
    loop.create_task(bot.start(TOKEN))
    loop.run_forever()
except (KeyboardInterrupt, SystemExit):
    sched.shutdown(
        wait=True
    )  # Properly shut down the scheduler and save jobs to the database
    loop.run_until_complete(
        bot.close()
    )  # Close the bot gracefully before exiting the script
    print("Have successfully shut down")
finally:
    loop.close()
