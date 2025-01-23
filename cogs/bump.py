import discord
import discord
from discord.ui import Button, View
from datetime import timedelta, datetime
from discord.ext import commands
from .ids import *
import asyncio
import os  # Add import for os
import time  # Add import for time

class bump(commands.Cog): # create a class for our cog that inherits from commands.Cog
    
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        self.guild = self.bot.get_guild(GUILD_ID)
        self.star_member = self.get_star_bump_members(self.guild)[0]
        print(f"Current Star member: {self.star_member.display_name}")

        if self.conn is None:
            raise Exception("Failed to connect to the database")
        
        
    # Function to get members with the BUMP_STAR_ID role
    def get_star_bump_members(self, guild):
        bump_star_role = discord.utils.get(guild.roles, id=BUMP_STAR_ID)
        if bump_star_role:
            return [member for member in guild.members if bump_star_role in member.roles]
        return []
        
    # On message - The void - mentions
    @commands.Cog.listener()
    async def on_message(self, message):
        # Bump
        if (message.channel.id == BUMP_CHANNEL_ID and message.author.id == 302050872383242240):
            await message.delete()

            async def bump_timer():
                await asyncio.sleep(60*60*2+5)
                bump_channel = self.bot.get_channel(BUMP_CHANNEL_ID)
                await bump_channel.send(f"<@&{BUMP_ID}> it's bump time!")

            asyncio.create_task(bump_timer())
            try:
                id = message.interaction_metadata.user.id 
            except:
                id = KYU_ID
            member = message.guild.get_member(id)

            try:
                cursor = self.conn.cursor()


                cursor.execute("SELECT bump_amount, star_time FROM users WHERE user_id = %s", (id,))
                result = cursor.fetchone()
                if result:
                    bump_amount = result[0] + 1
                    current_user_star_time = result[1] or 0
                else:
                    bump_amount = 1
                    current_user_star_time = 0
                

                cursor.execute("SELECT bump_time, user_id FROM bump ORDER BY bump_time DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    last_bump_time = result[0]
                    last_bump_userid = result[1]
                else:
                    last_bump_time = int(time.time())
                    last_bump_userid = 0


                cursor.execute("SELECT star_time FROM users WHERE user_id = %s", (last_bump_userid,))
                last_user_star_time = cursor.fetchone()[0] or 0
                last_user_star_time = last_user_star_time + (int(time.time()) - last_bump_time) 

                if last_bump_userid == id:
                    hours_held = round(last_user_star_time / 3600, 1)
                else:
                    hours_held = round(current_user_star_time / 3600, 1)
                

                cursor.execute("INSERT INTO bump (user_id, bump_time) VALUES (%s, %s)", (id, int(time.time())))
                cursor.execute("UPDATE users SET bump_amount = %s WHERE user_id = %s", (bump_amount, id))
                cursor.execute("UPDATE users SET star_time = %s WHERE user_id = %s", (last_user_star_time, last_bump_userid))
                self.conn.commit()
            except Exception as e:
                print(f"Database error: {e}")
            finally:
                cursor.close()

            ticket_stamp = bump_amount % 6 or 6
            coins_earned = int(25 * ticket_stamp)
            
            image_path = os.path.join(IMAGES_PATH, f"LNS bump {ticket_stamp}.png")
            file = discord.File(image_path, filename="image.png")

            description = f"Thank you <@{id}> for bumping the server! You've earned {coins_earned} coins!\n\n"
            
            if self.star_member.id == id:
                description += f"⭐ You yet again reign victorious as you keep the star for yourself.\n\n"
            else:
                description += f"⭐ You've stolen the star from <@{self.star_member.id}>!\n\n"

            description += f"You've bumped the server a total of {bump_amount} times!\n"
            description += f"You've held the star for a total of **{hours_held} Hours!**"
            
            if ticket_stamp == 6:
                role = discord.utils.get(message.guild.roles, id=SWEETHEART_ID)
                
                if role not in member.roles:
                    await member.add_roles(role)
                    description += "\n\nYou've earned the *Absolute Sweetheart* role and a bonus 100 coins for reaching 6 stamps! Thank you! 🎉"
                    coins_earned += 100
                else:
                    description += "\nYou've earned an additional 200 coins for reaching 6 stamps! Thank you! 🎉"
                    coins_earned += 200

            embed = discord.Embed(title="Bump!", description=description, color=0xe5a5a5)
            embed.set_image(url=f"attachment://image.png")

            bump_channel = self.bot.get_channel(BUMP_CHANNEL_ID)
            await bump_channel.send(file=file, embed=embed)
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE users SET coins = coins + %s WHERE user_id = %s", (coins_earned, id))
                self.conn.commit()
            except Exception as e:
                print(f"Database error: {e}")
            finally:
                cursor.close()
            
            # Bump star role exchange
            if id is not self.star_member.id:
                bump_star_role = discord.utils.get(message.guild.roles, id=BUMP_STAR_ID)
                for person in self.get_star_bump_members(message.guild):
                    if bump_star_role in person.roles:
                        await person.remove_roles(bump_star_role)
                await member.add_roles(bump_star_role)
                self.star_member = member
            

async def setup(bot): # this is called by Pycord to setup the cog
    await bot.add_cog(bump(bot, bot.conn)) # add the cog to the bot