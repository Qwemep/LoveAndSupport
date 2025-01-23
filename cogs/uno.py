import discord
from discord import Embed
from discord.ext import commands
from discord.ui import Button, View
import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
script_dir = os.path.dirname(os.path.abspath(__file__))
from .ids import *
import re
import asyncio
game1 = False
game2 = False




class uno(commands.Cog):
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        if self.conn is None:
            raise Exception("Failed to connect to the database")

    def add_coins(self, amount: int, target: discord.Member):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET coins = coins + %s WHERE user_id = %s", (amount, target.id))
            self.conn.commit()
        finally:
            cursor.close()

    class CustomView(View):
        def __init__(self, cog, timeout=None, message = None):
            super().__init__(timeout=timeout)
            self.cog = cog
            self.message = message

        async def on_timeout(self):
            if self.message:
                await self.message.delete()
            print("Timeout Happend!")
            return
        
        async def on_error(self, error, item, interaction):
            # Print the error in the console
            print(f"Error in {item.custom_id}: {error}")
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)


    @commands.command(name="uno")
    async def uno (self, ctx):
        global game1
        global game2
        
        colors = ["🟥 Red","🟨 Yellow","🟩 Green","🟦 Blue"]
        deck = [] 
        hand = {}
        menu_message = False
        image_color = False
        image_value = 0
        card_count = 0
        hand_message = {}
        menu_been_ran = False
        players_joined = []
        turn_person = False
        direction = "🔻"
        plus_flag = False
        plus_amount = 0
        handView = {}


        if ctx.message.channel.id != UNO_ONE_ID and ctx.message.channel.id != UNO_TWO_ID:
            await ctx.send("Please head over to a uno channel to play!")
            return

        if ctx.message.channel.id == UNO_ONE_ID:
            if not game1:
                game1 = True
            else:
                await ctx.send("There is already a game playing here!")
                return
        
        if ctx.message.channel.id == UNO_TWO_ID:
            if not game2:
                game2 = True
            else:
                await ctx.send("There is already a game playing here!")
                return
        

        def create_deck():
        # Initialize the deck
            nonlocal deck 
            print("Creating Deck")
            deck = []

            # Standard numbered cards and special cards for each color
            for color in colors:
                for i in range(1, 10):  # 1-9
                    deck.append(f"{color} {i}")
                deck.append(f"{color} Skip❌") # Skip
                deck.append(f"{color} Reverse🔁")  # Reverse
                deck.append(f"{color} +2")  # Draw 2
        
        
            # Add another set of the same colored cards (minus the 0s)
            deck.extend(deck)

            # Adding "0" card separately as it's unique (only one per color)
            for color in colors:
                deck.append(f"{color} 0")

            # Wild cards (these are non-colored)
            for _ in range(4):#4
                deck.append("🌈 Wild")
                deck.append("🌈 Wild +4")
            return

        def create_hand(bisexual):
            nonlocal hand
            nonlocal players_joined

            if isinstance(bisexual, commands.Context):
                player = bisexual.author
            elif isinstance(bisexual, discord.Interaction):
                player = bisexual.user

            user_id = str(player.id)
            if user_id not in hand:
                hand[user_id] = []

            for _ in range(7):#7
                pick = random.randint(0, len(deck) - 1) 
                card = deck.pop(pick) 
                hand[user_id].append(card)

            players_joined.append(player)
            return

        async def create_menu(bisexual):
            nonlocal menu_been_ran
            nonlocal menu_message
            nonlocal players_joined

            name_list = ""
            for player in players_joined:
                name_list += f"{player.display_name}\n"

            embed = Embed(
                title=f"Welcome to L&S Uno",
                description=f"Current Players ({len(players_joined)}/3):\n{name_list}",
                color = 0xFF0000
            )
            view = self.CustomView(self)
            button0 = Button(
                label = "Join Game",
                style= discord.ButtonStyle.blurple,
                custom_id="uno join game"
            )
            button1 = Button(
                label = "Start Game",
                style= discord.ButtonStyle.green,
                custom_id="uno start game"
            )
            button2 = Button(
                label = "Cancel Game",
                style= discord.ButtonStyle.red,
                custom_id="uno cancel game"
            )
            
            
            view.add_item(button0)
            view.add_item(button1)
            view.add_item(button2)

            button0.callback = button_callback
            button1.callback = button_callback
            button2.callback = button_callback
            if not menu_been_ran:
                menu_been_ran = True
                menu_message = await bisexual.send(embed=embed,view=view)
            else:
                await menu_message.edit(embed=embed,view=view)
            return

        def starting_card():
            nonlocal deck
            starting_card = deck.pop(random.randint(0, len(deck) -9))
            process_color(starting_card)
            process_value(starting_card)
            return

        def process_color(bisexual):
            nonlocal image_color

            if isinstance(bisexual, str):
                card = bisexual.lower()
            elif isinstance(bisexual, discord.Interaction):
                card = bisexual.data["custom_id"].lower()

            if "green" in card:
                image_color = "green"
            elif "blue" in card:
                image_color = "blue"
            elif "red" in card:
                image_color = "red"
            elif "yellow" in card:
                image_color = "yellow"
            else:
                image_color = "wild"
            return
        
        def process_value(bisexual):
            nonlocal image_value

            if isinstance(bisexual, str):
                card = bisexual.lower()
            elif isinstance(bisexual, discord.Interaction):
                card = bisexual.data["custom_id"].lower()

            if "passthrough" in card:
                image_value = "PT"
            elif "+2" in card:
                image_value = "+2"
            elif "+4" in card:
                image_value = "+4"
            elif "reverse" in card:
                image_value = "reverse"
            elif "skip" in card:
                image_value = "skip"
            else:
                matches = re.findall(r'\d', card)
                image_value = matches[-1]

        def reconstruct_card():
            nonlocal image_color
            nonlocal image_value

            if image_color == "red":
                color = "🟥 Red "
            elif image_color == "green":
                color = "🟩 Green "
            elif image_color == "blue":
                color = "🟦 Blue "
            elif image_color == "yellow":
                color = "🟨 Yellow "
            else:
                color = "🌈 Wild"
        
            if "+4" == image_value:
                value = " +4"
            elif "+2" == image_value:
                value = "+2"
            elif "reverse" == image_value:
                value = "Reverse🔁"
            elif "skip" == image_value:
                value = "Skip❌"
            else:
                value = image_value 
    
            if color == "🌈 Wild" and value != " +4":
                value = ""

            return color + value

        def update_image():
            nonlocal image_value
            nonlocal image_color

            if image_value == "PT":
                conditioned = ""
            else:
                conditioned = image_value

            return f"https://www.flippercat.com/uno/{image_color}{conditioned}.png"

        # Button Callback
        async def button_callback(interaction: discord.Interaction):
            nonlocal image_color
            nonlocal image_value
            nonlocal turn_person
            nonlocal deck
            nonlocal hand
            nonlocal plus_flag
            nonlocal plus_amount
            nonlocal menu_message
            nonlocal players_joined
            nonlocal handView

            global game1
            global game2

            
                
            user_id = str(interaction.user.id)
            user_hand = hand.get(user_id, [])

            if not interaction.response.is_done():
                await interaction.response.defer()
            

            #################


            if interaction.data['custom_id'] == "uno join game":
                if interaction.user in players_joined:
                    await interaction.channel.send(f"{interaction.user.display_name}, you're already playing!")
                    return
                if len(players_joined) == 5:
                    await interaction.channel.send("Maximum amount of players joined!")
                    return

                create_hand(interaction)
                await create_menu(interaction)
                return
            
            elif interaction.data['custom_id'] == "uno start game":
                if len(players_joined) > 2:
                    turn_person = players_joined[0]
                    starting_card()
                    await current_board(interaction, update_image())
                    await timeout(interaction)
                    return
                else:
                    await interaction.channel.send("Sorry, you must have at least four players to play!")
                    return

            elif interaction.data['custom_id'] == "uno cancel game":
                await menu_message.delete()
                if interaction.channel.id == UNO_ONE_ID:
                    game1 = False
                elif interaction.channel.id == UNO_TWO_ID:
                    game2 = False
                return
            

            #################

            
            if interaction.user not in players_joined:
                msg = await interaction.channel.send(f"{interaction.user.display_name}, you're not playing!")
                await asyncio.sleep(4)
                await msg.delete()
                return

            if interaction.data["custom_id"] == "uno show hand":
                if user_id in hand_message:
                    del hand_message[user_id]
                    del handView[user_id]
                await show_hand(interaction)
                return
            
            # Check turn
            if turn_person != interaction.user:
                await interaction.followup.send(f"{interaction.user.display_name}, it is not your turn!", ephemeral=True)
                return

            if interaction.data["custom_id"] == "uno draw":
                await draw_card(interaction, 1, interaction.user)
                msg = await interaction.channel.send(f"{interaction.user.display_name} Passed their turn!")
                passturn()
                await update_hands(interaction)
                await current_board(interaction, update_image())
                await asyncio.sleep(4)
                await msg.delete()
                return

            if interaction.data['custom_id'] == "uno plus":
                plus_flag = False
                msg = await interaction.channel.send(f"{interaction.user.display_name} got hit with the +{plus_amount}!")
                await draw_card(interaction, plus_amount, interaction.user)
                plus_amount = 0
                passturn()
                await update_hands(interaction)
                await current_board(interaction, update_image())
                await asyncio.sleep(4)
                await msg.delete()
                return

            process_color(interaction)
            process_value(interaction)
            card = reconstruct_card()


            await special_cards()


            if image_value != "PT":
                if card in user_hand:
                    hand[user_id].remove(card)


            if image_color == "wild":
                await wild_menu(interaction)
                return
        
            passturn()
            await current_board(interaction, update_image())
            await update_hands(interaction, plus_flag)
            await check_win(interaction)
            await timeout(interaction)
            return

        async def draw_card(interaction, amount, target):
            nonlocal hand
            nonlocal deck
            user_id = str(target.id)

            for _ in range(amount):
                if len(deck) == 0:
                    create_deck()
                if len(hand[user_id]) < 24:
                    hand[user_id].append(deck.pop(random.randint(0, len(deck) - 1)))
                    await update_hands(interaction)
                else:
                    msg = await interaction.channel.send(f"{interaction.user.display_name}, you can only have up to 24 cards in your hand!")
                    await asyncio.sleep(4)
                    await msg.delete()
                    break
            return

        async def special_cards():
            nonlocal image_value
            nonlocal players_joined
            nonlocal turn_person
            nonlocal hand
            nonlocal deck
            nonlocal direction
            nonlocal plus_flag
            nonlocal plus_amount


            if image_value == "+2":
                plus_flag = 2
                plus_amount += plus_flag
            elif image_value == "+4":
                plus_flag = 4
                plus_amount += plus_flag
            elif image_value == "reverse":
                if direction == "🔻":
                    direction = "🔺"
                else:
                    direction = "🔻"
            elif image_value == "skip":
                passturn()

            return
                    
        async def current_board(interaction, image):
            nonlocal menu_message
            nonlocal turn_person
            nonlocal players_joined
            nonlocal hand
            nonlocal direction

            if not interaction.response.is_done():
                await interaction.response.defer()


            view=self.CustomView(self)
            embed = Embed(
                title="L&S Uno",
                description=f"It is **{turn_person.display_name}**'s turn!",
                color = 0xFF0000
            )
            
        
            button = Button(label="Show Hand", style=discord.ButtonStyle.success, custom_id="uno show hand")

            footer = ""
            for player in players_joined:
                footer += f"• {player.display_name}'s cards: {len(hand[str(player.id)])}    "
                if player == turn_person:
                    footer += direction
                footer += "\n"

            embed.set_footer(text=footer)
            button.callback = button_callback
            view.add_item(button)
            embed.set_thumbnail(url=image)

            await menu_message.edit(embed=embed, view=view)

            return

        async def wild_menu(interaction):
            if not interaction.response.is_done():
                await interaction.response.defer()

            user_id = str(interaction.user.id)

            view = self.CustomView(self)
            buttonred = Button(label="🟥 Red",style=discord.ButtonStyle.gray,custom_id=f"uno passthrough {image_value}red",disabled=False)
            buttonblue = Button(label="🟦 Blue",style=discord.ButtonStyle.gray,custom_id=f"uno passthrough{image_value}blue",disabled=False)
            buttonyellow = Button(label="🟨 Yellow",style=discord.ButtonStyle.gray,custom_id=f"uno passthrough {image_value}yellow",disabled=False)
            buttongreen = Button(label="🟩 Green",style=discord.ButtonStyle.gray,custom_id=f"uno passthrough {image_value}green",disabled=False)

            buttonred.callback = button_callback
            buttonblue.callback = button_callback
            buttonyellow.callback = button_callback
            buttongreen.callback = button_callback

            view.add_item(buttonred)
            view.add_item(buttonblue)
            view.add_item(buttonyellow)
            view.add_item(buttongreen)

            await hand_message[user_id].edit(view=view)

        async def show_hand(interaction, flag = False):

            # Ensure the user's hand is properly initialized
            user_id = str(interaction.user.id)
            nonlocal hand_message
            nonlocal plus_flag

            if user_id in hand_message:
                await hand_message[user_id].delete()
      
            if not plus_flag:
                view = generate_buttons(interaction.user)
            else:
                view = generate_plus_buttons(interaction.user)

            hand_message[user_id]  = await interaction.followup.send("Here is your hand:", view=view, ephemeral= True)
            view.message = hand_message[user_id]
            return
                     
        async def update_hands(interaction, flag = False):
            nonlocal players_joined
            nonlocal plus_flag

            for player in players_joined:
                user_id = str(player.id)

                if not plus_flag:
                    view = generate_buttons(player)
                else:
                    view = generate_plus_buttons(player)
              
                await hand_message[user_id].edit(view=view)
            return
                
        def passturn():
            nonlocal turn_person
            nonlocal players_joined
            nonlocal turn_person

            index = players_joined.index(turn_person)


            if direction == "🔻":
                if turn_person != players_joined[-1]:
                    turn_person = players_joined[index + 1]
                else:
                    turn_person = players_joined[0]
            else:
                if turn_person == players_joined[0]:
                    turn_person = players_joined[-1]
                else:
                    turn_person = players_joined[index - 1]


            return

        def generate_buttons(player):
            nonlocal card_count
            nonlocal turn_person
            nonlocal players_joined
            nonlocal handView

            user_id = str(player.id)

            if user_id not in handView:
                handView[user_id] = self.CustomView(self)    
            else:
                handView[user_id].clear_items()

           
            id = str(player.id)
            player_hand = hand.get(str(id), [])

            for card in player_hand:
                card_lower = card.lower()  # Convert card to lowercase

                if turn_person != player:
                    match = True
                elif "wild" in card_lower:
                    match = False
                elif image_color in card_lower:
                    match = False
                elif image_value == "2" and "+2" in card_lower:
                    match = True
                elif image_value in card_lower and image_value != "":
                    match = False
                else:
                    match = True
            

                button = Button(
                    label=card,
                    style=discord.ButtonStyle.gray,
                    custom_id=f"uno{card_count}{card}",
                    disabled= match
                )
                card_count += 1

                button.callback = button_callback
                handView[user_id].add_item(button)
                
            if turn_person != player:
                match = True
            else:
                match = False

            draw_button = Button(label = "Draw Card",style = discord.ButtonStyle.gray,custom_id=f"uno draw", disabled = match)
            draw_button.callback = button_callback
            handView[user_id].add_item(draw_button)

            return handView[user_id]
        
        def generate_plus_buttons(player):
            nonlocal card_count
            nonlocal plus_amount
            nonlocal turn_person
            nonlocal players_joined
            nonlocal plus_flag
            nonlocal handView
            user_id = str(player.id)

            if user_id not in handView:
                handView[user_id] = self.CustomView(self, timeout=10)    
            else:
                handView[user_id].clear_items()
            
            id = str(player.id)
            player_hand = hand.get(str(id), [])

            for card in player_hand:
                card_lower = card.lower()  # Convert card to lowercase

                if turn_person != player:
                    match = True
                elif "+" + str(plus_flag) in card_lower:
                    match = False
                elif "+4" in card_lower:
                    match = False
                else:
                    match = True
            

                button = Button(
                    label=card,
                    style=discord.ButtonStyle.gray,
                    custom_id=f"uno{card_count}{card}",
                    disabled= match
                )
                card_count += 1

                button.callback = button_callback
                handView[user_id].add_item(button)
                
            if turn_person != player:
                match = True
            else:
                match = False
            draw_button = Button(label = "Draw " +str(plus_amount)+" Cards",style = discord.ButtonStyle.gray,custom_id=f"uno plus", disabled = match)
            draw_button.callback = button_callback
            handView[user_id].add_item(draw_button)

            return handView[user_id]

        async def one_card(interaction):

            def check(message):
                return message.author == interaction.user  and message.content.lower() == "uno"
        
            try:
                message = await self.bot.wait_for('message', timeout=5.0, check=check)
                msg = await interaction.channel.send(f"{interaction.user.display_name} has one card left!")
                await asyncio.sleep(4)
                await msg.delete()

            except asyncio.TimeoutError:
                msg = await interaction.channel.send(f"{interaction.user.display_name}, you didn't type 'uno' in time!\nDraw two cards!")
                await draw_card(interaction,2,interaction.user)
                await asyncio.sleep(4)
                await msg.delete()

        async def check_win(interaction):
            nonlocal hand
            nonlocal menu_message
            global game1
            global game2

            user_id = str(interaction.user.id)

            if len(hand[user_id]) == 1:
                await one_card(interaction)

            if len(hand[user_id]) == 0:
                await menu_message.delete()
                await interaction.channel.send(f"{interaction.user.display_name} Won!\n**100 coins** have been added to your account!")
                self.add_coins(100, interaction.user)
                if interaction.channel.id == UNO_ONE_ID:
                    game1 = False
                elif interaction.channel.id == UNO_TWO_ID:
                    game2 = False
                return

        async def timeout(interaction):
            nonlocal menu_message
            nonlocal turn_person

            def check(message, id):
                return message == menu_message and message.id == menu_message.id

            try:
                 message = await self.bot.wait_for('message_edit', timeout=300.0, check=check)

            except asyncio.TimeoutError:
                await menu_message.delete()
                await interaction.channel.send(f"Game timed out!")
                if interaction.channel.id == UNO_ONE_ID:
                    game1 = False
                elif interaction.channel.id == UNO_TWO_ID:
                    game2 = False
                return
            
        create_deck()
        create_hand(ctx)
        await create_menu(ctx)




async def setup(bot): # this is called by Pycord to setup the cog
    await bot.add_cog(uno(bot, bot.conn)) # add the cog to the bot