import discord
from discord.ext import commands, tasks
from discord import Embed
import os
import sys
import time
import random
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




farm_data = {}
vegetables = {
    'daisy': {'price': 40, 'time': 30},
    'tulip': {'price': 50, 'time': 30},
    'pumpkin': {'price': 100, 'time': 60},
    'mango': {'price': 100, 'time': 60},
    'corn': {'price': 240, 'time': 120},
    'chilli': {'price': 240, 'time': 120},
    'watermelon': {'price': 400, 'time': 180},
    'pineapple': {'price': 400, 'time': 180},
}


images = {}
script_dir = os.path.dirname(os.path.abspath(__file__))
images["starting"] = os.path.join(script_dir, "../crops/starting.png")

for vegetable in vegetables:
    images[f"{vegetable}_progress"] = os.path.join(script_dir, f"../crops/{vegetable}_progress.png")
    images[f"{vegetable}_done"] = os.path.join(script_dir, f"../crops/{vegetable}_done.png")



class Farm(commands.Cog):
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        if self.conn is None:
            raise Exception("Failed to connect to the database")

        self.all_crops = list(vegetables.keys())

        self.available_seeds = []
        self.fertilizer = 0

        self.load_data()
        self.daily_tasks.start()
        

    @tasks.loop(hours = 20)
    async def daily_tasks(self):
        await self.random_gen()
        
    
    # Seed Generation
    async def random_gen(self):
        self.available_seeds = random.sample(self.all_crops, 3)
        self.fertilizer = random.randint(1, 16)

        if self.fertilizer == 1:
            self.fertilizer = "super"
        elif self.fertilizer <= 4:
            self.fertilizer = "regular"
        else:
            self.fertilizer = False
        print(f"Seeds: {self.available_seeds}", f"Fertilizer: {self.fertilizer}", sep='\n')

               
    def load_data(self):
        global farm_data

        parent_dir = os.path.dirname(script_dir)
        json_directory = os.path.join(parent_dir, 'json')
        farm_path = os.path.join(json_directory, 'farm_data.json')


    def save_data(self, member: discord.User, crop: str = None, seed: str = None, misc: str = None,plot: bool = None):
        global farm_data
        self.load_data()

        id = str(member.id)        
        if id not in farm_data:
            new_player(member)
        
        if plot:
            if farm_data[id]['amount_plots'] < 3:
                farm_data[id]['amount_plots'] += 1
                return False
            return "You already have 3 plots."
        
        if seed:
            if seed in farm_data[id]['seeds']:
                farm_data[id]['seeds'][seed] += 1
                return False
            return "Invalid seed."
        
        if misc:
            farm_data[id]['misc'][misc] += 1
            return False
        

        def new_player(self, member):
            farm_data[member.id] = {
                'crops': [False, False, False],
                'harvest_date': [False, False, False],
                'amount_plots': 1,
                'seeds': {},
                'misc': {'regular': 0, 'super': 0}
            }
            for crop in self.all_crops:
                farm_data[self.user.id]['seeds'][crop] = 0


    @commands.command(name='farm')
    async def farm(self, ctx, action=None, item=None):
        # Tutorial
        if action is None:
            embed = Embed(title="Welcome to L&S Farming", description='''Here you can farm the tutorial of what you can do in the farm.\n
                          To talk to the shop owner, type `!farm shop`. You might be able to buy seeds from him!\n
                          To see your inventory of seeds, type `!farm inventory`.\n
                          To plant a seed, type `!farm plant [seed]`.\n
                          To see the status of your current crops, type `!farm status`.\n
                          To see the news, type `!farm news`.\n
                          ''', color=0x00ffff)
            
            await ctx.send(embed=embed)

        # Shop
        elif action.lower() == 'shop':
            embed = Embed(title="The Shop", description="Hey there welcome to the shop!\nFeel free to take a look at what i've got in stock.\n\n To buy anything, just say `!farm buy [seed]`", color=0x00ffff)
            for seed in self.available_seeds:
                price = vegetables[seed]['price']
                embed.add_field(name=f"{seed.capitalize()} Seed", value=f"${price} coins", inline=False)

            if self.fertilizer == "super":
                embed.add_field(name="Super Fertilizer", value="$600 coins", inline=False)
            elif self.fertilizer:
                embed.add_field(name="Fertilizer", value=f"$200 coins", inline=False)
            
            await ctx.send(embed=embed)
            
        # Buy
        elif action.lower() == 'buy' and item:
            item = item.lower()

            # Buy Seed
            if item in self.available_seeds:
                price = vegetables[item]['price']


                if True:
                    self.save_data(ctx.author, seed=item)

                    await ctx.send(embed=Embed(description=f"You have successfully bought {item.capitalize()} seed for {price} coins.", color=0x00ff00))
                else:
                    await ctx.send(embed=Embed(description=f"You don't have enough coins to buy this crop. Current balance: {current_coins} coins.", color=discord.Color.red()))

            # Buy Fertilizer
            elif "fertilizer" in item:
                if self.fertilizer:
                    price = 600 if self.fertilizer == "super" else 200



                    self.save_data(ctx.author, misc=self.fertilizer)

                    await ctx.send(embed=Embed(description=f"You have successfully bought {self.fertilizer} fertilizer for {price} coins.", color=0x00ff00))
                    
                    await ctx.send(embed=Embed(description=f"You don't have enough coins to buy this fertilizer. Current balance:  coins.", color=discord.Color.red()))
                else:
                    await ctx.send(embed=Embed(description="Hey! I don't have any fertilizer on sale right now.", color=discord.Color.red()))

            #Invalid buy item
            else:
                await ctx.send(embed=Embed(description="Hey! I don't have that item available to sell at the moment.", color=discord.Color.red()))


        # Plant
        elif action.lower() == 'plant':
            for i in range(farm_data[id]['amount_plots']):
                if not farm_data[id]['crops'][i]:
                    farm_data[id]['crops'][i] = crop
                    farm_data[id]['harvest_date'][i] = time.time()
                    return False
                return "You don't have any available plots to plant this crop."
        
            file = discord.File(images["starting"], filename="image.png")
            embed = Embed(title=f"{item.capitalize()} planted", 
                    description=f"You have planted {item}. It will be ready to harvest in {grow_time} minutes.", 
                    color=0x00ff00).set_image(url="attachment://image.png")

        # Harvest
        elif action.lower() == 'harvest':
            if ctx.author.id in self.user_crops:
                current_time = time.time()
                planted_time = self.user_timestamps[ctx.author.id]
                crop = self.user_crops[ctx.author.id]
                crop_data = vegetables[crop]
                grow_time = crop_data['time']

                if current_time - planted_time >= grow_time * 60:
                    file = discord.File(images[f"{crop}_done"], filename="image.png")
                    harvested_veg = self.user_crops.pop(ctx.author.id)
                    self.user_timestamps.pop(ctx.author.id)

                    sell_price = random.randint(int(crop_data['price']*1.2), int(crop_data['price']*1.8))


                    await ctx.send(embed=Embed(description=f"You've harvested and sold your {harvested_veg}! You sold this harvest for **{sell_price}** coins!", 
                                            color=0x00ff00).set_image(url="attachment://image.png"), file=file)

                    if str(ctx.author.id) in farm_data:
                        del farm_data[str(ctx.author.id)]

                else:
                    remaining_time = int((planted_time + grow_time * 60) - current_time)
                    if remaining_time >= grow_time * 30:
                        file = discord.File(images["starting"], filename="image.png")
                        await ctx.send(embed=Embed(description=f"Your {crop} is not ready to harvest yet. Remaining time: {remaining_time} seconds.", 
                                                     color=discord.Color.red()).set_image(url="attachment://image.png"), file=file)
                    else:
                        file = discord.File(images[f"{crop}_progress"], filename="image.png")
                        await ctx.send(embed=Embed(description=f"Your {crop} is almost ready to harvest. Remaining time: {remaining_time} seconds.", 
                                                     color=discord.Color.gold()).set_image(url="attachment://image.png"), file=file)
            else:
                await ctx.send(embed=Embed(description="You don't have any crops to harvest.", color=discord.Color.red()))

        # Invalid Command
        else:
            await ctx.send(embed=Embed(description="Invalid command. Use `!farm` to see the list of vegetables, `!farm buy [vegetable]` to plant, or `!farm harvest` to harvest.", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(Farm(bot, bot.conn))




# Seasonal crops
# Price alerts up or down
# Sales on seeds
# Planting multiple crops
# Harvesting multiple crops
# Crops take more time to grow
# More Crops
# Shop one seed at a time
# Guy shop image
# not ready to harvest remaning time
# ping when ready to harvest
# Inventory to store seeds
# fertilizer to speed up growth