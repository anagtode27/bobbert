import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Set up environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Create a connection to discord 
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables used to keep state
sessionExists = False
gameName = ""
gameTime = ""
neededReactions = 1 #change this as needed 

# Init message
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# Ignore all "command not found" errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

# Code for specific commands below 

@bot.command()
async def gethelp(ctx):
    embed = discord.Embed(
            colour = discord.Colour.dark_teal(),
            description = "",
            title = "Bobbert: useless discord bot"
        )
    embed.set_thumbnail(url="https://statics.koreanbuilds.net/tile_200x200/Blitzcrank.webp")
    embed.add_field(name="Chatbot", value="!chat [message]: talk to Bobbert!", inline=False)
    embed.add_field(name="Quotes (inspired by Gain Wisdom)", value=
                        "!quote: shows a random quote\n" +
                        "!quoteadd [\"quote\" - person]: adds a quote\n"
                        "!quotelist: lists all quotes\n" +
                        "!quotedelete [id]: deletes a specific quote, by ID\n", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def chat(ctx):
    await ctx.send("Hello!")

@bot.command()
async def quote(ctx):
    await ctx.send("showing random quote")

@bot.command()
async def addquote(ctx):
    await ctx.send("quoteadd")

@bot.command()
async def quotelist(ctx):
    await ctx.send("quotelist")

@bot.command()
async def deletequote(ctx):
    await ctx.send("quotedelete")

@bot.command()
async def session(ctx):
    global sessionExists
    global gameName
    global gameTime
    if(sessionExists):
        await ctx.send(f"Show up to {gameName} @ {gameTime}!")
    else:
        await ctx.send("There's no scheduled session!")

@bot.command()
async def newsession(ctx, *, arg: str = None):
    global sessionExists
    global gameName
    global gameTime
    global neededReactions

    if arg is None or "at" not in arg:
        await ctx.send("Usage: [video game] at [time]")
    elif sessionExists:
        await ctx.send("Session already exists, run !sessionend to cancel.")
    else:
        splitParameters = arg.split(" at ")
        tentativeGameName = splitParameters[0].strip()
        tentativeGameTime = splitParameters[1].strip()

        sentMessage = await ctx.send(f"@everyone Who wants to play {tentativeGameName} @ {tentativeGameTime}?")

        def check(reaction, user):
            return str(reaction.emoji) == '✅' and reaction.message.id == sentMessage.id
        
        reactionCount = 0

        while reactionCount < neededReactions:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=None)
            reactionCount += 1
            if reactionCount == 1:
                await ctx.send(f"We have {reactionCount} vote for {tentativeGameName}!")   
            else: 
                await ctx.send(f"We have {reactionCount} votes for {tentativeGameName}!") 

        sessionExists = True
        gameName = tentativeGameName
        gameTime = tentativeGameTime
        await ctx.send(f"Scheduled {gameName} @ {gameTime}!")              

@bot.command()
async def endsession(ctx):
    global sessionExists
    global gameName
    global gameTime

    if(sessionExists):
        #remove roles 
        await ctx.send(f"Ended/cancelled {gameName} @ {gameTime}.")
        gameName = ""
        gameTime = ""
        sessionExists = False
    else:
        await ctx.send("There's no scheduled session!")

bot.run(DISCORD_TOKEN)