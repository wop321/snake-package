import discord
from discord import app_commands
import os
import re
import aiohttp 
import json 
import asyncio 

# --- NEW: Optional Local Environment Loading ---
try:
    from dotenv import load_dotenv
    # Load variables from local .env file (if running locally)
    load_dotenv()
    print("Environment variables loaded from .env file (if present).")
except ImportError:
    # This is fine if running on a cloud host like Render/Replit
    print("Dotenv not found. Relying on host environment variables.")
    pass
# ---------------------------------------------

# Core Firebase Admin SDK imports
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from keep_alive import keep_alive 

# --- CONFIGURATION ---
ADMIN_PASSWORD = "abcd980"
URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+" 

# --- FIREBASE SETUP ---
try:
    if not firebase_admin._apps:
        # Check if the credentials variable exists
        creds_json = os.environ.get('FIREBASE_CREDENTIALS')
        
        if creds_json:
            # Use credentials from the environment variable (better for deployment)
            print("Database: Attempting initialization using FIREBASE_CREDENTIALS...")
            cred_dict = json.loads(creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback to default (relies on host service account)
            print("Database: FIREBASE_CREDENTIALS not found. Attempting default initialization.")
            firebase_admin.initialize_app()
            
    db = firestore.client()
    print("Firestore initialized successfully.")
except Exception as e:
    # IMPORTANT: The Discord token is needed later, but Firebase failure is logged here.
    print(f"FATAL ERROR: Firebase initialization failed. Persistence will not work. Error: {e}")
    db = None

COLLECTION_NAME = 'discord_git_projects'

# Initialize the in-memory dictionary. This holds the live data, synced with Firestore.
module_database = {} 

# --- HELPER FUNCTION: GITHUB VALIDATION ---

async def check_github_repo_valid(github_path: str) -> bool:
    """Checks if the given GitHub path corresponds to a live repository using an HTTP HEAD request."""
    # Construct the full URL for the repository's main page
    repo_url = f"https://github.com/{github_path}"
    
    # Use aiohttp to make an asynchronous request
    async with aiohttp.ClientSession() as session:
        try:
            # Use HEAD request for efficiency (only checks headers, doesn't download content)
            # GitHub returns 200 for a valid repo and 404 for an invalid one.
            async with session.head(repo_url, allow_redirects=True, timeout=5) as response:
                # 200 means the page exists (is valid)
                return response.status == 200
        except aiohttp.ClientError as e:
            # Catch network/connection issues
            print(f"Aiohttp error during GitHub check for {github_path}: {e}")
            return False
        except Exception as e:
            # Catch other unexpected errors
            print(f"Unexpected error during GitHub check: {e}")
            return False

# --- FIREBASE HANDLER FUNCTIONS (Persistence) ---

def load_database():
    """Loads all projects (Git install commands) from Firestore into the in-memory dictionary."""
    global module_database
    module_database = {} # Clear existing data
    
    if db:
        try:
            modules_ref = db.collection(COLLECTION_NAME).stream()
            for doc in modules_ref:
                data = doc.to_dict()
                if 'url' in data: # 'url' field now stores the full install command string
                    # Document ID is the module name (e.g., 'my_lib')
                    module_database[doc.id] = data['url']
            print(f"Database loaded successfully from Firestore. {len(module_database)} projects found.")
        except Exception as e:
            print(f"Error loading data from Firestore: {e}")
    else:
        print("Firestore client unavailable. Running with an empty, non-persistent database.")


def add_module_to_firestore(name, command):
    """Adds or updates a project (install command) in Firestore."""
    if not db: return False
    try:
        # Store the full command string under the 'url' field
        db.collection(COLLECTION_NAME).document(name).set({'url': command})
        return True
    except Exception as e:
        print(f"Error adding module to Firestore: {e}")
        return False

def delete_module_from_firestore(name):
    """Deletes a project from Firestore."""
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


# --- DEFINE CLIENT (MUST BE BEFORE COMMANDS ARE REGISTERED) ---
client = MyClient()


# --- COMMAND: /add ---
@client.tree.command(name="add", description="Add a GitHub project for easy 'pip install git+' linking")
@app_commands.describe(name="Shortcut Name (e.g., my_project)", github_path="GitHub username/repo (e.g., user/awesome-project)")
async def add(interaction: discord.Interaction, name: str, github_path: str):
    # 1. Validate the GitHub path format (must contain exactly one '/')
    if not re.match(r'^[^/]+/[^/]+$', github_path):
        await interaction.response.send_message("Invalid GitHub path format. Please use 'username/repo-name'.", ephemeral=True)
        return

    # 2. Check if the GitHub repository actually exists (HTTP HEAD request)
    await interaction.response.defer(ephemeral=True, thinking=True) # Acknowledge interaction while checking
    if not await check_github_repo_valid(github_path):
        await interaction.followup.send("❌ Error: That GitHub repository does not appear to be valid or accessible. Please check the path.", ephemeral=True)
        return

    # 3. Construct the full Git install command
    install_command = f"pip install git+https://github.com/{github_path}.git"

    if name in module_database:
        await interaction.followup.send("module already added", ephemeral=True)
    else:
        # 4. Save the full command string to Firestore
        if add_module_to_firestore(name, install_command):
            # Update in-memory dictionary
            module_database[name] = install_command
            await interaction.followup.send(
                f"Project added successfully and verified.\n"
                f"Shortcut: **{name}**\n"
                f"Command: `{install_command}`"
            )
        else:
             await interaction.followup.send("Failed to add project due to database error. Is Firestore configured?", ephemeral=True)


# --- COMMAND: /list ---
@client.tree.command(name="list", description="Show all saved project install commands")
async def list_modules(interaction: discord.Interaction):
    if not module_database:
        await interaction.response.send_message("The database is empty.", ephemeral=True)
        return

    module_list = []
    for name, command in sorted(module_database.items()):
        # Displays the shortcut name and the full install command
        module_list.append(f"**{name}**: `{command}`")

    content = "\n".join(module_list)

    if len(content) > 1950:
        await interaction.response.send_message(
            "List is too long! Sending as text file.",
            file=discord.File(fp=discord.io.BytesIO(content.encode("utf-8")), filename="projects_list.txt"))
    else:
        await interaction.response.send_message(f"**Current Projects (Install Commands):**\n{content}")


# --- COMMAND: /delete ---
@client.tree.command(name="delete", description="Delete a project (Password Required)")
@app_commands.describe(name="Project Name to delete", password="Admin Password")
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
             await interaction.response.send_message("Failed to delete project due to database error.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ Project **{name}** not found.", ephemeral=True)


# --- START BOT AND KEEP-ALIVE SERVER ---

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

if DISCORD_TOKEN is None:
    print("FATAL ERROR: DISCORD_TOKEN environment variable not set.")
    exit()

# The FIX: client is now defined above, so we can use it here.
# Run the Discord bot and the Flask server concurrently using asyncio
client.loop.create_task(keep_alive(module_database))

client.run(DISCORD_TOKEN)
