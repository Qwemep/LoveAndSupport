import discord
from discord.ui import Button, View
from datetime import timedelta, datetime
from discord.ext import commands
from .ids import *
import aiohttp
import asyncio
import random


class events(commands.Cog): # create a class for our cog that inherits from commands.Cog
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        self.galavalor = list(range(1, 21))
        self.guild = self.bot.get_guild(GUILD_ID)

        if self.conn is None:
            raise Exception("Failed to connect to the database")

    # On message - The void - mentions
    @commands.Cog.listener()
    async def on_message(self, message):

        # Cinnabitch
        if message.content.lower() == "cinna" or message.content.lower().endswith("cinna"):
            await message.channel.send("BITCH")
            return
        
        # Furry
        if message.content.lower() == "im a furry":
            image_path = os.path.join(EGGS_PATH, f"furry.png")
            await message.channel.send(file=discord.File(image_path))

        # AJ
        if message.author.id == 144262790608060416 and message.content.lower() == "im so confused":
            image_path = os.path.join(EGGS_PATH, f"AJ.gif")
            await message.channel.send(file=discord.File(image_path))

        # Wolf
        if message.content.lower() == "rule 1":
            image_path = os.path.join(EGGS_PATH, f"rule 1.gif")
            await message.channel.send(file=discord.File(image_path))
              
        # Make bot talk
        if message.author.id == KYU_ID and message.content.startswith('!bot '):
            await message.delete()
            response = message.content[len('!bot '):]
            genchat = self.bot.get_channel(1263290021058842624)
            await genchat.send(response)
      
        # Galavalor
        if message.content.lower() == "galavalor spotted":

            # Rate limit set
            current_time = datetime.now()
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"SELECT galavalor_count FROM server_data")
                result = cursor.fetchone()
                galaCount = result[0] if result else 0
                cursor.execute(f"SELECT galavalor_timestamp from server_data")
                result = cursor.fetchone()
                galavalor_time = result[0] if result else datetime.now()
            finally:
                cursor.close()
            
            timeDiff = (current_time - galavalor_time).total_seconds()

            # Check if the event has been triggered less than 3 times in the past hour
            try:
                cursor = self.conn.cursor()
                if galaCount >= 3 and timeDiff < 3600:
                    await message.channel.send("Galavalor Spotted ✨")
                    return
                elif galaCount >= 3 and timeDiff > 3600:             
                    cursor.execute(f"UPDATE server_data SET galavalor_count = 1, galavalor_timestamp = '{current_time_str}'")
                elif galaCount < 3 and timeDiff > 3600:
                    cursor.execute(f"UPDATE server_data SET galavalor_count = 1, galavalor_timestamp = '{current_time_str}'")
                else:
                    cursor.execute(f"UPDATE server_data SET galavalor_count = {galaCount + 1}")
                self.conn.commit()
            finally:
                cursor.close()

            # Check if all the images have been used
            if len(self.galavalor) == 0:
                self.galavalor = list(range(1, 21))

            random_item = random.choice(self.galavalor)
            self.galavalor.pop(random_item - 1)
 
            if random_item in range(1, 19):
                image_path = os.path.join(EGGS_PATH, f"gala {random_item}.jpg")
            else:
                image_path = os.path.join(EGGS_PATH, f"gala {random_item}.gif")
            
            await message.channel.send(file=discord.File(image_path))

        # Introductions
        if message.channel.id == INTRODUCTIONS_ID:
            role_to_remove = discord.utils.get(message.guild.roles, id=DIVIDER0_ID)
            role_to_add = discord.utils.get(message.guild.roles, id=DIVIDER0_NOPERM_ID)
            
            if role_to_remove in message.author.roles:
                await message.author.remove_roles(role_to_remove)
            
            if role_to_add:
                await message.author.add_roles(role_to_add)

        # The Void
        if message.channel.id == THE_VOID_ID:
            await message.delete()
            if len(message.mentions) > 0:
                await message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(hours=0.5))    
                # Send a notification message in mod chat
                notification_channel = self.bot.get_channel(MOD_CHAT_ID)
                warning_message = f"{message.author.display_name} was muted for pinging people in the void."
                await notification_channel.send(warning_message)  
                await message.author.send("Please do not ping people in the void.") 
            return
        
        # Uno games
        if message.channel.id == UNO_ONE_ID or message.channel.id == UNO_TWO_ID:
            await asyncio.sleep(15)
            await message.delete()
            return

        # Mass mentions
        if len(message.mentions) > 15:
            # Delete the message
            await message.delete()
            await message.channel.send("You may only ping up to 15 people at a time!")   
            # Time out the user for 30 minutes
            await message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(hours=0.5))
            # Send a notification message in mod chat
            notification_channel = self.bot.get_channel(MOD_CHAT_ID)
            warning_message = f"{message.author.display_name} was muted for mass pinging for 30 minutes."
            await notification_channel.send(warning_message)

    # On Reaction - Starboard
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        
        # Check if the reaction is :starboard: and the count is 5 or more
        if reaction.emoji.name == "⭐":
            # Get the message
            message = await self.bot.get_channel(reaction.channel_id).fetch_message(reaction.message_id)
            reactions = message.reactions
            for reaction in reactions:
                if reaction.emoji == "⭐" and reaction.count >= 5:
                    print("--Message got starboarded!--")
                    # Get the starboard channel
                    starboard_channel = self.bot.get_channel(STARBOARD_ID)

                    # Avoid reposting the same message by checking for a previous post
                    async for message in starboard_channel.history(limit=50):
                        if str(reaction.message.id) in str(message.embeds[0].footer.text):
                            return  # Message already posted to starboard
                        
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute(f"SELECT starboard_count FROM users WHERE user_id = {reaction.message.author.id}")
                        result = cursor.fetchone()
                        starboard_count = result[0] if result else 0
                        
                        cursor.execute(f"UPDATE users SET starboard_count = {starboard_count + 1} WHERE user_id = {reaction.message.author.id}")
                        self.conn.commit()
                    finally:
                        cursor.close()

                    # Create the embed to post to the starboard channel
                    embed = discord.Embed(description=reaction.message.content, color=discord.Color.gold())
                    embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)
                    embed.add_field(name="Jump to Message", value=f"[Click here]({reaction.message.jump_url})")
                    embed.set_footer(text=f"ID: {reaction.message.id}   Total Stars: {starboard_count + 1}")

                    # If the message has an attachment, add it to the embed
                    if reaction.message.attachments:
                        embed.set_image(url=reaction.message.attachments[0].url)

                    # Send the embed to the starboard channel
                    await starboard_channel.send(embed=embed)

    #On message edit - edit logs
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Ensure that the message was actually edited (and not just auto-corrected by Discord)
        if before.content == after.content:
            return

        if before.channel.id == THE_VOID_ID or before.channel.id == ANONYMOUS_ID or before.channel.id == COMMANDS_ID:
            return 
        
        if before.channel.category_id == ADMIN_CATEGORY_ID:
            return


        log_channel = self.bot.get_channel(CHAT_LOG_ID)

        embed = discord.Embed(title="Message Edited", color=discord.Color.orange())
        embed.add_field(name="User", value=before.author.display_name, inline=False)
        embed.add_field(name="Before", value=before.content or "No content", inline=False)
        embed.add_field(name="After", value=after.content or "No content", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.set_footer(text=f"Message ID: {before.id} | User ID: {before.author.id}")
        embed.timestamp = discord.utils.utcnow()

        await log_channel.send(embed=embed)

    # On message delete - delete logs
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        log_channel = self.bot.get_channel(CHAT_LOG_ID)

        forbidden_channel_ids = [THE_VOID_ID, ANONYMOUS_ID, COMMANDS_ID, UNO_ONE_ID, UNO_TWO_ID]

        if message.author.bot:
            return
    
        if message.channel.id in forbidden_channel_ids:
            return 
        
        if message.channel.category_id == ADMIN_CATEGORY_ID:
            return

        embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
        embed.add_field(name="User", value=message.author.display_name, inline=False)
        embed.add_field(name="Content", value=message.content or "No content", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.set_footer(text=f"Message ID: {message.id} | User ID: {message.author.id}")
        embed.timestamp = discord.utils.utcnow()

        await log_channel.send(embed=embed)

    # Event - on member update
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Handle role assignment for achievements
        new_roles = [role.id for role in after.roles if role.id not in [role.id for role in before.roles]]
        for role_id in new_roles:
            if role_id in ROLE_IMAGES:
                role = discord.utils.get(after.guild.roles, id=role_id)
                if role:
                    water_role = discord.utils.get(after.guild.roles, id=WATER_ID)
                    await after.remove_roles(water_role)
                    
                    message = f"{after.mention}, you just unlocked a new rank! You are now: **{role.name}!** 🥳✨"
                    embed = discord.Embed(description=message, color=discord.Color.green())

                    image_path = os.path.join(ACHIEVEMENT_PATH, ROLE_IMAGES[role_id])
                    try:
                        channel = self.bot.get_channel(GENERAL_ID)
                        if channel:
                            await channel.send(embed=embed, file=discord.File(image_path))
                    except Exception as e:
                        print(f"Failed to send message: {e}")

        # Kick from server - Unloved role
        if UNLOVED_ROLE_ID in [role.id for role in after.roles]:
            try:
                dm_message = (
                    "You have been kicked from *Love & Support Mental Health* for not agreeing to the rules. "
                    "If you wish to join our community, please consider agreeing to our rules."
                )
                await after.send(dm_message)
                await after.kick(reason="Kicked for not agreeing to the rules")
                Kyu = after.guild.get_member(KYU_ID)
                await Kyu.send(f"{after.display_name} is unloved")
                print(after.display_name)
            except discord.HTTPException as e:
                print(f"Failed to kick member: {e}")
        
    # Updates member count channel name
    async def update_membercount(self, guild):
        # Find the voice channel by its ID
        channel = discord.utils.get(guild.voice_channels, id=COUNT_ID)
        if channel:
            # Update the channel name with the current member count
            new_name = f"Total members: {guild.member_count}"
            await channel.edit(name=new_name)

    # Event - on member join
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Assigns roles
        water_role = discord.utils.get(member.guild.roles, id=WATER_ID)
        divider0_role = discord.utils.get(member.guild.roles, id=DIVIDER0_ID)
        divider1_role = discord.utils.get(member.guild.roles, id=DIVIDER1_ID)
        await member.add_roles(water_role)
        await member.add_roles(divider0_role)
        await member.add_roles(divider1_role)
        await self.update_membercount(member.guild)

        # Send welcome message
        welcome_channel = self.bot.get_channel(WELCOME_ID)
        await welcome_channel.send(f"Welcome {member.display_name} to the server!")

        # Adds user to the database on member join
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (member.id,))
            result = cursor.fetchone()
            if not result:
                cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (member.id,))
                self.conn.commit()
        finally:
            cursor.close()

    # Event - on member remove
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.update_membercount(member.guild)
        welcome_channel = self.bot.get_channel(WELCOME_ID)
        if welcome_channel:
            await welcome_channel.send(f"{member.display_name} has left the server.")

    # Event - On Interaction
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):     # Event - On Interaction

        if interaction.data['custom_id'].startswith("uno"):
                return
        if interaction.data['custom_id'].startswith("ci"):
                return

        # Button interactions
        if interaction.type == discord.InteractionType.component:
            economy_cog = self.bot.get_cog('economy')

            if interaction.data['custom_id'] == "coinflip_heads":
                await economy_cog.coinflip_logic(interaction, "Heads")
                return
            elif interaction.data['custom_id'] == "coinflip_tails":
                await economy_cog.coinflip_logic(interaction, "Tails")
                return
            elif interaction.data['custom_id'] == "coinflip_cashin":
                await economy_cog.coinflip_logic(interaction, "coinflip_cashin")
                return
            elif interaction.data['custom_id'] == "coinflip_deny":
                await interaction.response.send_message("Ok Bye!", ephemeral = True)
                return
                  
            
            # Rules Agree
            if interaction.data['custom_id'] == "agree":
                role = discord.utils.get(interaction.guild.roles, id=LOVED_ROLE_ID)
                await interaction.user.add_roles(role)
                await interaction.response.send_message("Welcome to our server!", ephemeral=True)
                return
            if interaction.data['custom_id'] == "disagree":
                role = discord.utils.get(interaction.guild.roles, id=UNLOVED_ROLE_ID)
                await interaction.user.add_roles(role)
                await interaction.response.send_message("You've denied the rules", ephemeral=True)
                return
            
            # Early
            if interaction.data['custom_id'] == "early":
                role = discord.utils.get(interaction.guild.roles, id=EARLY_ID)
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message("Received role!", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message("Removed role!", ephemeral=True)     
                return

            # Clock in
            if interaction.data['custom_id'] == "clockin":
                role = discord.utils.get(interaction.guild.roles, id=STAFFPING_ROLE_ID)
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message("clocked in!", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message("clocked out!", ephemeral=True)     
                return

            #Ticketing
            if interaction.data['custom_id'] == "report" or interaction.data['custom_id'] == "question":
                category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
                mod_role = interaction.guild.get_role(MOD_ROLE_ID)
                
                overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
                }
                # Normalize display name
                normalized_name = interaction.user.name.replace(" ", "-").lower()
                normalized_name = ''.join(e for e in normalized_name if e.isalnum())
                if not normalized_name:
                    normalized_name = str(interaction.user.id)

                channel_name = f"ticket-{normalized_name}"
                existing_channel = discord.utils.get(interaction.user.guild.channels, name=channel_name)
                if not existing_channel:
                    await interaction.guild.create_text_channel(f"ticket-{normalized_name}", category=category, overwrites=overwrites)
                    await interaction.response.send_message(f"Succesfully created a ticket!", ephemeral=True)
                    existing_channel = discord.utils.get(interaction.user.guild.channels, name=channel_name)
                    close_button = Button(label="Close Ticket", emoji="🗑️", style=discord.ButtonStyle.primary, custom_id="close")
                    view = View()
                    view.add_item(close_button)
                    await existing_channel.send(f"Please let us know your issue while a member of staff becomes available - <@&{STAFFPING_ROLE_ID}> ", view=view)
                else :
                    await interaction.response.send_message(f"You already have a ticket open!", ephemeral=True)
                return
            if interaction.data['custom_id'] == "staff":
                category = interaction.guild.get_channel(ADMIN_CATEGORY_ID)
                mod_role = interaction.guild.get_role(MOD_ROLE_ID)
                admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)

                overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                mod_role: discord.PermissionOverwrite(view_channel=False, send_messages=True),
                admin_role:discord.PermissionOverwrite(view_channel=True, send_messages=True),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
                }

                normalized_name = interaction.user.name.replace(" ", "-").lower()
                channel_name = f"ticket-{normalized_name}"
                existing_channel = discord.utils.get(interaction.user.guild.channels, name=channel_name)
                if not existing_channel:
                    await interaction.guild.create_text_channel(f"ticket-{normalized_name}", category=category, overwrites=overwrites)
                    await interaction.response.send_message(f"Succesfully created a ticket!", ephemeral=True)
                    existing_channel = discord.utils.get(interaction.user.guild.channels, name=channel_name)
                    close_button = Button(label="Close Ticket", emoji="🗑️", style=discord.ButtonStyle.primary, custom_id="close")
                    view = View()
                    view.add_item(close_button)
                    await existing_channel.send(f"Please let us know your issue while an administrator becomes available - <@&{ADMIN_ROLE_ID}> ", view=view)
                else :
                    await interaction.response.send_message(f"You already have a ticket open!", ephemeral=True)
                return
            
            # Close Ticket
            if interaction.data['custom_id'] == "close":
                ATTACHMENTS_DIR = "attachments"
                # Ensure the attachments directory exists
                if not os.path.exists(ATTACHMENTS_DIR):
                    os.makedirs(ATTACHMENTS_DIR)
                # Respond to the interaction first
                await interaction.response.send_message("Deleting the ticket and logging its history...", ephemeral=True)

                # Fetch the last 100 messages from the channel (adjust the limit as needed)
                messages = [message async for message in interaction.channel.history(limit=100)]

                # Create a session to download files
                async with aiohttp.ClientSession() as session:
                    index = 0
                    embed0 = False
                    embed1 = False
                    embed2 = False
                    embed3 = False

                    for message in reversed(messages):  # Reversed to show messages in chronological order
                        content = message.content or "[No Content]"
                        
                        # Download and save attachments
                        attachment_files = []
                        for attachment in message.attachments:
                            file_path = os.path.join(ATTACHMENTS_DIR, attachment.filename)
                            async with session.get(attachment.url) as response:
                                if response.status == 200:
                                    with open(file_path, 'wb') as f:
                                        f.write(await response.read())
                                    attachment_files.append(discord.File(fp=file_path, filename=attachment.filename))
                        
                        # Upload files to Discord and get URLs
                        attachment_urls = []
                        if attachment_files:
                            for file in attachment_files:
                                upload_msg = await self.bot.get_channel(TRANSCRIPTS_ID).send(file=file)
                                attachment_urls.extend([a.url for a in upload_msg.attachments])

                        # Format content with attachment URLs
                        combined_content = content + "\n" + "\n".join(attachment_urls) if attachment_urls else content

                        # Add to the embed (discord embeds have a character limit, so be mindful of large content)
                        if not embed0 and index <24:
                            embed0 = discord.Embed(title=f"Ticket Transcript: {interaction.channel.name}", color=discord.Color.blue())
                        if not embed1 and index > 24 and index < 49:
                            embed1 = discord.Embed(title=f"Ticket Transcript: {interaction.channel.name}", color=discord.Color.blue())
                        if not embed2 and index > 49 and index < 74:
                            embed2 = discord.Embed(title=f"Ticket Transcript: {interaction.channel.name}", color=discord.Color.blue())
                        if not embed3 and index > 74 and index < 99:
                            embed3 = discord.Embed(title=f"Ticket Transcript: {interaction.channel.name}", color=discord.Color.blue())
    
                        if combined_content:
                            if index <24:
                              embed0.add_field(name=f"{message.author.display_name}:", value=combined_content, inline=False)    
                            elif index > 24 and index < 49:   
                                embed1.add_field(name=f"{message.author.display_name}:", value=content, inline=False)
                            elif index > 49 and index < 74:  
                                 embed2.add_field(name=f"{message.author.display_name}:", value=content, inline=False)
                            elif index > 74 and index < 99:          
                                 embed3.add_field(name=f"{message.author.display_name}:", value=content, inline=False)
                        # Add to the transcript text
                            index += 1

                # Send the embed to the transcript channel
                transcripts_channel = self.bot.get_channel(TRANSCRIPTS_ID)
                await transcripts_channel.send(embed=embed0)
                if embed1:
                    await transcripts_channel.send(embed=embed1)
                if embed2:
                    await transcripts_channel.send(embed=embed2)
                if embed3:
                    await transcripts_channel.send(embed=embed3)

                # Finally, delete the original channel
                await interaction.channel.delete()
                return
            
            # Roles
            role_id = int(interaction.data['custom_id'])
            role = discord.utils.get(interaction.guild.roles, id=role_id)
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(f"The {role.name} role has been removed.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"You have been given the {role.name} role", ephemeral=True)


async def setup(bot): # this is called by Pycord to setup the cog
    await bot.add_cog(events(bot, bot.conn)) # add the cog to the bot