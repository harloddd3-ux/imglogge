import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

TOKEN = os.getenv("TOKEN")
GAMEPASS_ID = 174939572

used_usernames = set()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


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


async def owns_gamepass(user_id):
    url = f"https://inventory.roblox.com/v1/users/{user_id}/items/GamePass/{GAMEPASS_ID}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

            if data.get("data"):
                return len(data["data"]) > 0

    return False


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.tree.command(name="redeem", description="Check Roblox Game Pass ownership")
@app_commands.describe(username="Your Roblox username")
async def redeem(interaction: discord.Interaction, username: str):

    await interaction.response.defer(ephemeral=True)

    username_lower = username.lower()

    if username_lower in used_usernames:
        await interaction.followup.send(
            "❌ This Roblox username has already been used.",
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

    used_usernames.add(username_lower)

    if has_pass:
        try:
            await interaction.guild.kick(
                interaction.user,
                reason="User owns restricted Roblox Game Pass"
            )

            await interaction.followup.send(
                f"🚫 {interaction.user.mention} was kicked because the Roblox account owns the restricted Game Pass.",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to kick user: {e}",
                ephemeral=True
            )

    else:
        await interaction.followup.send(
            "✅ User does NOT own the Game Pass.",
            ephemeral=True
        )


@bot.tree.command(name="gamepass", description="Show Game Pass information")
async def gamepass(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎮 Elmir's mods Supporter",
        description=(
            "Support the server and unlock exclusive perks by purchasing the Elmir's mods Supporter Game Pass!

"
            "💰 Price: 500 Robux
"
            "🎁 Reward: Exclusive Supporter Discord role
"
            "🔓 Perks: Access to supporter-only channels, special badge & more!

"
            "Click Buy Game Pass below, then use /redeem with your Roblox username.

"
            "After purchasing, use /redeem."
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
