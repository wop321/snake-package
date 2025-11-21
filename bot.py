import discord
import os
from discord import app_commands
from dotenv import load_dotenv

# --- CONFIGURATION & ENV LOADING ---
load_dotenv() # Load variables from the .env file
TOKEN = os.getenv('DISCORD_TOKEN')

DATABASE_FILE = "database.txt"
DELETE_PASSWORD = "abcd980" # The required password for /delete

class MyClient(discord.Client):
    def __init__(self):
        # We only need default intents for slash commands and reading simple files
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        # Syncing the commands so they appear in Discord
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
        # Write the new entry in the requested format
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
        with open(DATABASE_FILE, "rb") as f:
            await interaction.response.send_message(
                "The list is too long to display! Here is the file:", 
                file=discord.File(f, filename="database.txt")
            )
    else:
        # Send as a message
        await interaction.response.send_message(f"**Current Modules:**\n{content}")

# ---------------------------------------------
# --- COMMAND: /delete [name] [password] ---
# ---------------------------------------------
@client.tree.command(name="delete", description="Remove a module using the admin password")
@app_commands.describe(name="The module name to delete", password="The admin password (abcd980)")
async def delete(interaction: discord.Interaction, name: str, password: str):
    # 1. Password Check
    if password != DELETE_PASSWORD:
        await interaction.response.send_message("Incorrect password. Access denied.", ephemeral=True)
        return

    if not os.path.exists(DATABASE_FILE):
        await interaction.response.send_message("Database is empty.", ephemeral=True)
        return

    lines = []
    deleted = False

    # 2. Read all lines
    with open(DATABASE_FILE, "r") as f:
        lines = f.readlines()

    # 3. Rewrite file, skipping the line to be deleted
    with open(DATABASE_FILE, "w") as f:
        for line in lines:
            parts = line.split(' - ')
            if parts and parts[0].strip() == name:
                deleted = True
            else:
                f.write(line)

    # 4. Respond
    if deleted:
        await interaction.response.send_message(f"Successfully deleted module: **{name}**")
    else:
        await interaction.response.send_message(f"Module **{name}** not found.", ephemeral=True)

if TOKEN:
    client.run(TOKEN)
else:
    print("FATAL ERROR: DISCORD_TOKEN not found. Please check your .env file.")
