import discord
import os
from dotenv import load_dotenv

# Set up environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Create a connection to discord 
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

sessionExists = False
gameName = ""
gameTime = ""

# Event registers 
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    global sessionExists
    global gameName
    global gameTime

    if message.author == client.user:
        return

    # The text content of the message  
    msg = message.content 

    # Chat section
    if msg == "!bobbert":
        await message.channel.send("Hello!")
    
    # Quote section
    elif msg == "!quote":
        await message.channel.send("showing random quote")
    
    elif msg == "!quoteadd":
        await message.channel.send("quoteadd")
    
    elif msg == "!quotelist":
        await message.channel.send("quotelist")

    elif msg == "!quotedelete":
        await message.channel.send("quotedelete")


    # Session section
    elif msg == "!session":
        if(sessionExists):
            await message.channel.send(f"Show up to {gameName} @ {gameTime}!")
        else:
            await message.channel.send("There's no scheduled session!")

    
    elif msg.startswith("!sessionadd"):
        if len(msg) == 11:
            await message.channel.send("Usage: <game> at <time>PM")

        elif(sessionExists):
            await message.channel.send("Session already exists, run !sessionend to cancel.")
        
        else:
            if "at" not in msg:
                await message.channel.send("Usage: <game> at <time>PM")
            else:
                sessionExists = True
                parameters = msg[11:]
                splitParameters = parameters.split(" at ")
                gameName = splitParameters[0].strip()
                gameTime = splitParameters[1].strip()
                await message.channel.send(f"Scheduled {gameName}, {gameTime}.")

    elif msg.startswith("!sessionend"):
        if(sessionExists):
            sessionExists = False
            #remove roles 
            await message.channel.send(f"Ended/cancelled {gameName} @ {gameTime}.")
        else:
            await message.channel.send("There's no scheduled session!")


client.run(DISCORD_TOKEN)