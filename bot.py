import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive # Import the uptime handler

# --- Configuration ---
load_dotenv()
# Load token securely from a .env file
TOKEN = os.getenv('DISCORD_TOKEN') 
DATABASE_FILE = 'database.txt'
DELETE_PASSWORD = "abcd980"

# --- Bot Setup ---
# We need the message_content intent to read user commands
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Initialize the bot client
bot = commands.Bot(command_prefix='/', intents=intents)

# --- Utility Functions for File Management ---

def load_data():
    """Loads all non-empty lines from the database file."""
    if not os.path.exists(DATABASE_FILE):
        return []
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        # Filter out empty lines and strip whitespace
        return [line.strip() for line in f if line.strip()]

def save_data(data):
    """Saves the current list of data lines to the file."""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(entry + '\n')

# --- Events ---

@bot.event
async def on_ready():
    """Confirms the bot is logged in and ready."""
    print(f'Bot logged in as {bot.user}')
    print('-------------------------------------------')

# --- Commands ---

@bot.command(name='add')
async def add_entry(ctx, name: str, url: str):
    """/add [name] [url]: Adds a new unique entry to the database.txt."""
    
    entries = load_data()
    
    # Check for duplicates based on name (assuming format is always "name - url")
    new_entry_name_prefix = f"{name} - "
    if any(entry.startswith(new_entry_name_prefix) for entry in entries):
        return await ctx.send(f"Error: Entry with name **{name}** already exists.")

    new_entry = f"{name} - {url}"
    entries.append(new_entry)
    save_data(entries)
    
    await ctx.send("✅ Module upload successful.")

@bot.command(name='list')
async def list_entries(ctx):
    """/list: Reads all entries from database.txt and sends them to the user."""
    
    entries = load_data()
    
    if not entries:
        return await ctx.send("The database is currently empty.")

    # 1. Format the list string
    formatted_list = "Module Database Entries:\n"
    for i, full_entry in enumerate(entries, 1):
        formatted_list += f"{i}. {full_entry}\n"
    
    # 2. Handle Discord's character limit (1950 characters as a safe buffer)
    if len(formatted_list) > 1950:
        # Send as a file if it exceeds the limit
        file_path = "module_list.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted_list)
        
        await ctx.send(
            "📚 The module list is too long for a message. Sending as a file:",
            file=discord.File(file_path)
        )
        os.remove(file_path) # Clean up the temporary file
    else:
        # Send directly as a message
        await ctx.send(f"```\n{formatted_list}\n```")


@bot.command(name='delete')
async def delete_entry(ctx, name: str, password: str):
    """/delete [name] [password]: Requires a password check and deletes the entry."""

    # 1. Password check
    if password != DELETE_PASSWORD:
        return await ctx.send("❌ Incorrect password. Deletion failed.")

    entries = load_data()
    
    # Find the full entry string to delete
    entry_to_delete = None
    prefix = f"{name} - "
    
    for entry in entries:
        if entry.startswith(prefix):
            entry_to_delete = entry
            break
            
    if entry_to_delete:
        entries.remove(entry_to_delete)
        save_data(entries)
        await ctx.send(f"🗑️ Successfully deleted entry: **{name}**.")
    else:
        await ctx.send(f"Error: Entry with name **{name}** not found.")

# --- Startup ---

if __name__ == '__main__':
    # Start the Flask web server in a separate thread for uptime monitoring
    keep_alive() 
    
    if TOKEN:
        # Ensure database.txt exists when starting the bot
        if not os.path.exists(DATABASE_FILE):
             print(f"Creating empty {DATABASE_FILE}")
             with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
                 pass
                 
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found. Please create a .env file and set the token.")
