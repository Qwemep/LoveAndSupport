import discord
from discord.ext import commands, tasks
from discord import Embed
from .ids import *
from datetime import datetime, timedelta
from cogs.economy import BIRTHDAY_BEAN_ID, GENERAL_ID, LOTTERY_ID
import pytz
import random

class Tasks(commands.Cog):

    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        if self.conn is None:
            raise Exception("Failed to connect to the database")
        
        self.pst = pytz.timezone('US/Pacific')
        self.last_lottery = None

        self.main_tasks.start()

    @tasks.loop(minutes=15)
    async def main_tasks(self):
        print("---\nRunning Quarterly tasks...")
        try:
            await self.check_birthdays()
        except Exception as e:
            print(f"Error checking birthdays: {e}")
        try:
            await self.lottery_winner()
        except Exception as e:
            print(f"Error checking lottery: {e}")

    # Birthday Taks
    async def check_birthdays(self):
        today = datetime.now(self.pst).date()
        today_str = today.strftime('%m-%d')
        print("Checking Birthdays...")

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, birthday FROM users WHERE birthday IS NOT NULL")
            result = cursor.fetchall()
            birthdays = {user_id: birthdays for user_id, birthdays in result}
        finally:
            cursor.close()

        # Check if any user has a birthday today
        for user_id, birthday_str in birthdays.items():
            member = self.bot.get_guild(GUILD_ID).get_member(user_id)
            if member is None:
                continue
            role = discord.utils.get(member.guild.roles, id=BIRTHDAY_BEAN_ID)
            
            

            # Add the birthday role and give the user 500 coins
            if birthday_str == today_str:
                print(f"It is {member.display_name}'s birthday!")
                if role not in member.roles:
                    await member.add_roles(role)
                    channel = self.bot.get_channel(GENERAL_ID)
                    await channel.send(f'Happy Birthday {member.mention}! 🎉\n You get a birthday gift of **500 coins!**')
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("UPDATE users SET coins = coins + 500 WHERE user_id = %s", (user_id,))
                        self.conn.commit()
                    finally:
                        cursor.close()

            # Remove the birthday role if the user's birthday has passed
            elif role in member.roles:
                await member.remove_roles(role)
                print(f"{member.display_name}'s birthday role has been taken.")
            
    @commands.command(name='force_lottery')
    async def force_lottery(self,ctx):
        if ctx.author.id != KYU_ID:
            await ctx.send("You do not have permission to run this command.")
            return
        await self.lottery_winner(bypass=True)
        return

   
    async def lottery_winner(self, bypass=False):
        current_time = datetime.now(self.pst)
        channel = self.bot.get_channel(GENERAL_ID)

        if (self.last_lottery == current_time.date()) and not bypass:
            print("Lottery already ran today.")
            return
        else:
            self.last_lottery = current_time.date()

        # Lottery Function 
        if current_time.hour == 12 or bypass:
            lottery_number = random.randint(1, 1000)  # Example lottery number between 1 and 1000
            print(f"Lottery number: {lottery_number}")

            guild = self.bot.get_guild(GUILD_ID)
            embed = discord.Embed(
                title=f"Lottery time!",
                description=f"Today's lottery number: {lottery_number}",
                color=0x00FFFF
            )
            await channel.send(embed=embed)

 
            # Check if there are no lottery entries
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT user_id, lottery_guess FROM users WHERE lottery_guess IS NOT NULL")
                result = cursor.fetchall()
                lottery_key = {user_id: lottery_guess for user_id, lottery_guess in result}
            finally:
                cursor.close()

            if not lottery_key:
                await channel.send("No one entered the lottery today! Please type `!lottery <number>` to enter the lottery!")
                return
            
            # Find the minimum difference between the lottery number and the guesses
            difference = {}
            prize = 0

            for k in lottery_key:
                # Calculate the absolute difference in a circular manner
                diff = abs(lottery_key[k] - lottery_number)
                circular_diff = min(diff, 1000 - diff)
                
                difference[k] = circular_diff
                prize += 30

            min_diff = min(difference[k] for k in difference)

            # Find all users with the minimum difference
            closest_guesses = [k for k in lottery_key if difference[k] == min_diff]
            print(f"winners:{closest_guesses}")

            num_winners = len(closest_guesses)
            prize_per_winner = prize // num_winners if num_winners > 0 else 0

            winner_mentions = []
            for guesser in closest_guesses:
                member = guild.get_member(int(guesser))
                if not member:
                    continue

                winner_mentions.append(f"<@{member.id}>")
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("UPDATE users SET coins = coins + %s WHERE user_id = %s", (prize_per_winner, member.id))
                    self.conn.commit()
                finally:
                    cursor.close()

            if not member:
                await channel.send(f"There was an error getting the lottery winners, user left the server.")
            else:
                # Update the embed description to include all winners and their prize
                if num_winners == 1:
                    await channel.send(f"The closest person to win the <@&{LOTTERY_ID}> is <@{member.id}>\nThey have won **{prize} coins**!\n")
                else:
                    await channel.send(f"Multiple <@&{LOTTERY_ID}> Winners! {', '.join(winner_mentions)}\nEach winner gets **{prize_per_winner} coins**!")

                await channel.send(f"Total participants: {len(lottery_key)}")
                
            # Remove lottery role from all participants
            role_to_remove = discord.utils.get(guild.roles, id=LOTTERY_ID)
            for guesser in self.bot.get_guild(GUILD_ID).get_role(LOTTERY_ID).members:
                await guesser.remove_roles(role_to_remove)
            
            # Clear the lottery entries for the next lottery
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE users SET lottery_guess = NULL")
                self.conn.commit()
            finally:
                cursor.close()

            
            
            return
        else:
            print("Not lottery time yet.")
            return

async def setup(bot):
    await bot.add_cog(Tasks(bot, bot.conn))