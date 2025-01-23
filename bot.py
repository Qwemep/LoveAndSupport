import discord
from discord.ext import commands
import os
from cogs.ids import *
from cogs.events import *
import mysql.connector
from db_config import connect_db


# Obtain the Token
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create an instance of a bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Connect to the database
conn = connect_db()
bot.conn = conn

# List of cogs to load
cogs = [
    'cogs.moderation',
    'cogs.setups',
    'cogs.events',
    'cogs.economy',
    'cogs.uno',
    'cogs.farm',
    'cogs.bump',
    'cogs.tasks',
]

reload_cogs = [cog for cog in cogs if cog not in ['cogs.farm', 'cogs.tasks', 'cogs.bump']]

# Event - On Ready
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')
    print('Loading cogs...')
    for cog in cogs: 
        try:
            await bot.load_extension(cog)
            print(f'Loaded {cog}!')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        except Exception as e:
            print(f'Failed to load {cog}: {e}')

@bot.command(name='reload')
async def reload(ctx):
    if ctx.author.id != KYU_ID:
        await ctx.send("You do not have permission to use this command.")
        return

    try:
        for cog in reload_cogs:
            await bot.reload_extension(cog)
    except Exception as e:
        await ctx.send(f'Failed to reload {cog}: {e}')

    await ctx.send(f'Reloaded cogs!')

@bot.command(name='fr')
async def fr(ctx):
    if ctx.author.id != KYU_ID:
        await ctx.send("You do not have permission to use this command.")
        return

    try:
        await bot.reload_extension('cogs.farm')
        await ctx.send(f'Farm Reloaded!')
    except Exception as e:
        await ctx.send(f'Failed to reload farm: {e}')
   

# Run the bot
print("successfully finished startup")

# Confession Command
@bot.tree.command(name="confess", description="Submit an anonymous confession")
async def confess(interaction: discord.Interaction, confession: str):

    if interaction.channel.id != ANONYMOUS_ID:
        await interaction.response.send_message(f"You cannot use that here! Please go to <#{ANONYMOUS_ID}>.")
        return

    await interaction.response.defer()  # Acknowledge the command without showing it


    try:
        cursor = bot.conn.cursor()

        cursor.execute("SELECT confession_value FROM server_data")
        confession_value = cursor.fetchone()[0]
        cursor.execute("UPDATE server_data SET confession_value = confession_value + 1")
        bot.conn.commit()
    finally:
        cursor.close()
    
    

    await interaction.channel.send(
        embed=discord.Embed(
            title=f"Anonymous Confession #" + str(confession_value),
            description=confession,
            color=discord.Color.from_rgb(0, 255, 255)  # Set the color to cyan
        )
    )
    await interaction.channel.send("\u200b")
    await interaction.delete_original_response()

    # Send it to admin log as well
    admin_mod_logs_channel = bot.get_channel(ADMIN_MOD_LOGS)
    if admin_mod_logs_channel:
        await admin_mod_logs_channel.send(
            embed=discord.Embed(
                title=f"Anonymous Confession #" + str(confession_value) + " by " + str(interaction.user.display_name),
                description=confession,
                color=discord.Color.from_rgb(0, 255, 255)  # Set the color to cyan
            )
        )

   



bot.run(TOKEN)