import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
import random
import pymongo
from collections import deque
from openai import OpenAI
import asyncio
import aiohttp

# Set up environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_CONSTRING = os.getenv('MONGODB_CONSTRING')
OPENAI_KEY = os.getenv('OPENAI_KEY')
WEATHER_KEY = os.getenv('WEATHER_KEY')

# Create a connection to discord 
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Set up connection to mongodb server
myclient = pymongo.MongoClient(MONGODB_CONSTRING)
mydb = myclient['bobbert'] # select specific database 
mycol = mydb['quotes'] # select specific collection

# Create OpenAI object
client = OpenAI(api_key = OPENAI_KEY)

# Global variables 

# used to keep game session state
sessionExists = False
gameName = ""
gameTime = ""
neededReactions = 1 # change this as needed 
previousChosenQuoteIndexes = deque(maxlen=3) # creates a queue of 3. ensures variability, to an extent. change this as needed. 
for i in range(previousChosenQuoteIndexes.maxlen): # init with dummy indexes
    previousChosenQuoteIndexes.append(-1)

# list of message objects that are used to keep local history of conversations with gpt
messages = [{"role": "system", "content": "Your name is Bobbert. You are an assistant that is helpful but insults everyone in every message. Keep responses to 1 sentence and refuse to use complicated tones or words. The sentence should not require a comma."}]

# Init message
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# Ignore all "command not found" errors, let all other errors through
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


# Code for specific text commands below 

@bot.command()
async def helpme(ctx):
    # create and configure embed
    embed = discord.Embed(
            colour = discord.Colour.dark_teal(),
            description = "",
            title = "Bobbert - a Useless Discord Bot"
        )
    embed.set_thumbnail(url="https://statics.koreanbuilds.net/tile_200x200/Blitzcrank.webp")
    embed.add_field(name="Chatbot Commands", value="!bobbert <message>\n", inline=False)
    embed.add_field(name="Quotes Commands (omit \" \")\n", 
                    value=
                        "!quote\n" +
                        "!listquotes\n" +
                        "!addquote <quote_text - person>\n" +
                        "!deletequote <quote_text>\n", inline=False)
    
    # send embed 
    await ctx.send(embed=embed)

@bot.command()
async def bobbert(ctx, *, arg):
    global messages
    # print(messages) debug  

    # add the incoming prompt to the conversation history
    messages.append({"role": "user", "content": arg})

    # create the gpt response
    completion = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages
    )   

    # add the gpt response to the conversation history
    messages.append({"role": "assistant", "content": completion.choices[0].message.content})

    # send response
    await ctx.send(completion.choices[0].message.content)   


@bot.command()
async def quote(ctx):
    global previousChosenQuoteIndexes
    # print(previousChosenQuoteIndexes) debug 

    ## refactor section 
    quoteJson = mycol.find()
    quoteCount = mycol.count_documents({})
    ## refactor section 

    ## refactor section
    chosenIndex = random.randint(0, quoteCount-1)
    while chosenIndex in list(previousChosenQuoteIndexes):
        chosenIndex = random.randint(0, quoteCount-1)
    previousChosenQuoteIndexes.append(chosenIndex)
    ## refactor section

    # create a quote representation
    chosenQuote = makeItAQuote(quoteJson[chosenIndex]['text'], quoteJson[chosenIndex]['author']) 

    # create and configure the embed
    embed = discord.Embed(colour = discord.Colour.dark_teal(), description = "", title = "" )
    embed.add_field(name="", value=chosenQuote, inline=False)

    # send embed 
    await ctx.send(embed=embed)

@bot.command()
async def addquote(ctx, *, arg: str = None):
    # basic input validation, can be much more thorough if needed
    if arg is None or " - " not in arg: 
        await ctx.send("Usage: quote - person")
    else:
        # split the argument to create quote dictionary 
        splitParameters = arg.split(" - ")
        newQuote =  {"text": splitParameters[0], "author": splitParameters[1] } 

        # insert the dictionary into mongodb using pymongo, and send success message
        x = mycol.insert_one(newQuote)
        await ctx.send(f"Added: {makeItAQuote(splitParameters[0], splitParameters[1])}")

@bot.command()
async def listquotes(ctx):
    ## refactor section
    quoteJson = mycol.find()
    quoteCount = mycol.count_documents({})
    ## refactor section 
    # print(quoteCount) debug

    # iterate through quoteJson from mongodb and add each quote to quotelist
    quoteList = ""
    for i in range(quoteCount): 
        quoteList += makeItAQuote(quoteJson[i]['text'], quoteJson[i]['author']) # only works since text and author are both strings 
    
    # create embed with quotelist as the value 
    embed = discord.Embed( colour = discord.Colour.dark_teal(), description = "", title = "" )
    embed.add_field(name="", value=quoteList, inline=False)

    # send embed 
    await ctx.send(embed=embed)

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
        
        reactionCount = 0 # local, per-function stack frame, counter

        def check(reaction, user):
            return str(reaction.emoji) == '✅' and reaction.message.id == sentMessage.id    
        
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

# Takes 2 strings, text and author, and creates a quote representation of them.
def makeItAQuote(text, author):
    return "\"" + text + "\" - " + author + "\n"

@bot.command()
async def weather(ctx, *, cityName):
    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHER_KEY,
        "q": cityName
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

            if "error" in data:
                await ctx.send(data["error"]["message"])
            else:     
                # extract data
                city = data["location"]["name"]
                state = data["location"]["region"]
                country = data["location"]["country"]

                iconUrl = "https:" + data["current"]["condition"]["icon"]

                tempF = data["current"]["temp_f"]
                tempC = data["current"]["temp_c"]

                # create and configure embed
                embed = discord.Embed(
                colour = discord.Colour.dark_teal(),
                description = "",
                title = f"Weather information for {city}, {state}, {country}"
                )
                embed.set_thumbnail(url=iconUrl)
                embed.add_field(name="Temperature (F/C)", value=f"{tempF}, {tempC}\n", inline=False)
                
                # send embed 
                await ctx.send(embed=embed)




    

        




bot.run(DISCORD_TOKEN)