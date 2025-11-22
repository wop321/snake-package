import discord
from discord import app_commands
import os
import re
import sqlite3 # New import for persistent database handling
from keep_alive import keep_alive # Imports the server function

# --- CONFIGURATION ---
ADMIN_PASSWORD = "abcd980"
URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
DATABASE_FILE_SQLITE = "modules.db" # Database file for persistent storage

# Initialize the in-memory dictionary. This holds the live data, synced with SQLite.
module_database = {} 

# --- SQLITE HANDLER FUNCTIONS (Persistence) ---

def initialize_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE_SQLITE)
    cursor = conn.cursor()
    # Create the modules table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            name TEXT PRIMARY KEY,
            url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    
def load_database():
    """Loads all modules from the SQLite database into the in-memory dictionary."""
    global module_database
    module_database = {} # Clear existing data
    
    conn = sqlite3.connect(DATABASE_FILE_SQLITE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, url FROM modules")
    
    for name, url in cursor.fetchall():
        module_database[name] = url
        
    conn.close()
    print(f"Database loaded successfully. {len(module_database)} modules found.")

def execute_db_change(query, params=()):
    """Executes an INSERT, UPDATE, or DELETE query and returns success status."""
    conn = sqlite3.connect(DATABASE_FILE_SQLITE)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

# --- Discord Bot Setup ---

class MyClient(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        # 1. Initialize DB structure and load data
        initialize_db()
        load_database()
        
        # 2. Sync commands
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

    # Check for duplicates in memory (faster check)
    if name in module_database:
        await interaction.response.send_message("module already added", ephemeral=True)
    else:
        # Add to SQLite
        query = "INSERT INTO modules (name, url) VALUES (?, ?)"
        if execute_db_change(query, (name, url)):
            # Update in-memory dictionary only on success
            module_database[name] = url
            await interaction.response.send_message(f"module upload successful: **{name}** added.")
        else:
             await interaction.response.send_message("Failed to add module due to a database error.", ephemeral=True)


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
        # For long lists, we still send a text file buffer
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
        # Delete from SQLite
        query = "DELETE FROM modules WHERE name = ?"
        if execute_db_change(query, (name,)):
            # Delete from in-memory dictionary only on success
            del module_database[name]
            await interaction.response.send_message(f"✅ Successfully deleted: **{name}**")
        else:
             await interaction.response.send_message("Failed to delete module due to a database error.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ Module **{name}** not found.", ephemeral=True)


# --- START BOT AND KEEP-ALIVE SERVER ---

# Pass the module_database dictionary as the required positional argument.
keep_alive(module_database)

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

if DISCORD_TOKEN is None:
    print("FATAL ERROR: DISCORD_TOKEN environment variable not set.")
    exit()

client.run(DISCORD_TOKEN)
