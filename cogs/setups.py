import discord
from discord.ext import commands
from discord.ui import View, Button
from .ids import *
import os
from datetime import timedelta
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import script_dir 

class setups(commands.Cog): # create a class for our cog that inherits from commands.Cog

    def __init__(self, bot, db_connection):
        self.bot = bot
        self.conn = db_connection
        if self.conn is None:
            raise Exception("Failed to connect to the database")

    # Break Command
    @commands.command(name='break')
    async def timeout(self, ctx):  
        try:
            await ctx.message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(hours=1))
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    # Rules Setup
    @commands.command(name="rulesSetup")
    async def rulesSetup(self, ctx):
        if not any(role.id in [ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        await ctx.message.delete()

        image_path = os.path.join(script_dir, 'rules.png')
        # Attach the image and send it
        file = discord.File(image_path, filename="rules.png")
        await ctx.send(file=file)

        rules_message = """
        **╰┈➤1. Be respectful of other's wishes\n

        ╰┈➤2. Be supportive of others\n

        ╰┈➤3. Do not say slurs or derogatory terms or engage in gossip and drama\n

        ╰┈➤4. Do not discriminate others. This includes LGBTQ, race, sex, gender, or disability status.\n

        ╰┈➤5. Do not discuss politics or religion\n

        ╰┈➤6. You shouldn't treat a lighthearted chat as you would a DM.\n

        ╰┈➤7. Keep lighthearted topics in lighthearted chats.\n

        ╰┈➤8. No sexually-explicit messages\n

        ╰┈➤9. Keep heavy banter in dms, not in chat.\n

        ╰┈➤10. Use TW when appropriate\n

        ╰┈➤11. Must speak in English\n

        ╰┈➤12. This is not a dating server\n

        ╰┈➤13. Do not ping people in the void\n

        ╰┈➤14. Do not avoid bans/mutes/chat filters\n

        ╰┈➤15. Do not spam\n

        ╰┈➤16. Do not promote without permission\n

        ╰┈➤17. Requests for money are not allowed\n

        ╰┈➤18. No inappropriate profiles. This includes blank names, weird Unicode characters, political views, or offensive material\n

        ╰┈➤19. Be respectful of Staff's wishes. If there is any problem, you are allowed to make a ticket to discuss further or directly make a complaint regarding a staff member\n

        ╰┈➤20. Abide by Discord’s Terms of Service and Community Guidelines**\n
        """
        await ctx.send(rules_message)


        embed = discord.Embed(
            title="Welcome!",
            description=("To gain access to all its features and channels, please confirm that you've read and agree to the rules above.\n\n"
                        "Afterwards, you'll be able to fully engage with our community and participate in all our events and activities."),
            color=discord.Color.from_rgb(0, 255, 255)  # Cyan color (RGB: 0, 255, 255)
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.green, label="Agree", custom_id="agree"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.red, label="Disagree", custom_id="disagree"))

        await ctx.send(embed=embed, view=view)

    # Role Setup
    @commands.command(name="roleSetup")
    async def roleSetup(self, ctx):
        if not any(role.id in [ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        blank_message = "\u200b"  # Zero-width space
        # Define embed messages and their options
        embeds = [
            {
                "title": "What are your pronouns?",
                "options": [
                    ("She/her", 1263385997605994509),
                    ("They/them", 1263386058200977410),
                    ("He/him", 1263386088207159356),
                    ("Pronouns in bio!", 1263386230846914582)
                ]
            },
            {
                "title": "What is your gender?",
                "options": [
                    ("Female", 1263388334919651408),
                    ("Non-binary", 1263388482219409459),
                    ("Male", 1263388579577729045),
                    ("Cis", 1263389144076386439),
                    ("Trans", 1263389200095379557),
                    ("Gender in bio!", 1263393908449083415)
                ]
            },
            {
                "title": "What continent do you live in?",
                "options": [
                    ("North America", 1263390260445052989),
                    ("South America", 1263390358864396329),
                    ("Europe", 1263390445023657986),
                    ("Asia", 1263390546463035393),
                    ("Africa", 1263390657674739795),
                    ("Oceania", 1263390788704796702)
                ]
            },
            {
                "title": "What is your sexuality?",
                "options": [
                    ("Straight", 1263391813507616859),
                    ("Gay", 1263391909855105065),
                    ("Lesbian", 1263391967740432445),
                    ("Bisexual", 1263392031082938419),
                    ("Pansexual", 1263392094245093489),
                    ("Asexual Spectrum", 1263392191414407291),
                    ("Aromantic Spectrum", 1263392545111674901),
                    ("Queer", 1263392592939319327),
                    ("Sexuality in bio!", 1263394180676190208)
                ]
            },
            {
                "title": "DM Status?",
                "options": [
                    ("DMs Open", 1263395811501539359),
                    ("Ask DMs", 1263395877871947808),
                    ("DMs Closed", 1263395916728107081)
                ]
            },
            {
                "title": "What is your age?",
                "options": [
                    ("Teen", 1263396555159769201),
                    ("Young Adult (18-29)", 1263396601838440509),
                    ("Adult (30+)", 1263396621748539473)
                ]
            },
            {
                "title": "Pings?",
                "options": [
                    ("Dead chat ping!", 1268716336586948628),
                    ("Level up! Pings", 1264682843586564218),
                    ("Announcement pings!", 1264684496301588593),
                    ("VC Party pings!", 1270176990795792465),
                    ("Events pings!", 1270537704936964158),
                    ("Bump us Pings!", 1312575150104903772),
                ]
            },
            {
                "title":"Common MH Diagnoses",
                "options":[
                    ("Depression", 1263399301917179935),
                    ("Anxiety", 1263399335765475348),
                    ("Bipolar", 1263399362495778856),
                    ("OCD", 1263399386118094898),
                    ("ASD", 1263399415717302373),
                    ("ADHD", 1263399444267925576),
                    ("Schizophrenia/Schizoaffective", 1263399499452256343),
                    ("Borderline Personality Disorder", 1263399633359736842),
                    ("Other Personality Disorder", 1272389409332924529),
                    ("Gender Dysphoria", 1263399668226723924),
                    ("PTSD", 1263399691584933939),
                    ("Panic Disorder", 1263399728700325891),
                    ("Addiction", 1263399759499231335),
                    ("DID/OSDD", 1263399789232525356),
                    ("Eating Disorder", 1317976085450854421),
                    ("Other MH Diagnosis", 1263399944203669514)
            ]
            },
            {
                "title":"Common Physical Impairments",
                "options":[
                    ("Sleep Disorder", 1327869792492720159),
                    ("Visual Impairment", 1263401391808974901),
                    ("Hearing Impairment", 1263401436897607802),
                    ("Cystic Fibrosis", 1263401475514830902),
                    ("Epilepsy", 1263401503373131777),
                    ("Cerebral Palsy", 1263401551741845556),
                    ("Multiple Sclerosis", 1263401589104967761),
                    ("Speech & Language Disability", 1263401661880078388),
                    ("Tourette's", 1263401691932393513),
                    ("Gastrointestinal Problems", 1264689372670984273),
                    ("Other Chronic Illness", 1263401728418517087),
                    ("Other Physical Disability", 1263401763042754673)
                ]
            }
        ]

        for embed_info in embeds:
            embed = discord.Embed(
                title=embed_info["title"],
                color=discord.Color.from_rgb(0, 255, 255)  # Cyan color
            )

            view = discord.ui.View()
            for label, role_id in embed_info["options"]:
                # Convert role_id to string to use in custom_id
                button = discord.ui.Button(style=discord.ButtonStyle.primary, label=label, custom_id=str(role_id))
                view.add_item(button)
            
            await ctx.send(embed=embed, view=view)
            await ctx.send(blank_message)

    # Ticket Setup
    @commands.command(name="ticketSetup")
    async def ticketSetup(self, ctx):
        if not any(role.id in [ADMIN_ROLE_ID] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        # Create a button with a custom ID
        report_button = Button(label="Member Report or Complaint", emoji="✉️", style=discord.ButtonStyle.primary, custom_id="report")
        question_button = Button(label="Server Question", emoji="✉️", style=discord.ButtonStyle.primary, custom_id="question")
        staff_button = Button(label="Staff Report", emoji="✉️", style=discord.ButtonStyle.primary, custom_id="staff")

        # Create a view and add the button to it
        view = View()
        view.add_item(report_button)
        view.add_item(question_button)
        viewStaff = View()
        viewStaff.add_item(staff_button)

        # Send a message with the button
        await ctx.send(
        "Welcome to L&S Ticketing service.\n"
        "\n"
        "If you have a member report / complaint, or a server question:\n"
        "\n"
        "Please select one of the buttons below", 
        view=view
        )
        blank_message = "\u200b"  # Zero-width space
        await ctx.send(blank_message)
        await ctx.send(
            "If you would like to create a staff report or an Admin ticket,\n"
            "\n"
            "Please select the button below",
            view=viewStaff
        )

    # Clock-in Setup
    @commands.command(name="clockInSetup")
    async def clockInSetup(self, ctx):
        if not any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return
        
        await ctx.message.delete()

        # Create a button with a custom ID
        clockin_button = Button(label="Clock in", emoji="⌚", style=discord.ButtonStyle.success, custom_id="clockin")

        # Create a view and add the button to it
        view = View()
        view.add_item(clockin_button)

        # Create an embed (make sure to define your embed title)
        embed = discord.Embed(
            color=discord.Color.from_rgb(0, 255, 255)  # Cyan color
        )

        embed.description = (
            "Please click the button below to clock in or out.\n"
            "\n"
            "Don't feel guilty or obligated to be clocked in, you're just helping out when you have time. I appreciate all you do.\n"
            "\n"
            "Thanks,\n"
            "-Kyu"
        )
        await ctx.send(embed=embed, view=view)

    # Early Setup
    @commands.command(name="earlySetup")
    async def earlySetup(self, ctx):
        if not any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        # Create a button with a custom ID
        clockin_button = Button(label="Claim", emoji="✨", style=discord.ButtonStyle.success, custom_id="early")

        # Create a view and add the button to it
        view = View()
        view.add_item(clockin_button)
        await ctx.send(view=view)

    # Manual adding user ids into database
    @commands.command(name="manualAdd")
    async def ManualAdd(self, ctx):
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT user_id FROM users")
            users = cursor.fetchall()
            user_ids = [user[0] for user in users]
            for member in ctx.guild.members:
                if member.id not in user_ids:
                    cursor.execute(f"INSERT INTO users (user_id) VALUES ({member.id})")
            self.conn.commit()
        finally:
            cursor.close()
        await ctx.send("All users added to the database")
        return

async def setup(bot): # this is called by Pycord to setup the cog
    await bot.add_cog(setups(bot, bot.conn)) # add the cog to the bot