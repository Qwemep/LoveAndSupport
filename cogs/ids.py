import os
import sys
import os

# Add the directory containing config.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import script_dir 

# Kyu
KYU_ID = 337118361009782786
GUILD_ID = 1263288275616137236

# Role IDs
ADMIN_ROLE_ID = 1263336075926175776
MOD_ROLE_ID = 1263342078512070731
MUTED_ROLE_ID = 1269570590306599045
LOVED_ROLE_ID = 1263364087518335057
UNLOVED_ROLE_ID = 1271640348942401608
STAFFPING_ROLE_ID = 1270544407308800164
BIRTHDAY_BEAN_ID = 1263367711497388104
EARLY_ID = 1271991550762680420
DIVIDER0_ID = 1263403425723449365
DIVIDER1_ID = 1263403288783622208
DIVIDER0_NOPERM_ID = 1273455875759017984
LOTTERY_ID = 1273840977215225988
BUMP_ID = 1312575150104903772
SWEETHEART_ID = 1327516545114443787
BUMP_STAR_ID = 1329277021942976562

# Category and Channel IDs
PM_CATEGORY_ID = 1270598657976041503
TICKET_CATEGORY_ID = 1263450334706274325
ADMIN_CATEGORY_ID = 1271336217514086450
TRANSCRIPTS_ID = 1263451078461227120
ADULT_STRUGGLES_ID = 1263318469710053466
THE_VOID_ID = 1263293195874205696
STARBOARD_ID = 1263294444497797185
CHAT_LOG_ID = 1263361828004565032
MOD_CHAT_ID = 1263290446835093585
COUNT_ID = 1271961932257038376
GENERAL_ID = 1263290021058842624
ANONYMOUS_ID = 1273091098637631572
COMMANDS_ID = 1263350833895182441
INTRODUCTIONS_ID = 1263290765195612170
UNO_ONE_ID = 1279661746289639435
UNO_TWO_ID = 1279661897393766421
WELCOME_ID = 1312567399119065129
BUMP_CHANNEL_ID = 1263297306552434709
ADMIN_MOD_LOGS = 1263383265025327125
QOTD_ID = 1266389395129499730
FEMALE_ID = 1277795989104754800


# Progression Roles ID
WATER_ID = 1263330553365790865
MILK_ID = 1263325566640197654
ICED_ID = 1268714491705561225
HERBAL_ID = 1263327273646424095
WHITE_ID = 1263326945299398789
GREEN_ID = 1263327335176867881
OOLONG_ID = 1263327395226583050
EARL_ID = 1263327458820882585
ENGLISH_ID = 1263327491578396814
PUERH_ID = 1263327522414788652
YERBA_ID = 1263328195751710731
MOCHA_ID = 1263329047778295859

# Vanity Roles IDs
vanityRoles = {
    "Outgoing Friend": [1263553800610910229, 5000],
    "Warm Friend": [1263553455457304669, 5000],
    "Trusted Friend": [1263552924345303040, 5000],

    "Mother": [1263554180803592192, 10000],
    "Father": [1263554278740725801, 10000],
    "Parent": [1263554654906613831, 10000],

    "Goth King": [1290756134226890874, 20000],
    "Goth Queen": [1290755931323371601, 20000],
    "Goth Icon": [1290756337596235858, 20000],

    "Dumbass": [1327869580240228353, 25000],
    "Smartass": [1327869425579327528, 25000],
    "Lurker": [1317976939327258624, 25000],
    "Furry": [1317977099100885062, 25000],
    "Magical Fairy": [1317230383598931979, 25000],
    "Necromancer": [1327868322473316404, 2500],

    "Just Baby": [1263554339826303106, 30000],
}


# Achievements
ACHIEVEMENT_PATH = os.path.join(script_dir, 'Achievements')
EGGS_PATH = os.path.join(script_dir, 'eggs')
IMAGES_PATH = os.path.join(script_dir, 'images')
UNO_PATH = os.path.join(script_dir, 'uno')

ROLE_IMAGES = {
    MILK_ID: 'milk.png', 
    ICED_ID: 'iced.png',
    HERBAL_ID: 'herbal.png',
    WHITE_ID: 'white.png',
    GREEN_ID: 'green.png',
    OOLONG_ID: 'oolong.png',
    EARL_ID: 'earl.png',
    ENGLISH_ID: 'english.png',
    PUERH_ID: 'puerh.png',
    YERBA_ID: 'yerba.png',
    MOCHA_ID: 'mocha.png',
}



