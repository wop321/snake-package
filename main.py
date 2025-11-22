import discord
from discord import app_commands
import os
import re
import json
from keep_alive import keep_alive # Imports the server function

# --- CONFIGURATION ---
ADMIN_PASSWORD = "abcd980"
URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
DATABASE_FILE_JSON = "database.json"

# Initialize the in-memory dictionary
module_database = {}

# --- JSON HANDLER FUNCTIONS (Persistence) ---

def load_database():
    """Loads the dictionary from the JSON file."""
    global module_database
    if os.path.exists(DATABASE_FILE_JSON):
        try:
            with open(DATABASE_FILE_JSON, "r") as f:
                module_database = json.load(f)
            print(f"Database loaded successfully from {DATABASE_FILE_JSON}.")
        except json.JSONDecodeError:
            print("WARNING: Could not decode JSON file. Starting with empty database.")
            module_database = {}
    else:
        print("No existing database file found. Starting fresh.")

def save_database():
    """Saves the current dictionary to the JSON file."""
    with open(DATABASE_FILE_JSON, "w") as f:
        json.dump(module_database, f, indent=4)


class MyClient(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        load_database()
        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')


client = MyClient()


# --- COMMAND: /add ---
@client.tree.command(name="add", description="Add a module to the database")
@app_commands.describe(name="Module Name", url="Module Link")
async def add(interaction: discord.Interaction, name: str, url: str):
    if not re.match(URL_REGEX, url):
        await interaction.response.send_message("not an url, skill issue buddy", ephemeral=True)
        return

    if name in module_database:
        await interaction.response.send_message("module already added", ephemeral=True)
    else:
        module_database[name] = url
        save_database()
        await interaction.response.send_message(f"module upload successful: **{name}** added.")


# --- COMMAND: /list ---
@client.tree.command(name="list", description="Show all modules")
async def list_modules(interaction: discord.Interaction):
    if not module_database:
        await interaction.response.send_message("The database is empty.", ephemeral=True)
        return

    module_list = []
    for name, url in sorted(module_database.items()):
        module_list.append(f"**{name}**: <{url}>")

    content = "\n".join(module_list)

    if len(content) > 1950:
        await interaction.response.send_message(
            "List is too long! Sending as text file.",
            file=discord.File(fp=discord.io.BytesIO(content.encode("utf-8")), filename="modules_list.txt"))
    else:
        await interaction.response.send_message(f"**Current Modules:**\n{content}")


# --- COMMAND: /delete ---
@client.tree.command(name="delete", description="Delete a module (Password Required)")
@app_commands.describe(name="Module Name to delete", password="Admin Password")
async def delete(interaction: discord.Interaction, name: str, password: str):
    if password != ADMIN_PASSWORD:
        await interaction.response.send_message("❌ Incorrect password.", ephemeral=True)
        return

    if name in module_database:
        del module_database[name]
        save_database()
        await interaction.response.send_message(f"✅ Successfully deleted: **{name}**")
    else:
        await interaction.response.send_message(f"⚠️ Module **{name}** not found.", ephemeral=True)


# --- START BOT AND KEEP-ALIVE SERVER ---

# Passes the database reference to the web server
keep_alive(module_database)

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

if DISCORD_TOKEN is None:
    print("FATAL ERROR: DISCORD_TOKEN environment variable not set.")
    exit()

client.run(DISCORD_TOKEN)
