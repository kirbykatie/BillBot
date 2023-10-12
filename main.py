import os

from apscheduler.jobstores.memory import MemoryJobStore
from dotenv import load_dotenv
import time
from datetime import date, datetime, timedelta
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import discord
from discord.ext import commands, tasks
from parse_message import parse_message

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite', tablename="tasks")
}
sched = AsyncIOScheduler(jobstores=jobstores)


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
    await ctx.channel.send("Your mother was a hamster and your father smelt of elderberries")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content[0] == "!":
        await bot.process_commands(message)
        return
    if 'remind me' in message.content.lower():
        parsed_reminder = parse_message(message.content)
        if parsed_reminder is not None:
            await message.channel.send(f"Reminder {parsed_reminder.task} set at {time.strftime('%X (%d/%m/%y)')}")
            scheduled_time = get_task_run_date(parsed_reminder.time_type, parsed_reminder.numeral)
            message_ref = message.to_reference()
            try:
                sched.add_job(task, 'date', id=scheduled_time, run_date=scheduled_time, args=[parsed_reminder,
                                                                                              message_ref.message_id,
                                                                                              message_ref.channel_id,
                                                                                              message_ref.guild_id])
                print("Job made")
            except Exception as e:
                print(f"Error adding job: {e}")
    else:
        return


def get_task_run_date(time_type, numeral):
    current_datetime = datetime.now()
    future_datetime = current_datetime + timedelta(seconds=time_type * numeral)
    formatted_datetime = future_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_datetime


async def task(item, message_id, channel_id, guild_id):
    print(item.task, time.strftime('%X (%d/%m/%y)'))
    message_ref = discord.MessageReference(message_id=message_id, channel_id=channel_id, guild_id=guild_id)
    channel = bot.get_channel(channel_id)
    await channel.send(f"{item.task}, {time.strftime('%X (%d/%m/%y)')}", reference=message_ref)


# Create an event loop and run the bot within it
loop = asyncio.get_event_loop()
try:
    print('Setting up...')
    loop.create_task(setup())
    loop.create_task(bot.start(TOKEN))
    loop.run_forever()
except (KeyboardInterrupt, SystemExit):
    sched.shutdown(wait=True)  # Properly shut down the scheduler and save jobs to the database
    loop.run_until_complete(bot.close())  # Close the bot gracefully before exiting the script
    print("Have successfully shut down")
finally:
    loop.close()
