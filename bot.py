import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

TOKEN = os.getenv("TOKEN")

GAMEPASS_ID = 174939572

redeemed_accounts = set()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# GET ROBLOX USER ID
async def get_user_id(username):

    url = "https://users.roblox.com/v1/usernames/users"

    payload = {
        "usernames": [username],
        "excludeBannedUsers": False
    }

    async with aiohttp.ClientSession() as session:

        async with session.post(url, json=payload) as response:

            data = await response.json()

            if data.get("data"):

                return data["data"][0]["id"]

    return None


# CHECK GAMEPASS
async def owns_gamepass(user_id):

    url = f"https://inventory.roblox.com/v1/users/{user_id}/items/GamePass/{GAMEPASS_ID}"

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as response:

            data = await response.json()

            if data.get("data"):

                return len(data["data"]) > 0

    return False


# READY
@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    try:

        synced = await bot.tree.sync()

        print(f"Synced {len(synced)} commands")

    except Exception as e:

        print(e)


# REDEEM
@bot.tree.command(
    name="redeem",
    description="Redeem Roblox account"
)
@app_commands.describe(username="Your Roblox username")
async def redeem(interaction: discord.Interaction, username: str):

    await interaction.response.defer(ephemeral=True)

    username_lower = username.lower()

    if username_lower in redeemed_accounts:

        await interaction.followup.send(
            "❌ This Roblox account was already redeemed.",
            ephemeral=True
        )
        return

    user_id = await get_user_id(username)

    if not user_id:

        await interaction.followup.send(
            "❌ Roblox user not found.",
            ephemeral=True
        )
        return

    has_pass = await owns_gamepass(user_id)

    if has_pass:

        redeemed_accounts.add(username_lower)

        try:

            await interaction.guild.kick(
                interaction.user,
                reason="Owns Roblox gamepass"
            )

            await interaction.followup.send(
                "✅ Gamepass found. User kicked.",
                ephemeral=True
            )

        except Exception as e:

            await interaction.followup.send(
                f"❌ Kick failed: {e}",
                ephemeral=True
            )

    else:

        await interaction.followup.send(
            "❌ This Roblox account does NOT own the gamepass.",
            ephemeral=True
        )


# GAMEPASS
@bot.tree.command(
    name="gamepass",
    description="Show gamepass info"
)
async def gamepass(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎮 Elmir's mods Supporter",
        description=(
            "Support the server and unlock exclusive perks.\n\n"
            "💰 Price: 500 Robux\n"
            "🎁 Reward: Exclusive role\n\n"
            "Buy the gamepass then use /redeem."
        ),
        color=0x00ff00
    )

    view = discord.ui.View()

    button = discord.ui.Button(
        label="Buy Game Pass",
        url=f"https://www.roblox.com/game-pass/{GAMEPASS_ID}/"
    )

    view.add_item(button)

    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True
    )


bot.run(TOKEN)
