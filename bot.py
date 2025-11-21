import discord
import os
from discord import app_commands
from dotenv import load_dotenv
from flask import Flask  # <-- NEW
from threading import Thread # <-- NEW

# --- CONFIGURATION & ENV LOADING ---
load_dotenv() 
TOKEN = os.getenv('DISCORD_TOKEN')

DATABASE_FILE = "database.txt"
DELETE_PASSWORD = "abcd980"

# ------------------------------
# --- FLASK KEEP-ALIVE FUNCTIONS ---
# ------------------------------
app = Flask('')

@app.route('/')
def home():
    """A simple endpoint that reports the bot is running."""
    return "Bot is running!"

def run():
    """Starts the Flask server on a separate thread."""
    # Use 0.0.0.0 and port 8080 or 5000, depending on your hosting provider's default
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Initializes and starts the Flask thread."""
    t = Thread(target=run)
    t.start()
# ------------------------------

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
# --- COMMANDS (/add, /list, /delete) ---
# (The code for the commands is unchanged, shown simplified for brevity)
# ------------------------------

# --- /add [name] [url] ---
@client.tree.command(name="add", description="Add a module name and URL to the database")
@app_commands.describe(name="The name of the module", url="The link to the module")
async def add(interaction: discord.Interaction, name: str, url: str):
    is_duplicate = False
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            for line in f:
                parts = line.split(' - ')
                if parts and parts[0].strip() == name:
                    is_duplicate = True
                    break
    if is_duplicate:
        await interaction.response.send_message("module already added", ephemeral=True)
    else:
        with open(DATABASE_FILE, "a") as f:
            f.write(f"{name} - {url}\n")
        await interaction.response.send_message("module upload successful")

# --- /list ---
@client.tree.command(name="list", description="Show all modules in the database")
async def list_modules(interaction: discord.Interaction):
    if not os.path.exists(DATABASE_FILE) or os.path.getsize(DATABASE_FILE) == 0:
        await interaction.response.send_message("The database is currently empty.", ephemeral=True)
        return
    with open(DATABASE_FILE, "r") as f:
        content = f.read()
    if len(content) > 1950:
        import io
        f_io = io.BytesIO(content.encode())
        await interaction.response.send_message(
            "The list is too long! Here is the file:", 
            file=discord.File(f_io, filename="database.txt")
        )
    else:
        await interaction.response.send_message(f"**Current Modules:**\n{content}")

# --- /delete [name] [password] ---
@client.tree.command(name="delete", description="Remove a module using the admin password")
@app_commands.describe(name="The module name to delete", password="The admin password (abcd980)")
async def delete(interaction: discord.Interaction, name: str, password: str):
    if password != DELETE_PASSWORD:
        await interaction.response.send_message("Incorrect password.", ephemeral=True)
        return
    if not os.path.exists(DATABASE_FILE):
        await interaction.response.send_message("Database is empty.", ephemeral=True)
        return
    lines = []
    deleted = False
    with open(DATABASE_FILE, "r") as f:
        lines = f.readlines()
    with open(DATABASE_FILE, "w") as f:
        for line in lines:
            parts = line.split(' - ')
            if parts and parts[0].strip() == name:
                deleted = True
            else:
                f.write(line)
    if deleted:
        await interaction.response.send_message(f"Successfully deleted module: **{name}**")
    else:
        await interaction.response.send_message(f"Module **{name}** not found.", ephemeral=True)

# ------------------------------
# --- RUN THE BOT ---
# ------------------------------

if TOKEN:
    # START THE FLASK SERVER BEFORE STARTING THE BOT
    keep_alive() # <-- CALLING THE NEW FUNCTION
    client.run(TOKEN)
else:
    print("FATAL ERROR: DISCORD_TOKEN not found. Please check your .env file.")
