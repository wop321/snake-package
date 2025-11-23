import discord
from discord import app_commands
import os
import re
import aiohttp 
import json 
import asyncio # NEW: Import asyncio

# Core Firebase Admin SDK imports
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from keep_alive import keep_alive 

# ... (configuration, FIREBASE SETUP, HELPER FUNCTIONS, and COMMANDS all unchanged) ...

# --- START BOT AND KEEP-ALIVE SERVER ---

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

if DISCORD_TOKEN is None:
    print("FATAL ERROR: DISCORD_TOKEN environment variable not set.")
    exit()

# Run the Discord bot and the Flask server concurrently using asyncio

# The keep_alive function is now called differently: it's scheduled as a task.
# This is a much more stable pattern than using Python's 'threading' module.
client.loop.create_task(keep_alive(module_database))

client.run(DISCORD_TOKEN)
