import os 
from flask import Flask, redirect, abort, Response
import asyncio 

# Global variable to hold the reference to the Discord bot's live module database.
global_module_database = {}

app = Flask(__name__)

@app.route('/')
def home():
    """
    The main route. It generates an HTML page listing all available shortcuts
    from the in-memory database dictionary (synced from Firestore).
    This serves as the public, viewable database.
    """
    names = sorted(global_module_database.keys())
    
    if not names:
        return Response(
            """
            <!DOCTYPE html>
            <html><head><title>Project Redirect Server</title></head>
            <body><h1>No Projects Found</h1><p>The server is running, but the database is empty. Add projects using the Discord bot's /add command!</p></body>
            </html>
            """,
            mimetype='text/html'
        )

    # Generate an HTML list of all available shortcuts
    html_list = "<ul>" + "".join([
        f'<li><a href="/{name}" class="font-mono bg-blue-100 text-blue-800 p-2 rounded-lg hover:bg-blue-200">{name}</a></li>' 
        for name in names
    ]) + "</ul>"
    
    # Use Tailwind CSS classes for a simple, mobile-friendly design
    return Response(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Project Redirect Server</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{ font-family: 'Inter', sans-serif; }}
            </style>
        </head>
        <body class="bg-gray-50 min-h-screen flex flex-col items-center p-4">
            <div class="max-w-xl w-full bg-white shadow-xl rounded-2xl p-6 md:p-10 mt-10">
                <h1 class="text-3xl font-extrabold text-gray-900 mb-2">Project Shortcut Database</h1>
                <p class="text-gray-600 mb-6">
                    This is a live, persistent list of all projects saved via the Discord bot. 
                    Click a shortcut name to get the direct <code>pip install</code> command.
                </p>
                
                <h2 class="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Available Shortcuts ({len(names)})</h2>
                
                <div class="space-y-3">
                    {html_list}
                </div>

                <div class="mt-8 pt-4 border-t text-sm text-gray-500">
                    <p>To use, type the following into your terminal, replacing [site.com] with this server's URL:</p>
                    <p class="font-mono bg-gray-100 p-2 rounded-lg mt-2 text-gray-700">
                        pip install <a href="#" class="underline">https://[site.com]/[shortcut-name]</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """,
        mimetype='text/html'
    )

@app.route('/<name>')
def redirect_to_url(name):
    """
    Looks up the 'name' (shortcut) in the database and redirects the user
    to the associated Git install command URL.
    """
    url = global_module_database.get(name)
    
    if url:
        return redirect(url, code=302)
    else:
        return abort(404, description=f"Module '{name}' not found in the persistent database.")


def run_flask_server():
    """Blocking function to start the Flask server."""
    # Use 0.0.0.0 and the PORT environment variable expected by hosting services
    print("Attempting to start Flask server on 0.0.0.0...")
    # By setting threaded=True, we rely on Flask's internal threading, 
    # but still offload the main blocking call via the executor.
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080), debug=False, threaded=True)


async def keep_alive(client, db_reference):
    """
    Schedules the blocking Flask server function to run on a separate thread 
    provided by the Discord bot's event loop executor.
    
    This function is called by client.setup_hook and receives the client object 
    (Arg 1) and the database reference (Arg 2).
    """
    global global_module_database
    global_module_database = db_reference
    
    # Run the blocking Flask server in the event loop's executor
    await client.loop.run_in_executor(None, run_flask_server)
    
    print("Keep-alive server confirmed running via asyncio executor.")
