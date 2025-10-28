import statistics
from discord.ext import commands
import time
import discord
from utils.helpers import *
from flask import Flask, g, jsonify
import threading
import swapfest
import math
import os
from flask_cors import CORS
from flask import send_from_directory


# Discord bot and Flask app setup
app = Flask(__name__)
CORS(app)

def get_db():
    """
    Get database connection from Flask application context.
    
    Returns:
        Database connection object (PostgreSQL or SQLite depending on environment).
    """
    if 'db' not in g:
        if db_type == 'postgresql':
            g.db = psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            g.db = sqlite3.connect('local.db', detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error) -> None:
    """
    Close database connection when application context tears down.
    
    Args:
        error: Error object if teardown is due to an exception, None otherwise.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path: str):
    """
    Serve React application files with fallback to index.html for client-side routing.
    
    Args:
        path: Requested file path within the React build directory.
    
    Returns:
        File response from the react-build directory.
    """
    if path != "" and os.path.exists(f"react-build/{path}"):
        return send_from_directory('react-build', path)
    else:
        return send_from_directory('react-build', 'index.html')

@app.route("/api/leaderboard")
def api_leaderboard():
    """
    Get Swapfest leaderboard with points, prizes, and timing multipliers.
    
    Returns:
        JSON response containing prize pool and leaderboard data with entries.
    """
    # Define event period in UTC
    start_time = '2025-09-25 21:00:00'
    end_time = '2025-10-22 00:00:00'

    db = get_db()
    cursor = db.cursor()

    query = prepare_query('''
        SELECT
            from_address,
            SUM(points) AS total_points,
            MAX("timestamp") AS last_scored_at
        FROM gifts
        WHERE "timestamp" BETWEEN ? AND ?
        GROUP BY from_address
        ORDER BY total_points DESC, last_scored_at ASC
    ''')

    cursor.execute(query, (start_time, end_time))
    rows = cursor.fetchall()

    def _to_iso(ts):
        # Works if ts is already a string (SQLite) or a datetime (Postgres)
        try:
            return ts.isoformat(sep=' ')
        except AttributeError:
            return str(ts) if ts is not None else None

    # Map wallets to usernames + attach last_scored_at
    leaderboard_data = [
        {
            "username": map_wallet_to_username(from_address),
            "points": total_points,
            "last_scored_at": _to_iso(last_scored_at),
        }
        for (from_address, total_points, last_scored_at) in rows
    ]

    # 1️⃣ Total prize pool
    prize_pool = sum(float(entry["points"]) for entry in leaderboard_data)

    # 2️⃣ Prize percentage mapping by rank
    prize_percentages = {1: 25, 2: 20, 3: 15, 4: 11, 5: 8, 6: 6, 7: 5, 8: 4, 9: 3, 10: 2}

    # 3️⃣ Add prize info
    for index, entry in enumerate(leaderboard_data, start=1):
        if index in prize_percentages:
            percent = prize_percentages[index]
            pet_count = math.ceil(prize_pool * (percent / 100))
            entry["prize"] = f"{entry["points"]} sweepstake entries + Pet your horse {pet_count} times"
        else:
            entry["prize"] = "-"

    return jsonify({
        "prize_pool": prize_pool,
        "leaderboard": leaderboard_data
    })

def run_flask() -> None:
    """
    Run Flask web server on all interfaces at port 8000.
    """
    app.run(host="0.0.0.0", port=8000)
threading.Thread(target=run_flask).start()

# Detect if running on Heroku by checking if DATABASE_URL is set
DATABASE_URL = os.getenv('DATABASE_URL')  # Heroku PostgreSQL URL

# Define the intents required
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Ensure you can read message content

# Define the bot
bot = commands.Bot(command_prefix='/', intents=intents)

# On Heroku/Azure, use PostgreSQL
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()
db_type = 'postgresql'



@bot.tree.command(
    name="gift_leaderboard",
    description="Show Swapfest leaderboard by total gifted points in event period"
)
async def gift_leaderboard(interaction: discord.Interaction) -> None:
    """
    Discord command to display Swapfest gift leaderboard with time-based multipliers.
    
    Args:
        interaction: Discord interaction object for command invocation.
    """
    # Define the event window in UTC
    start_time = '2025-09-25 21:00:00'
    end_time   = '2025-10-22 00:00:00'


    cursor.execute(prepare_query('''
        SELECT
            from_address,
            SUM(points) AS total_points
        FROM gifts
        WHERE timestamp BETWEEN ? AND ?
        GROUP BY from_address
        ORDER BY total_points DESC
        LIMIT 20
    '''), (start_time, end_time))
    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message(
            "No gift records found in the event period.",
            ephemeral=True
        )
        return

    # Format leaderboard with wallet-to-username mapping
    leaderboard_lines = ["🎁 **Swapfest Gift Leaderboard** 🎁"]
    for i, (from_address, total_points) in enumerate(rows, start=1):
        username = map_wallet_to_username(from_address)
        # If you prefer whole numbers, swap to: int(round(total_points))
        leaderboard_lines.append(f"{i}. `{username}` : **{total_points:.2f} points**")

    message = "\n".join(leaderboard_lines)
    await interaction.response.send_message(message, ephemeral=True)


@bot.tree.command(name="swapfest_latest_block", description="Check the last processed blockchain block scraping swapfest gifts (Admin only)")
@commands.has_permissions(administrator=True)
async def latest_block(interaction: discord.Interaction) -> None:
    """
    Discord command to check the last processed blockchain block (Admin only).
    
    Args:
        interaction: Discord interaction object for command invocation.
    """
    # Check if the user is an admin
    if not is_admin(interaction):
        await interaction.response.send_message(
            "You need admin permissions to run this command.",
            ephemeral=True
        )
        return

    # Call your helper function
    last_block = get_last_processed_block()

    if last_block is None:
        await interaction.response.send_message(
            "⚠️ No processed block found.",
            ephemeral=True
        )
        return

    # Respond with the block number
    await interaction.response.send_message(
        f"🧱 **Last processed block:** {last_block}",
        ephemeral=True
    )

@bot.tree.command(
    name="add_gift_swapfest",
    description="(Admin only) Manually add a swapfest gift to the database"
)
@commands.has_permissions(administrator=True)
async def add_gift(
    interaction: discord.Interaction,
    txn_id: str,
    moment_id: int,
    from_address: str,
    points: int,
    timestamp: str
) -> None:
    """
    Discord command to manually add a Swapfest gift to the database (Admin only).
    
    Args:
        interaction: Discord interaction object for command invocation.
        txn_id: Transaction ID from the blockchain.
        moment_id: Unique identifier of the gifted moment.
        from_address: Flow blockchain address of the gift sender.
        points: Point value of the gifted moment.
        timestamp: Timestamp of the gift transaction.
    """
    # ✅ Check admin (if you have a custom checker)
    if not is_admin(interaction):
        await interaction.response.send_message(
            "You need admin permissions to run this command.",
            ephemeral=True
        )
        return

    try:
        # ✅ Call your helpers.py function
        save_gift(txn_id, moment_id, from_address, points, timestamp)

        # ✅ Respond with success
        await interaction.response.send_message(
            f"✅ Gift added:\n- txn_id: {txn_id}\n- moment_id: {moment_id}\n- from: {from_address}\n- points: {points}\n- timestamp: {timestamp}",
            ephemeral=True
        )

    except Exception as e:
        # ✅ Error handling
        await interaction.response.send_message(
            f"❌ Failed to add gift: {e}",
            ephemeral=True
        )


@bot.tree.command(
    name="latest_gifts_csv",
    description="(Admin only) List the latest gifts in CSV format (optionally filter by username)"
)
@commands.has_permissions(administrator=True)
async def latest_gifts_csv(
    interaction: discord.Interaction,
    from_address: str | None = None
) -> None:
    """
    Discord command to list latest gifts in CSV format with optional address filter (Admin only).
    
    Args:
        interaction: Discord interaction object for command invocation.
        from_address: Optional Flow address to filter gifts by sender.
    """
    # ✅ Check admin
    if not is_admin(interaction):
        await interaction.response.send_message(
            "You need admin permissions to run this command.",
            ephemeral=True
        )
        return

    if from_address:
        query = prepare_query('''
            SELECT txn_id, moment_id, from_address, points, timestamp
            FROM gifts
            WHERE from_address = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        cursor.execute(query, (from_address,))
    else:
        query = prepare_query('''
            SELECT txn_id, moment_id, from_address, points, timestamp
            FROM gifts
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        cursor.execute(query)

    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message(
            "No gifts found in the database.",
            ephemeral=True
        )
        return

    csv_lines = ["txn_id,moment_id,from_address,points,timestamp"]

    for txn_id, moment_id, from_address, points, timestamp in rows:
        display_name = map_wallet_to_username(from_address)
        csv_line = f"{txn_id},{moment_id},{display_name},{points},{timestamp}"
        csv_lines.append(csv_line)

    csv_text = "\n".join(csv_lines)
    message_content = f"```csv\n{csv_text}\n```"

    await interaction.response.send_message(message_content, ephemeral=True)

@bot.tree.command(
    name="swapfest_refresh_points",
    description="(Admin only) Re-scan gifts with 0 points and refresh their scoring"
)
@commands.has_permissions(administrator=True)
async def swapfest_refresh_points(interaction: discord.Interaction) -> None:
    """
    Discord command to re-scan and refresh point values for gifts with 0 points (Admin only).
    
    Args:
        interaction: Discord interaction object for command invocation.
    """
    # Admin check
    if not is_admin(interaction):
        await interaction.response.send_message(
            "You need admin permissions to run this command.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🔄 Refreshing points for gifts with 0 points. This may take a while...", 
        ephemeral=True
    )
    FLOW_ACCOUNT = "0xf853bd09d46e7db6"

    # 1️⃣ Find all gifts with 0 points
    cursor.execute(prepare_query('''
        SELECT txn_id, moment_id, from_address
        FROM gifts
    WHERE COALESCE(points, 0) = 0
    '''))
    rows = cursor.fetchall()

    if not rows:
        await interaction.followup.send(
            "✅ No gifts with 0 points found.",
            ephemeral=True
        )
        return

    updated_count = 0

    # 2️⃣ Process each gift
    for txn_id, moment_id, from_address in rows:
        await interaction.followup.send(
            f"✅ Refreshing points for {moment_id}.",
        ephemeral=True
    )
        new_points = await swapfest.get_moment_points(FLOW_ACCOUNT, int(moment_id))
        if new_points > 0:
            await interaction.followup.send(
                f"✅ Refreshing points for {moment_id}: {new_points}.",
                ephemeral=True
            )
            # Update the points in DB
            cursor.execute(prepare_query('''
                UPDATE gifts
                SET points = ?
                WHERE txn_id = ?
            '''), (new_points, txn_id))
            updated_count += 1
            conn.commit()

    # 3️⃣ Report result
    await interaction.followup.send(
        f"✅ Refreshed points for {updated_count} gifts.",
        ephemeral=True
    )



# Close the database connection when the bot stops
@bot.event
async def on_close() -> None:
    """
    Event handler to close database connection when bot stops.
    """
    conn.close()

# Read the token from secret.txt or environment variable
token = os.getenv('DISCORD_TOKEN')
if not token:
    with open('secret.txt', 'r') as file:
        token = file.read().strip()

# Run the bot
bot.run(token)