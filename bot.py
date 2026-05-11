import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
GAMEPASS_ID = 174939572

# =========================
# BOT SETUP
# =========================
intents = discord.Intents.default()
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# This clears if the bot restarts. Consider a database for permanent bans/kicks.
redeemed_accounts = set()

# =========================
# ROBLOX FUNCTIONS
# =========================

async def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            data = await response.json()
            if data.get("data"):
                return data["data"][0]["id"]
    return None

async def owns_gamepass(user_id):
    # Note: The user's Roblox inventory MUST be set to Public for this to work.
    url = f"https://inventory.roblox.com/v1/users/{user_id}/items/GamePass/{GAMEPASS_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return len(data.get("data", [])) > 0
    return False

# =========================
# EVENTS
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

# =========================
# /REDEEM
# =========================

@bot.tree.command(name="redeem", description="Check ownership and initiate kick")
@app_commands.describe(username="Your Roblox username")
async def redeem(interaction: discord.Interaction, username: str):
    # We use ephemeral=True so others don't see the user's Roblox name
    await interaction.response.defer(ephemeral=True)

    username_lower = username.lower()

    # 1. CHECK IF ALREADY PROCESSED
    if username_lower in redeemed_accounts:
        await interaction.followup.send("❌ This Roblox account has already been used.", ephemeral=True)
        return

    # 2. GET ROBLOX ID
    user_id = await get_user_id(username)
    if not user_id:
        await interaction.followup.send("❌ Roblox user not found.", ephemeral=True)
        return

    # 3. CHECK OWNERSHIP
    has_pass = await owns_gamepass(user_id)

    if has_pass:
        redeemed_accounts.add(username_lower)
        
        try:
            # Notify the user right before the kick
            await interaction.followup.send("✅ Game Pass verified.", ephemeral=True)
            
            # 4. PERFORM THE KICK
            await interaction.guild.kick(
                interaction.user, 
                reason=f"Verified ownership of Game Pass {GAMEPASS_ID} (Roblox: {username})"
            )
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Error: (Check role hierarchy).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An unexpected error occurred: {e}", ephemeral=True)
    else:
        await interaction.followup.send("❌ You do not own the required Game Pass. (Ensure your inventory is Public!)", ephemeral=True)

# =========================
# /GAMEPASS
# =========================

@bot.tree.command(name="gamepass", description="Show Game Pass info")
async def gamepass(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 Restricted Access Pass",
        description=(
            "To proceed, you must own the Supporter Game Pass.\n\n"
            "**Instructions:**\n"
            "1. Purchase the pass via the button below.\n"
            "2. Set your Roblox Inventory to **Public**.\n"
            "3. Use `/redeem` to verify."
        ),
        color=0xff0000
    )
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Buy Game Pass", url=f"https://www.roblox.com/game-pass/{GAMEPASS_ID}/"))
    
    await interaction.response.send_message(embed=embed, view=view)

bot.run(TOKEN)
