import discord
from discord import app_commands
import os
import re
# Core Firebase Admin SDK imports
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from keep_alive import keep_alive 

# --- CONFIGURATION ---
ADMIN_PASSWORD = "abcd980"
URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"

# --- FIREBASE SETUP ---
# WARNING: For production, you must configure authentication (e.g., using a 
# Service Account Key JSON file) for this to work outside of environments 
# with default credentials.
try:
    # Attempt to initialize using application default credentials (easiest way in cloud)
    # If this fails, you need to manually load your service account JSON key.
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()
    print("Firestore initialized successfully.")
except Exception as e:
    print(f"FATAL ERROR: Firebase initialization failed. Persistence will not work. Error: {e}")
    db = None

COLLECTION_NAME = 'discord_modules'

# Initialize the in-memory dictionary. This holds the live data, synced with Firestore.
module_database = {} 

# --- FIREBASE HANDLER FUNCTIONS (Persistence) ---

def load_database():
    """Loads all modules from Firestore into the in-memory dictionary."""
    global module_database
    module_database = {} # Clear existing data
    
    if db:
        try:
            modules_ref = db.collection(COLLECTION_NAME).stream()
            for doc in modules_ref:
                data = doc.to_dict()
                if 'url' in data:
                    # Document ID is the module name (e.g., 'python')
                    module_database[doc.id] = data['url']
            print(f"Database loaded successfully from Firestore. {len(module_database)} modules found.")
        except Exception as e:
            print(f"Error loading data from Firestore: {e}")
    else:
        print("Firestore client unavailable. Running with an empty, non-persistent database.")


def add_module_to_firestore(name, url):
    """Adds or updates a module in Firestore."""
    if not db: return False
    try:
        # Use the module name as the document ID for easy lookup
        db.collection(COLLECTION_NAME).document(name).set({'url': url})
        return True
    except Exception as e:
        print(f"Error adding module to Firestore: {e}")
        return False

def delete_module_from_firestore(name):
    """Deletes a module from Firestore."""
    if not db: return False
    try:
        db.collection(COLLECTION_NAME).document(name).delete()
        return True
    except Exception as e:
        print(f"Error deleting module from Firestore: {e}")
        return False


# --- Discord Bot Setup ---

class MyClient(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        # Load data from the persistent source (Firestore)
        load_database()
        
        # Sync commands
        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')


client = MyClient()


# --- COMMAND: /add ---
@client.tree.command(name="add", description="Add a module to the persistent database")
@app_commands.describe(name="Module Name", url="Module Link")
async def add(interaction: discord.Interaction, name: str, url: str):
    if not re.match(URL_REGEX, url):
        await interaction.response.send_message("not an url, skill issue buddy", ephemeral=True)
        return

    if name in module_database:
        await interaction.response.send_message("module already added", ephemeral=True)
    else:
        # Save to Firestore
        if add_module_to_firestore(name, url):
            # Update in-memory dictionary
            module_database[name] = url
            await interaction.response.send_message(f"module upload successful and persistent: **{name}** added.")
        else:
             await interaction.response.send_message("Failed to add module due to database error. Is Firestore configured?", ephemeral=True)


# --- COMMAND: /list ---
@client.tree.command(name="list", description="Show all modules from the persistent database")
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
        # Delete from Firestore
        if delete_module_from_firestore(name):
            # Delete from in-memory dictionary
            del module_database[name]
            await interaction.response.send_message(f"✅ Successfully deleted: **{name}** (Persistent)")
        else:
             await interaction.response.send_message("Failed to delete module due to database error.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ Module **{name}** not found.", ephemeral=True)


# --- START BOT AND KEEP-ALIVE SERVER ---

keep_alive(module_database)

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

if DISCORD_TOKEN is None:
    print("FATAL ERROR: DISCORD_TOKEN environment variable not set.")
    exit()

client.run(DISCORD_TOKEN)
