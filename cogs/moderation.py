import discord
from discord.ext import commands
from discord.ui import Button, View
from .ids import * 
import mysql.connector
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        if self.conn is None:
            raise Exception("Failed to connect to the database")
        
        self.master = None
        self.participants = []
    
    # skybliss command
    @commands.command(name='skybliss')
    async def skybliss(self, ctx):
        await ctx.send('''
                    A therian is an individual who experiences a profound and intrinsic connection to a particular animal species, perceiving this association as an integral facet 
                 of their identity on a spiritual, psychological, or instinctual level. This phenomenon is not a performative or imaginative exercise but rather a deeply rooted 
                 existential alignment wherein their self-concept encompasses attributes, instincts, or behaviors emblematic of the animal with which they identify.

                This synthesis of human consciousness and animalistic essence manifests in highly individualized ways, reflecting a complex interplay between introspection, subconscious 
                affinities, and the metaphysical nuances of self-perception.
                 ''')
        return

    # Mute Command
    @commands.command(name='mute')
    async def mute(self, ctx, member: discord.Member):
        if not any(role.id in [MOD_ROLE_ID, ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        if member == ctx.author:
            await ctx.send("You cannot mute yourself.")
            return

        loved_role = ctx.guild.get_role(LOVED_ROLE_ID)
        muted_role = ctx.guild.get_role(MUTED_ROLE_ID)
        category = ctx.guild.get_channel(PM_CATEGORY_ID)
        mod_role = ctx.guild.get_role(MOD_ROLE_ID)
        
        mute_overwrite = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
        }

        # Normalize display name
        normalized_name = member.name.replace(" ", "-").lower()
        normalized_name = ''.join(e for e in normalized_name if e.isalnum())
        if not normalized_name:
            normalized_name = str(ctx.author.id)

        if muted_role not in member.roles:
            await member.add_roles(muted_role)
            await member.remove_roles(loved_role)

            await ctx.guild.create_text_channel(f"mute-{normalized_name}", category=category, overwrites=mute_overwrite)

            channel = ctx.guild.get_channel(ADULT_STRUGGLES_ID)
            adult_overwrite = ctx.channel.overwrites_for(member)
            adult_overwrite.view_channel = False
            await channel.set_permissions(member, overwrite=adult_overwrite)

            femChannel = ctx.guild.get_channel(FEMALE_ID)
            fem_overwrite = ctx.femChannel.overwrites_for(member)
            fem_overwrite.view_channel = False
            await femChannel.set_permissions(member, overwrite=fem_overwrite)


            await ctx.send(f"Successfully muted {member.display_name}.")
        else:
            await member.add_roles(loved_role)
            await member.remove_roles(muted_role)

            channel_name = f"mute-{normalized_name}"
            existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
            if existing_channel:
                await existing_channel.delete()

            channel = ctx.guild.get_channel(ADULT_STRUGGLES_ID)
            await channel.set_permissions(member, overwrite=None)

            femChannel = ctx.guild.get_channel(FEMALE_ID)
            await channel.set_permissions(member, overwrite=None)

            if ctx.channel:
                await ctx.send(f"Successfully unmuted {member.display_name}.")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Member not found. Please mention a valid user.")
        else:
            await ctx.send(f"An error occurred: {error}")

    # PM Command
    @commands.command(name='pm')
    async def pm(self, ctx, member: discord.Member):
        if not any(role.id in [MOD_ROLE_ID, ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        if member == ctx.author:
            await ctx.send("You cannot create a chat with yourself.")
            return

        category = ctx.guild.get_channel(PM_CATEGORY_ID)
        mod_role = ctx.guild.get_role(MOD_ROLE_ID)
        
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
        }

        # Normalize display name
        normalized_name = member.name.replace(" ", "-").lower()
        normalized_name = ''.join(e for e in normalized_name if e.isalnum())
        if not normalized_name:
            normalized_name = str(ctx.author.id)


        channel_name = f"pm-{normalized_name}"
        existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        
        if not existing_channel:
            await ctx.guild.create_text_channel(f"pm-{normalized_name}", category=category, overwrites=overwrites)
            await ctx.send(f"Successfully created a private message with {member.display_name}.")
        else:
            await existing_channel.delete()
            await ctx.send(f"Successfully deleted private message with {member.display_name}.")

    @pm.error
    async def pm_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Member not found. Please mention a valid user.")
        else:
            await ctx.send(f"An error occurred: {error}")

    # Slowmode Command
    @commands.command(name='slowmode')
    async def slowmode(self, ctx, duration: str):
        if not any(role.id in [MOD_ROLE_ID, ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return
        
        if duration.lower() == "off":
            await ctx.channel.edit(slowmode_delay=0)  
            await ctx.send("Slowmode is now off.")
            return
        if duration.endswith('s'):
            duration = duration[:-1]
        try:
            seconds = int(duration)
        except ValueError:
            await ctx.send("Please provide a valid number for the slowmode duration.")
            return
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            return
        
        await ctx.send(f"Slowmode set to {seconds} seconds.")

    # Freeze Command
    @commands.command(name='freeze')
    async def freeze(self, ctx):
        if not any(role.id in [MOD_ROLE_ID, ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return
        
        try:
            LOVED_ROLE = ctx.guild.get_role(LOVED_ROLE_ID)
            overwrite = ctx.channel.overwrites_for(LOVED_ROLE)
            # Toggle the "Send Messages" permission
            if overwrite.send_messages is None or overwrite.send_messages:  # If it's enabled or unset
                overwrite.send_messages = False  # Disable it
                await ctx.send("Chat is temporarily frozen.")
            else:  # If it's disabled
                overwrite.send_messages = None  # Reset
                await ctx.send("Chat is now unfrozen.")
            
            await ctx.channel.set_permissions(LOVED_ROLE, overwrite=overwrite)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    # Lockdown Command
    @commands.command(name='lockdown')
    async def lockdown(self, ctx):
        if not any(role.id in [MOD_ROLE_ID, ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        role = ctx.guild.get_role(LOVED_ROLE_ID)
        try:
            permissions = role.permissions
            Kyu = ctx.guild.get_member(KYU_ID)

            if permissions.send_messages:
                permissions.update(send_messages=False)
                await ctx.send("Lockdown initiated: Please wait until an issue resolves.")
                await Kyu.send(f"L&S Alert: Lockdown initiated by {ctx.author.display_name}")
            else:
                permissions.update(send_messages=True)
                await ctx.send("Lockdown ended: Thank you for your patience.")

            await role.edit(permissions=permissions)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    # Clear Command
    @commands.command(name='clear')
    async def clear(self, ctx, amount: int):
        if not any(role.id in [MOD_ROLE_ID, ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return
        
        if amount <= 0:
            await ctx.send("Please specify a number greater than 0.")
            return

        messages = [message async for message in ctx.channel.history(limit=amount + 1)]
        await ctx.channel.delete_messages(messages)

    # PermissionSet Command
    @commands.command(name='PermissionSet')
    async def PermissionSet(self, ctx):
        if not any(role.id in [ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        mod_role = ctx.guild.get_role(MOD_ROLE_ID)
        if not mod_role:
            await ctx.send("Moderator role not found.")
            return

        for channel in ctx.guild.channels:
            overwrite = channel.overwrites_for(mod_role)
            overwrite.send_messages = True
            await channel.set_permissions(mod_role, overwrite=overwrite)

        await ctx.send("Permissions updated: MODERATOR_ID can now send messages in all channels.")

    @commands.command(name="test")
    async def test(self, ctx):
        if ctx.author.id != KYU_ID:
            await ctx.send("You do not have permission to use this command.")
            return


        embed = discord.Embed(
            title="*Daily Check in*",
            description="Welcome to our daily check in!\n\n\n\n*__Users Joined__*",
            color=0x4752c4
        )

        embed.set_footer(text=f"Users joined: {len(self.participants)}")

        view = discord.ui.View()
        btn0 = discord.ui.Button(label="Join", style=discord.ButtonStyle.primary, custom_id="ci_join")
        btn1 = discord.ui.Button(label="Leave", style=discord.ButtonStyle.danger, custom_id="ci_leave")

        view.add_item(btn0)
        view.add_item(btn1)

        btn0.callback = self.button_callback
        btn1.callback = self.button_callback

        self.master = await ctx.send(embed=embed, view=view)


    async def button_callback(self, interaction: discord.Interaction): 
        embed = self.master.embeds[0]
        description = description = self.master.embeds[0].description

        if interaction.data["custom_id"] == "ci_join":
            
            if interaction.user in self.participants:
                await interaction.response.send_message("You have already joined the daily check in!", ephemeral=True)
                return
            else:
                self.participants.append(interaction.user)

            description += f"\n{interaction.user.display_name}"
            embed.description = description
            embed.set_footer(text=f"Users joined: {len(self.participants)}")
            await self.master.edit(embed=embed)
            await interaction.response.defer()

        elif interaction.data["custom_id"] == "ci_leave":
            if interaction.user in self.participants:
                await interaction.response.defer()
                self.participants.remove(interaction.user)
                description = description.replace(f"\n{interaction.user.display_name}", "")
                embed.description = description
                embed.set_footer(text=f"Users joined: {len(self.participants)}")
                await self.master.edit(embed=embed)

            else:
                await interaction.response.send_message("You have not joined the daily check in!", ephemeral=True)
                return
    
    @commands.command(name='circle')
    async def circle_share(self, ctx):
        if ctx.author.id != KYU_ID:
            await ctx.send("You do not have permission to use this command.")
            return
        
        i=0
        description = f"Hey <@{self.participants[i].id}>!\n It's your turn to tell us about your day.\n\n First off,How would you rate your mood from 1-10? (1 being the worst and 10 being the best)"

        embed = discord.Embed(
            title=f"*{self.participants[i].display_name}'s day*",
            description=description,
            color=0x4752c4
        )

        modal = discord.ui.Modal(title="Mood Rating")
        input = discord.ui.TextInput(label= "Pick a number 1-10", placeholder="Enter your mood rating here", min_length=1, max_length=2, custom_id="ci_input", style=discord.TextStyle.short)
        
        modal.add_item(input)
        await ctx.send(embed=embed)
        await ctx.send_modal(modal)

        asyncio.sleep(15)

        answer = str(input)
        if not answer.isdigit() or int(answer) < 1 or int(answer) > 10:
            await ctx.send("Please enter a valid number between 1 and 10.")
            return
        else:
            ctx.send(f"You choose: {answer}")





        


async def setup(bot):
    await bot.add_cog(Moderation(bot, bot.conn))  # Add the cog to the bot
