import discord
import os
from discord import app_commands
from dotenv import load_dotenv
from keep_alive import keep_alive # <-- NEW IMPORT

# --- CONFIGURATION & ENV LOADING ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

DATABASE_FILE = "database.txt"
DELETE_PASSWORD = "abcd980"

# (The MyClient class, on_ready, and all command functions /add, /list, /delete remain unchanged)

class MyClient(discord.Client):
    # ... (init and on_ready functions unchanged) ...
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------ Ready to accept commands! ------')

client = MyClient()

# ... (Insert the full code for the /add, /list, and /delete commands here) ...

# ---------------------------------------------
# --- COMMAND: /add ---
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

# --- COMMAND: /list ---
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

# --- COMMAND: /delete ---
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
    # START THE FLASK SERVER (imported from keep_alive.py)
    keep_alive() # <-- THE ONLY CHANGE IN THE RUN BLOCK
    client.run(TOKEN)
else:
    print("FATAL ERROR: DISCORD_TOKEN not found. Please check your .env file.")
