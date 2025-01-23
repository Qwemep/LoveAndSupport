import discord
from discord import Member
from discord.ext import commands
import os
import json
import sys
import random
from datetime import datetime, timedelta
from .ids import *
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import script_dir 

# Card definitions
suits = ['♥', '♦', '♣', '♠']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
          'J': 10, 'Q': 10, 'K': 10, 'A': 11}

# Deck functions
def create_deck():
    return [{'rank': rank, 'suit': suit} for suit in suits for rank in ranks]

def card_value(card):
    return values[card['rank']]

def hand_value(hand):
    value = sum(card_value(card) for card in hand)
    num_aces = sum(1 for card in hand if card['rank'] == 'A')
    while value > 21 and num_aces:
        value -= 10
        num_aces -= 1
    return value

def card_to_str(card):
    return f"{card['rank']}{card['suit']}"

remaining_time_str = False
game_in_progress = {}
coinflip_message = {}
coinflip_amount = {}
    

class economy(commands.Cog): # create a class for our cog that inherits from commands.Cog

    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        if self.conn is None:
            raise Exception("Failed to connect to the database")
        
    def add_coins(self, amount: int, target: Member):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET coins = coins + %s WHERE user_id = %s", (amount, target.id))
            self.conn.commit()
        finally:
            cursor.close()
        
    def remove_coins(self, amount :int, target: Member):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT coins FROM users WHERE user_id = %s", (target.id,))
            coins = cursor.fetchone()[0]

            if coins < amount:
                cursor.execute("UPDATE users SET coins = 0 WHERE user_id = %s", (target.id,))
            else:
                cursor.execute("UPDATE users SET coins = coins - %s WHERE user_id = %s", (amount, target.id))

            self.conn.commit()
        finally:
            cursor.close()

    def set_coins(self, amount: int, target: Member):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET coins = %s WHERE user_id = %s", (amount, target.id))
            self.conn.commit()
        finally:
            cursor.close()

    def rate_limit_set(self,ctx,game):
        user_id = ctx.author.id

        # Data [amount, timestamp(epoch)]
        data = {
            "dice": [0, False],
            "rps": [0, False],
            "daily": [0, False],
            "bypass": [0, False],
            "blackjack": [0, False],
            "guess": [0, False],
            "hangman": [0, False],
            "coinflip": [0, False]
        }

         # List of games in order [hours, frequency]
        game_cooldowns = {
            "dice": [1,3],
            "rps": [1,3],
            "daily": [24, 1],
            "bypass": [1, 1],
            "blackjack": [1,3],
            "guess": [1,3],
            "hangman": [1,3],
            "coinflip": [0.75, 2]
        }

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT rate_limits FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if not result or result[0] == None:
                cursor.execute("UPDATE users SET rate_limits = %s WHERE user_id = %s", (json.dumps(data), user_id))
                self.conn.commit()
                return True
            else:
                data = json.loads(result[0])
        finally:
            cursor.close()

        logged_amount, logged_timestamp = data[game]
        max_time, max_amount = game_cooldowns[game]
        now = datetime.now().timestamp()
     
        def save_ratelimits(data):
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("UPDATE users SET rate_limits = %s WHERE user_id = %s", (json.dumps(data), user_id))
                    self.conn.commit()
                finally:
                    cursor.close()

        
        def calculate_remaining_time():
            global remaining_time_str
            remaining_time_str = str(timedelta(seconds=(logged_timestamp + (max_time * 3600)) - now))
            remaining_time_str = remaining_time_str.split('.')[0]  # Remove microseconds
            hours, remainder = divmod((logged_timestamp + (max_time * 3600)) - now, 3600)
            minutes, seconds = divmod(remainder, 60)
            remaining_time_str = f"**{int(hours)} hours {int(minutes)} minutes**"

        if logged_timestamp == False:
            data[game][0] = 1
            data[game][1] = now
            save_ratelimits(data)
            return True
        elif logged_timestamp + (max_time * 3600) > now:
            if logged_amount < max_amount:
                data[game][0] += 1
                save_ratelimits(data)
                return True
            else:
                calculate_remaining_time()
                return False
        else:
            data[game][0] = 1
            data[game][1] = now
            save_ratelimits(data)
            return True

    def command_channel_check(self, ctx):
        if ctx.message.channel.id != COMMANDS_ID and ctx.message.channel.id != BUMP_CHANNEL_ID:
            return False
        return True

    # Coinset Command
    @commands.command(name="coinset")
    async def coinset(self, ctx, option: str, amount: int, target: Member):
        if not any(role.id in [ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        def get_coins(target):
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT coins FROM users WHERE user_id = %s", (target.id,))
                return cursor.fetchone()[0]
            finally:
                cursor.close()

        coins = get_coins(target)

        # Process the command based on the option
        if option == "add":
            await ctx.send(f"{target.display_name}'s coins were {coins}") 
            self.add_coins(amount, target)
        elif option == "remove":
            await ctx.send(f"{target.display_name}'s coins were {coins}") 
            self.remove_coins(amount, target)
        elif option == "set":
            self.set_coins(amount, target)
        await ctx.send(f"{target.display_name}'s coins are now {coins + amount}")

    # Coins Command
    @commands.command(name="coins")
    async def coins(self, ctx, target: Member = None):
        global coins

        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return
    
        if target is None:
            user = ctx.author
        else:
            user = target
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT coins FROM users WHERE user_id = %s", (user.id,))
            coins = cursor.fetchone()[0]
        finally:
            await ctx.send(f"You have **{coins} coins!**")
        return
   

    # Daily command
    @commands.command(name="daily")
    async def daily(self, ctx):
        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return
        
        rate_limit_check = self.rate_limit_set(ctx, "daily")
        if not rate_limit_check:
            await ctx.send(f"You've used that command too frequently! Please try again in {remaining_time_str}")
            return
        daily_amount = random.randint(50,150)
        self.add_coins(daily_amount, ctx.author)
        await ctx.send(f"You earned **{daily_amount}** coins today!")
    

    # Richest Command
    @commands.command(name="richest")
    async def richest(self, ctx):

        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use  <#{COMMANDS_ID}>to use commands!")
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, coins FROM users WHERE coins > 0")
            coins = dict(cursor.fetchall())
        finally:
            cursor.close()

        # Calculate the total coin count for the server
        total_coin_count = sum(coins.values())
        
        # Sort users by their total coins in descending order
        sorted_users = sorted(coins.items(), key=lambda item: item[1], reverse=True)
        
        # Prepare the leaderboard embed
        embed = discord.Embed(
            title="🏆 **Top 10 Richest Users**",
            description=f"🏛 Total Coins in Server: **{total_coin_count}**",
            color=0x00FFFF
        )
        # Add top 10 users to the embed
        for i, (user_id, coins) in enumerate(sorted_users[:10], start=1):
            user = ctx.guild.get_member(int(user_id))
            username = user.display_name if user else "Unknown User"
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
            embed.add_field(name=f"{rank_emoji} {i}. {username}", value=f"{coins} Coins", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="startime")
    async def startime(self, ctx):
        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, star_time FROM users WHERE star_time IS NOT NULL")
            result = cursor.fetchall()
            star_time = {user_id: star_time for user_id, star_time in result}
        finally:
            cursor.close()

        # leaderboard
        sorted_users = sorted(star_time.items(), key=lambda item: item[1], reverse=True)

        #Prepare the leaderboard embed
        embed = discord.Embed(
            title="🏆 **Star time Leaderboard**",
            color=0x00FFFF
        )

        # Add top 10 users to the embed
        for i, (user_id, star_time) in enumerate(sorted_users[:10], start=1):
            user = ctx.guild.get_member(int(user_id))
            username = user.display_name if user else user.name
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
            embed.add_field(name=f"{rank_emoji} {i}. {username}", value=f"{round(star_time / 3600, 1)} Hours", inline=False)
        await ctx.send(embed=embed)

    # Starboard Command
    @commands.command(name="starboard")
    async def starboard(self, ctx):

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, starboard_count FROM users WHERE starboard_count > 0")
            starboard = cursor.fetchall()
        finally:
            cursor.close()
        sorted_users = sorted(starboard, key=lambda item: item[1], reverse=True)
        
        # Prepare the leaderboard embed
        embed = discord.Embed(
            title="🏆 **Top 10 Starboard Users**",
            description="Users with the most messages in the starboard",
            color=0x00FFFF
        )
        # Add top 10 users to the embed
        for i, (user_id, message_count) in enumerate(sorted_users[:10], start=1):
            user = ctx.guild.get_member(int(user_id))
            username = user.display_name if user else "Unknown User"
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
            embed.add_field(name=f"{rank_emoji} {i}. {username}", value=f"{message_count} Messages", inline=False)
        await ctx.send(embed=embed)

    # Dice Command
    @commands.command(name="dice")
    async def dice(self, ctx, bet: int):
        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return
        
        user_id = ctx.author.id

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT coins FROM users WHERE user_id = %s", (user_id,))
            coins = cursor.fetchone()[0]
        finally:
            cursor.close()

        if bet > 100:
            await ctx.send("Please bet up to a maximum of **100 Coins**!")
            return
        if bet > coins:
            await ctx.send("You do not have that many coins!")
            return

        rate_limit_check = self.rate_limit_set(ctx, "dice")
        if not rate_limit_check:
            await ctx.send(f"You've used that command too frequently! Please try again in {remaining_time_str}")
            return

        you0 = random.randint(1, 6)
        you1 = random.randint(1,6)
        bot0 = random.randint(1, 6)
        bot1 = random.randint(1,6)
        if you0 + you1 > bot0 + bot1:
            await ctx.send(f"You rolled a **{you0}**🎲 and a **{you1}**🎲\n" 
                    f"The bot rolled a **{bot0}**🎲 and a **{bot1}**🎲\n\n"
                    f"You win {bet} Coins!")
            self.add_coins(bet, ctx.author)
        elif you0 + you1 < bot0 + bot1:
            await ctx.send(f"You rolled a **{you0}**🎲 and a **{you1}**🎲\n" 
                    f"The bot rolled a **{bot0}**🎲 and a **{bot1}**🎲\n\n"
                    f"You lost {bet} Coins!")
            self.remove_coins(bet, ctx.author)
        else:
            await ctx.send(f"You rolled a **{you0}**🎲 and a **{you1}**🎲\n" 
                    f"The bot rolled a **{bot0}**🎲 and a **{bot1}**🎲\n\n"
                    "It was a draw!")
    @dice.error
    async def dice_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please bet up to **100** coins!\n"
                        '"!dice 50" bets 50 coins!')
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please bet a whole number up to 100")
        else:
            await ctx.send("An unexpected error occurred.")
            # Optionally log the error
            print(f"Error in 'dice' command: {error}")

    # RPS Command
    @commands.command(name="rps")
    async def rps(self, ctx, choose):
        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return
        
        rate_limit_check = self.rate_limit_set(ctx, "rps")
        if not rate_limit_check:
            await ctx.send(f"You've used that command too frequently! Please try again in {remaining_time_str}")
            return

        # Normalize user input
        choose = choose.lower()
        outcomes = ["rock", "paper", "scissors"]
        
        if choose not in outcomes:
            await ctx.send("Please choose rock, paper, or scissors!")
            return
        
        bot_choice = random.choice(outcomes)
        
        if choose == bot_choice:
            await ctx.send(f"You chose **{choose.capitalize()}!**\n"
                        f"The bot also chose **{bot_choice.capitalize()}!**\n\n"
                        "It was a draw!")
        elif (choose == "rock" and bot_choice == "scissors") or \
            (choose == "paper" and bot_choice == "rock") or \
            (choose == "scissors" and bot_choice == "paper"):
            await ctx.send(f"You chose **{choose.capitalize()}!**\n"
                        f"The bot chose **{bot_choice.capitalize()}!**\n\n"
                        "You win **50** Coins!")
            self.add_coins(50, ctx.author)
        else:
            await ctx.send(f"You chose **{choose.capitalize()}!**\n"
                        f"The bot chose **{bot_choice.capitalize()}!**\n\n"
                        "You lost **50** Coins!")
            self.remove_coins(50, ctx.author)
    @rps.error
    async def rps_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please choose rock, paper, or scissors!")
        elif isinstance(error, ValueError):
            await ctx.send("Please choose rock, paper, or scissors!")
        else:
            await ctx.send(f"An unexpected error occurred: {error}")


    # Blackjack Commands
    @commands.command(name='blackjack')
    async def blackjack(self, ctx, bet: int):
        global game_in_progress
        user_id = ctx.author.id

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT coins FROM users WHERE user_id = %s", (user_id,))
            coins = cursor.fetchone()[0]
        finally:
            cursor.close()
        
        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return
        
        if user_id in game_in_progress:
            await ctx.send("You're already playing a game! Finish it before starting a new one.")
            return

        if bet > 300:
            await ctx.send("Please bet up to a maximum of **300 Coins**!")
            return
        if bet > coins:
            await ctx.send("You do not have that many coins!")
            return

        rate_limit_check = self.rate_limit_set(ctx, "blackjack")
        if not rate_limit_check:
            await ctx.send(f"You've used that command too frequently! Please try again in {remaining_time_str}")
            return

        game_in_progress[user_id] = True

        deck = create_deck()
        random.shuffle(deck)

        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        def hand_to_str(hand):
            return ' '.join(f"[{card_to_str(card)}]" for card in hand)

        player_turn = True

 # Create embed for player and dealer's hands
        embed = discord.Embed(title="Blackjack", color=0x00FFFF)
        embed.add_field(name="Dealer's hand", value=f"{card_to_str(dealer_hand[0])} [Hidden card]", inline=False)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Your hand", value=f"{hand_to_str(player_hand)}\nValue: {hand_value(player_hand)}", inline=False)

        message = await ctx.send(embed=embed)

        while player_turn:
            if hand_value(player_hand) == 21:
                await ctx.send(f"**Blackjack!** You win **{bet} coins** with {hand_to_str(player_hand)}!")
                self.add_coins(bet, ctx.author)
                del game_in_progress[user_id]
                return
            if hand_value(player_hand) > 21:
                await ctx.send(f"**Bust!** You lose **{bet} coins** with {hand_to_str(player_hand)}.")
                self.remove_coins(bet, ctx.author)
                del game_in_progress[user_id]
                return

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ['hit', 'stand']

            await ctx.send("Do you want to hit or stand?")
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60.0)
            except TimeoutError:
                await ctx.send("You took too long to respond. You lose!")
                del game_in_progress[user_id]
                return

            if response.content.lower() == 'hit':
                player_hand.append(deck.pop())
                embed.set_field_at(2, name="Your hand", value=f"{hand_to_str(player_hand)}\n**Value: {hand_value(player_hand)}**", inline=False)
                await message.edit(embed=embed)
            elif response.content.lower() == 'stand':
                player_turn = False
        
        # Reveal dealer's hand and update the embed
        await message.delete()
        embed.set_field_at(0, name="Dealer's hand", value=f"{hand_to_str(dealer_hand)}\n**Value: {hand_value(dealer_hand)}**", inline=False)
        message = await ctx.send(embed=embed)

        while hand_value(dealer_hand) < 17 and hand_value(dealer_hand) < hand_value(player_hand) :
            dealer_hand.append(deck.pop())
            embed.set_field_at(0, name="Dealer's hand", value=f"{hand_to_str(dealer_hand)}\n**Value: {hand_value(dealer_hand)}**", inline=False)
            await message.edit(embed=embed)

        
        if hand_value(dealer_hand) > 21:
            await ctx.send(f"**Dealer busts!** You win **{bet} coins** with {hand_to_str(player_hand)}.")
            self.add_coins(bet, ctx.author)
        elif hand_value(dealer_hand) > hand_value(player_hand):
            await ctx.send(f"**Dealer wins** with {hand_to_str(dealer_hand)}\nYou lose **{bet} coins**.")
            self.remove_coins(bet, ctx.author)
        elif hand_value(dealer_hand) < hand_value(player_hand):
            await ctx.send(f"You win **{bet} coins** with {hand_to_str(player_hand)}!")
            self.add_coins(bet, ctx.author)
        else:
            await ctx.send(f"**It's a tie!** Both you and the dealer have {hand_value(player_hand)}.")
        del game_in_progress[user_id]
        player_turn = False
        return

    @blackjack.error
    async def blackjack_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please bet up to **300** coins!\n"
                        '"!blackjack 50" bets 50 coins!')
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please bet a whole number up to 300")
        else:
            await ctx.send("An unexpected error occurred.")
            # Optionally log the error
            print(f"Error in 'blackjack' command: {error}")

    @commands.command(name="guess")
    async def guess(self, ctx, guess: int = 0):
        global game_in_progress
        user_id = ctx.author.id

        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return

        if user_id in game_in_progress:
            await ctx.send("You're already playing a game! Finish it before starting a new one.")
            return

        rate_limit_check = self.rate_limit_set(ctx, "guess")
        if not rate_limit_check:
            await ctx.send(f"You've used that command too frequently! Please try again in {remaining_time_str}")
            return

        target_number = random.randint(1, 100)


        embed = discord.Embed(
        title="**Game Start!**",
        description="Please type ``23`` if you want to guess 23, from 1-100",
        color=0x00FFFF  # Cyan color
    )
        await ctx.send(embed=embed)
        
        
        tries_left = 5
        game_in_progress[user_id] = True
        while tries_left > 0:
            def check_message(m):
                return m.author == ctx.author and m.content.isnumeric()

            try:
                guess = await self.bot.wait_for('message', check=check_message, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send(f"{ctx.author.mention}, you took too long! Game over!")
                del game_in_progress[user_id]
                return
            
            guess = int(guess.content)

            if guess < 1 or guess > 100:
                await ctx.send("Please guess a number between 1 and 100.")
                return

            tries_left -= 1 

            if guess < target_number:
                await ctx.send(f"Too low! You have **{tries_left}** tries left.")
            elif guess > target_number:
                await ctx.send(f"Too high! You have **{tries_left}** tries left.")
            else:
                await ctx.send(f"Congratulations! You guessed the number: **{target_number}**, and won **150** coins!")

                del game_in_progress[user_id]
                self.add_coins(150, ctx.author)
                return

        await ctx.send(f"Game over! The correct number was {target_number}.")
        del game_in_progress[user_id]
        return



    @commands.command(name="lottery")
    async def lottery(self, ctx, guess: str = None): 
        if guess is None:
            await ctx.send(f"Please input a number between 1-1000\n example ``!lottery 725``.\nFor the lottery rules, type ``!lottery help``")
            return
        elif guess == "help":
            embed = discord.Embed(
            title="**Lottery Rules**",
            description=(
            "The lottery is free to enter and there will be a winner every day at 12pm PST / 8 PM British time\n"
            "You must pick a number 1-1,000 and the person closest to the winning number will get a prize\n"
            "You may change your lucky number any time before the drawing takes place\n"
            "The lottery will reset every day so if you wish to enter for tomorrow's lottery, type !lottery again\n\n"
            "Our lottery system works like pacman to make it fair for everyone. In pacman if you go all the way "
            "to the left of the screen you pop out on the right side of the screen. "
            "Similarly, the difference between '1000 and 1' will be 1 unit away, instead of 999 units away, "
            "because if you reach the left side of the number line (#1) its connected to the right side of the number line (#1000)."
            ),
            color=0x00FFFF)
            await ctx.send(embed=embed)
            return
        else:        
            try:
                guess = int(guess)
                if guess < 1 or guess > 1000:
                    await ctx.send("Please guess a number between 1 and 1000.")
                    return
                
                cursor = self.conn.cursor()
                cursor.execute("UPDATE users SET lottery_guess = %s WHERE user_id = %s", (guess, ctx.author.id))
                self.conn.commit()

                await ctx.message.delete()
                await ctx.send(f"{ctx.author.display_name}, your lottery guess has been recorded!")
                role_to_add = discord.utils.get(ctx.guild.roles, id=LOTTERY_ID)
                await ctx.author.add_roles(role_to_add)
                return
            except ValueError:
                await ctx.send("The input is not recognized. Please provide a valid integer or 'help'.")
                return
            finally:
                    cursor.close()

    # Birthday Command
    @commands.command(name='birthday')
    async def birthday(self, ctx, input_date: str = ""):
        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return

        user_id = ctx.author.id
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT birthday FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                birthday = str(result[0])
                birthday_date = datetime.strptime(birthday, '%m-%d').date()
                formatted_date = birthday_date.strftime('%B %d')  # e.g., "August 10"
            else:
                birthday = None
        finally:
            cursor.close()

        if not input_date and birthday:           
            await ctx.send(f'Your birthday is saved as {formatted_date}!')
            return
        if not input_date and not birthday:
            await ctx.send("Please input `!birthday MM-DD` to set your birthday.")
            return
        

        # Parse the date in MM-DD format
        try:
            formatted_input_date = datetime.strptime(input_date, '%m-%d').date()
            formatted_input_date = formatted_input_date.strftime('%B %d')  # e.g., "August 10"
        except ValueError:
            await ctx.send('Invalid date format! Please use MM-DD format.')
            return
    
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET birthday = %s WHERE user_id = %s", (input_date, user_id))
            self.conn.commit()
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
        finally:
            cursor.close()

        # Send confirmation message
        await ctx.send(f'Your birthday {formatted_input_date} has been saved!')

    @birthday.error
    async def birthday_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please input `!birthday MM-DD`.")
        elif isinstance(error, ValueError):
            await ctx.send('Invalid date format! Please use MM-DD format.')
        else:
            await ctx.send(f"An unexpected error occurred: {error}")
    
    # Hangman Command
    @commands.command(name="hangman")
    async def hangman(self,ctx):
        user_id = str(ctx.author.id)

        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return

        if user_id in game_in_progress:
            await ctx.send("You're already playing a game! Finish it before starting a new one.")
            return

        rate_limit_check = self.rate_limit_set(ctx, "hangman")
        if not rate_limit_check:
            await ctx.send(f"You've used that command too frequently! Please try again in {remaining_time_str}")
            return

        game_in_progress[user_id] = True


        words = [
        "anxiety", "depression", "therapy", "mindfulness", 
        "stigma", "meditation", "coping",  "hope", "strength", 
        "positivity", "psychology", "motivation",
        "harmony", "calm", "relaxation", "courage", "nurture", 
        "breathe", "focus", "empower", "optimism", "compassion", "boundaries", 
        "peace", "journaling", "exercise", "routine",
        "expression", "vulnerability", "dopamine", "grief", "mindful", 
        "confidence", "belonging", "sleep", "diet", "hygiene", "goal", "progress", 
        "success", "kindness", "friendship", "connection", "communication", 
        "listening", "validation", "emotions", "stability",
        "positive",  "grace", "emotional",  "restoration", "wholeness", 
        "selfworth", "integration", "acceptance", "wellbeing", 
        "awareness", "fulfillment", "nourishment", "calmness",
        "empowerment", "healing","balance", "selfesteem",
        "reflection","inspiration", "gratitude", 
        "growth", "solace", "comfort", "rest", "clarity", "renewal",
        "wellness", "recovery", "serenity", "mindset", "positivity", "understanding", "presence", 
        "supportive", "rejuvenation", "restorative", "reassurance", 
        "patience", "encouragement", "empathy", "resilience", "contentment", 
        "selfcare", "purpose", "trust", "serotonin", "joy", "tranquility", "caring", "affirmation", 
        "compassionate", "compassion", "equilibrium", "rhythm", "heart", "unconditional", "amazing", 
        "thriving", "reciprocate", "silence", "mind", "body", "soul", "spirit", "energy", "vibe",
        "aura", "frequency", "vibration", "flow", "harmony", "balance", "alignment", "center", "core",
        "essence", "being", "presence", "consciousness", "awareness", "awakening", "enlightenment",
        "illumination", "realization", "self", "identity", "individuality", "personality", "character",
        "ambition", "drive", "motivation", "passion", "purpose", "vision", "goal", "dream", "desire",
        "intention", "aspiration", "inspiration", "creativity", "imagination"
        ]

        # Select a random word from the list
        word = random.choice(words)
        guessed_letters = []
        incorrect_guesses = 0
        max_incorrect = 6
        player_turn = True

        # Function to display the current hangman state
        def display_hangman():
            hangman_stages = [
                "```+---+\n    |\n    |\n    |\n   ===```",
                "```+---+\n O  |\n    |\n    |\n   ===```",
                "```+---+\n O  |\n |  |\n    |\n   ===```",
                "```+---+\n O  |\n/|  |\n    |\n   ===```",
                "```+---+\n O  |\n/|\\ |\n    |\n   ===```",
                "```+---+\n O  |\n/|\\ |\n/   |\n   ===```",
                "```+---+\n O  |\n/|\\ |\n/ \\ |\n   ===```"
            ]
            return hangman_stages[incorrect_guesses]

        # Function to display the current word state
        def display_word():
            return ' '.join([letter if letter in guessed_letters else '\\_' for letter in word])

        # Send initial game state
        embed = discord.Embed(title="Hangman", description=f"{display_hangman()}\n\nWord: {display_word()}", color=0x00FFFF)
        message = await ctx.send(embed=embed)

        while player_turn:
            def check_message(m):
                return m.author == ctx.author and (m.content.isalpha() or len(m.content.split()) == 1)

            try:
                guess = await self.bot.wait_for('message', check=check_message, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send(f"{ctx.author.mention}, you took too long! Game over!")
                del game_in_progress[user_id]
                return

            if guess:
                await guess.delete()

            guess = guess.content.lower()

            if guess in guessed_letters:
                embed.description = f"You've already guessed **{guess}**!!\n{display_hangman()}\n\nWord: {display_word()}"
                await message.edit(embed=embed)
                continue

             #Check if they guessed the whole word
            if guess == word:
                await ctx.send(f"Congratulations {ctx.author.mention}, you've won **150 coins**! The word was '{word}'.")
                del game_in_progress[user_id]
                player_turn = False
                self.add_coins(150, ctx.author)
                return

            if len(guess) == 1:  # Check if guess is a single letter
                guessed_letters.append(guess)
                if guess in word:
                    embed.description = f"'{guess}' is correct!!!\n{display_hangman()}\n\nWord: {display_word()}"
                    await message.edit(embed=embed)
                else:
                    incorrect_guesses += 1
                    embed.description = f"'{guess}' is incorrect!!\n{display_hangman()}\n\nWord: {display_word()}"
                    await message.edit(embed=embed)
                    # Check if the player lost
                    if incorrect_guesses >= max_incorrect:
                        await ctx.send(f"Sorry {ctx.author.mention}, you've lost! The word was '{word}'.")
                        player_turn = False
                        del game_in_progress[user_id]
                        return
                    continue

            # Check if the player has won
            if all(letter in guessed_letters for letter in word):
                await ctx.send(f"Congratulations {ctx.author.mention}, you've won **150 coins**! The word was '{word}'.")
                player_turn = False
                self.add_coins(150, ctx.author)
                del game_in_progress[user_id]
                return
            continue
    
    @commands.command(name="rls")
    async def rls(self,ctx,game: str = "none",target = "none"):
        if not any(role.id in [ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return  
        
        # Data [amount, timestamp(epoch)]
        data = {
            "dice": [0, False],
            "rps": [0, False],
            "daily": [0, False],
            "bypass": [0, False],
            "blackjack": [0, False],
            "guess": [0, False],
            "hangman": [0, False],
            "coinflip": [0, False]
        }

        if target == "none":
            target = 337118361009782786
        else:
            target = int(target.strip('<@!>'))

        if game == "none":
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE users SET rate_limits = %s WHERE user_id = %s", (json.dumps(data), target))
                await ctx.send(f"Cleared Rate Limits for all commands for {ctx.author.display_name}!")
                return
            finally:
                cursor.close()
                return

        if game not in data:
            await ctx.send("Please input a valid game!")
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT rate_limits FROM users WHERE user_id = %s", (target,))
            data = cursor.fetchone()[0]
            data[game][0] = 0
            cursor.execute("UPDATE users SET rate_limits = %s WHERE user_id = %s", (data, target))
            await ctx.send(f"Cleared Rate Limits for {game} for {ctx.author.display_name}!")
        finally:
            cursor.close()
            return
        
    
    # Coinflip Command
    @commands.command(name="coinflip")
    async def coinflip(self, ctx):
        global coinflip_message

        view = discord.ui.View()
        user_id = str(ctx.author.id)

        command_channel_value = self.command_channel_check(ctx)
        if not command_channel_value:
            await ctx.send(f"Please use <#{COMMANDS_ID}> to use commands!")
            return

        rate_limit_check = self.rate_limit_set(ctx, "coinflip")
        if not rate_limit_check:
            await ctx.send(f"You've used that command too frequently! Please try again in {remaining_time_str}")
            return

        # Creating buttons
        heads_button = discord.ui.Button(label="Heads", style=discord.ButtonStyle.green, custom_id="coinflip_heads")
        tails_button = discord.ui.Button(label="Tails", style=discord.ButtonStyle.green, custom_id="coinflip_tails")
        deny_button = discord.ui.Button(label="Deny", style=discord.ButtonStyle.red, custom_id="coinflip_deny")

        # Adding buttons to the view
        view.add_item(heads_button)
        view.add_item(tails_button)
        view.add_item(deny_button)
        
 
        embed = discord.Embed(title="Coinflip!", description=f"Would you like to bet **32 coins** to play?", color=0x00FFFF)
        coinflip_message[user_id] = await ctx.send(embed=embed, view=view)

    # Coinflip Logic
    async def coinflip_logic(self, interaction, choice: str):
        global coinflip_message
        global coinflip_amount
        
        embed = discord.Embed(title="Coinflip!", color=0x00FFFF)
        view = discord.ui.View()
        user_id = str(interaction.user.id)
        

        result = random.choice(["Heads", "Tails"])
        won = (choice == result)

        if choice != "coinflip_cashin":
            if user_id not in coinflip_amount:
                coinflip_amount[user_id] = 32
            else:
                coinflip_amount[user_id] *= 2
            await coinflip_message[user_id].delete()
            gif_url = "https://media.tenor.com/0Q3yMTo3lXgAAAAM/piece-coin.gif"
            gif_message = await interaction.channel.send(gif_url)
            await asyncio.sleep(2) 
            await gif_message.delete()
        else:
            self.add_coins(coinflip_amount[user_id],interaction.user)
            await interaction.channel.send(f"You gained **{coinflip_amount[user_id]} coins!**")
            del coinflip_amount[user_id]
            del coinflip_message[user_id]
            return


        if not won:
            message = f"The result was . . . {result}!\n Better luck next time!"
            embed.description = message
            await interaction.channel.send(embed=embed)
            del coinflip_amount[user_id]
            del coinflip_message[user_id]
            self.remove_coins(32, interaction.user)
            return
        

        if coinflip_amount[user_id] == 512:
            message = f"The result was . . . {result}!\nCongratulations! You won **{coinflip_amount[user_id]} coins**.\nYou reached the max amount!"
            await interaction.channel.send(embed=embed)
            self.add_coins(512, interaction.user)
            del coinflip_amount[user_id]
            del coinflip_message[user_id]
            return
        
        message = f"The result was . . . {result}!\nCongratulations! You won **{coinflip_amount[user_id]} coins**. Would you like to play again for double or nothing?"
        
        embed.description = message

        
        # Creating buttons
        heads_button = discord.ui.Button(label="Heads", style=discord.ButtonStyle.green, custom_id="coinflip_heads")
        tails_button = discord.ui.Button(label="Tails", style=discord.ButtonStyle.green, custom_id="coinflip_tails")
        cashin_button = discord.ui.Button(label="Cash-in", style=discord.ButtonStyle.red, custom_id="coinflip_cashin")
      
        # Adding buttons to the view
        view.add_item(heads_button)
        view.add_item(tails_button)
        view.add_item(cashin_button)
        
        coinflip_message[user_id] = await interaction.channel.send(embed=embed, view=view)


    @commands.command(name="shop")
    async def shop(self, ctx, *, role_name: str = None):
        shop_items = vanityRoles

        if role_name is None:
            items_per_page = 6
            pages = [list(shop_items.items())[i:i + items_per_page] for i in range(0, len(shop_items), items_per_page)]
            current_page = 0

            embed = discord.Embed(title="Shop", description="Available roles to buy:", color=0x00FFFF)
            for item, details in pages[current_page]:
                embed.add_field(name=item, value=f"Price: {details[1]} coins", inline=False)
            embed.set_footer(text=f"Page {current_page + 1}/{len(pages)}")

            message = await ctx.send(embed=embed)

            if len(pages) > 1:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                        if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                            current_page += 1
                        elif str(reaction.emoji) == "⬅️" and current_page > 0:
                            current_page -= 1
                        else:
                            continue

                        embed.clear_fields()
                        for item, details in pages[current_page]:
                            embed.add_field(name=item, value=f"Price: {details[1]} coins", inline=False)
                        embed.set_footer(text=f"Page {current_page + 1}/{len(pages)}")
                        await message.edit(embed=embed)
                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break

                await message.clear_reactions()
            return

        role_name = ''.join(role_name)
        role_name = role_name.title()
        if role_name not in shop_items:
            await ctx.send("Invalid selection! Please choose a valid role from the shop.")
            return

        user_id = str(ctx.author.id)
        if user_id not in coins or coins[user_id] < shop_items[role_name][1]:
            await ctx.send("You don't have enough coins to buy this role.")
            return

        role = discord.utils.get(ctx.guild.roles, id=shop_items[role_name][0])
        if role in ctx.author.roles:
            await ctx.send("You already have this role.")
            return

        self.remove_coins(shop_items[role_name][1], ctx.author)
        await ctx.author.add_roles(role)
        await ctx.send(f"Congratulations! You have bought the {role_name} role!")


async def setup(bot): # this is called by Pycord to setup the cog
    await bot.add_cog(economy(bot, bot.conn)) # add the cog to the bote cog
