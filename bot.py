import discord
import os
import io
from discord import app_commands
from dotenv import load_dotenv
from keep_alive import keep_alive # Imports the Flask server logic

# --- CONFIGURATION & ENV LOADING ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

DATABASE_FILE = "database.txt" # The local file storage

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------ Ready to accept commands! ------')

client = MyClient()

# ------------------------------
# --- COMMAND: /add [name] [url] ---
# ------------------------------
@client.tree.command(name="add", description="Add a module name and URL to the database")
@app_commands.describe(name="The name of the module", url="The link to the module")
async def add(interaction: discord.Interaction, name: str, url: str):
    is_duplicate = False

    # Check for duplicates by reading the file
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            for line in f:
                parts = line.split(' - ')
                # Check if the name (first part) matches
                if parts and parts[0].strip() == name:
                    is_duplicate = True
                    break

    if is_duplicate:
        await interaction.response.send_message("module already added", ephemeral=True)
    else:
        # Write the new entry in the requested format: name - url
        with open(DATABASE_FILE, "a") as f:
            f.write(f"{name} - {url}\n")
        await interaction.response.send_message("module upload successful")

# ------------------------------
# --- COMMAND: /list ---
# ------------------------------
@client.tree.command(name="list", description="Show all modules in the database")
async def list_modules(interaction: discord.Interaction):
    if not os.path.exists(DATABASE_FILE) or os.path.getsize(DATABASE_FILE) == 0:
        await interaction.response.send_message("The database is currently empty.", ephemeral=True)
        return

    with open(DATABASE_FILE, "r") as f:
        content = f.read()

    # Handle Discord's 2000 character limit
    if len(content) > 1950:
        # Send as a file if the list is too long
        f_io = io.BytesIO(content.encode())
        await interaction.response.send_message(
            "The list is too long to display! Here is the file:", 
            file=discord.File(f_io, filename="database.txt")
        )
    else:
        # Send as a message
        await interaction.response.send_message(f"**Current Modules:**\n{content}")


# ------------------------------
# --- RUN THE BOT ---
# ------------------------------

if TOKEN:
    # START THE FLASK SERVER for 24/7 uptime
    keep_alive() 
    client.run(TOKEN)
else:
    print("FATAL ERROR: DISCORD_TOKEN not found. Please check your .env file.")
