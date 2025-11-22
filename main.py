import discord
from discord import app_commands
import os
import re
from keep_alive import keep_alive
# --- CONFIGURATION ---
DATABASE_FILE = "database.txt"
ADMIN_PASSWORD = "abcd980"
URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"


class MyClient(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')


client = MyClient()


# --- COMMAND: /add ---
@client.tree.command(name="add", description="Add a module to the database")
@app_commands.describe(name="Module Name", url="Module Link")
async def add(interaction: discord.Interaction, name: str, url: str):
    # 1. URL Validation Check (The fix you requested)
    if not re.match(URL_REGEX, url):
        await interaction.response.send_message("not an url, skill issue buddy",
                                               ephemeral=True)
        return

    is_duplicate = False

    # 2. Check for duplicates
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            for line in f:
                parts = line.split(' - ')
                if parts and parts[0].strip() == name:
                    is_duplicate = True
                    break

    if is_duplicate:
        await interaction.response.send_message("module already added",
                                               ephemeral=True)
    else:
        # 3. Add to database
        with open(DATABASE_FILE, "a") as f:
            f.write(f"{name} - {url}\n")
        await interaction.response.send_message("module upload successful")


# --- COMMAND: /list ---
@client.tree.command(name="list", description="Show all modules")
async def list_modules(interaction: discord.Interaction):
    if not os.path.exists(DATABASE_FILE) or os.path.getsize(
            DATABASE_FILE) == 0:
        await interaction.response.send_message("The database is empty.",
                                               ephemeral=True)
        return

    with open(DATABASE_FILE, "r") as f:
        content = f.read()

    if len(content) > 1950:
        # Send as file if too long
        with open(DATABASE_FILE, "rb") as f:
            await interaction.response.send_message(
                "List is too long! Here is the file:",
                file=discord.File(f, filename="database.txt"))
    else:
        await interaction.response.send_message(
            f"**Current Modules:**\n{content}")


# --- COMMAND: /delete ---
@client.tree.command(name="delete",
                     description="Delete a module (Password Required)")
@app_commands.describe(name="Module Name to delete", password="Admin Password")
async def delete(interaction: discord.Interaction, name: str, password: str):
    # 1. Verify Password
    if password != ADMIN_PASSWORD:
        await interaction.response.send_message("❌ Incorrect password.",
                                               ephemeral=True)
        return

    if not os.path.exists(DATABASE_FILE):
        await interaction.response.send_message("Database is empty.",
                                               ephemeral=True)
        return

    # 2. Filter the file
    lines = []
    found = False
    with open(DATABASE_FILE, "r") as f:
        lines = f.readlines()

    with open(DATABASE_FILE, "w") as f:
        for line in lines:
            parts = line.split(' - ')
            # Write the line ONLY if the name does NOT match
            if parts and parts[0].strip() == name:
                found = True
            else:
                f.write(line)

    if found:
        await interaction.response.send_message(
            f"✅ Automatically deleted: **{name}**")
    else:
        await interaction.response.send_message(
            f"⚠️ Module **{name}** not found.", ephemeral=True)


keep_alive()

# MODIFIED LINE: Get the token from the environment variable named DISCORD_TOKEN
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# Check if the token was successfully retrieved (good practice)
if DISCORD_TOKEN is None:
    print("FATAL ERROR: DISCORD_TOKEN environment variable not set.")
    exit()

client.run(DISCORD_TOKEN)
