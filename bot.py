import discord
from discord import app_commands
import os

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'Logged in as {self.user}')

client = MyClient()

# --- COMMAND: /add ---
@client.tree.command(name="add", description="Add a module to the database")
@app_commands.describe(name="The name of the module", url="The link to the module")
async def add(interaction: discord.Interaction, name: str, url: str):
    filename = "database.txt"
    is_duplicate = False

    # Check for duplicates
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                parts = line.split(' - ')
                if parts and parts[0].strip() == name:
                    is_duplicate = True
                    break

    if is_duplicate:
        await interaction.response.send_message("module already added", ephemeral=True)
    else:
        with open(filename, "a") as f:
            f.write(f"{name} - {url}\n")
        await interaction.response.send_message("module upload successful")

# --- COMMAND: /list ---
@client.tree.command(name="list", description="Show all modules in the database")
async def list_modules(interaction: discord.Interaction):
    filename = "database.txt"

    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        await interaction.response.send_message("The database is currently empty.", ephemeral=True)
        return

    with open(filename, "r") as f:
        content = f.read()

    if len(content) > 1950:
        with open(filename, "rb") as f:
            await interaction.response.send_message(
                "The list is too long to display! Here is the file:",
                file=discord.File(f, filename="database.txt")
            )
    else:
        await interaction.response.send_message(f"**Current Modules:**\n{content}")

# --- COMMAND: /delete ---
@client.tree.command(name="delete", description="Remove a module using a password")
@app_commands.describe(name="The module name to delete", password="The admin password")
async def delete(interaction: discord.Interaction, name: str, password: str):
    filename = "database.txt"
    ADMIN_PASSWORD = "abcd980"

    # 1. Check Password
    if password != ADMIN_PASSWORD:
        await interaction.response.send_message("Incorrect password. Access denied.", ephemeral=True)
        return

    # 2. Check if file exists
    if not os.path.exists(filename):
        await interaction.response.send_message("Database is empty.", ephemeral=True)
        return

    # 3. Read lines and filter out the one to delete
    lines = []
    deleted = False

    with open(filename, "r") as f:
        lines = f.readlines()

    with open(filename, "w") as f:
        for line in lines:
            parts = line.split(' - ')
            # If the name matches, we skip writing it (deleting it)
            if parts and parts[0].strip() == name:
                deleted = True
            else:
                f.write(line)

    # 4. Respond
    if deleted:
        await interaction.response.send_message(f"Successfully deleted module: **{name}**")
    else:
        await interaction.response.send_message(f"Module **{name}** not found.", ephemeral=True)

client.run('nigga')
