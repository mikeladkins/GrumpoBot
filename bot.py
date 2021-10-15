import discord
from discord.ext import commands
from character import Character
import requests
import json
import time
import datetime
import logging
import keys

token = keys.token
retail_v1_base_url = 'https://www.warcraftlogs.com:443/v1/'
ffl_v1_base_url = 'https://www.fflogs.com:443/v1/'
base_report_url = 'https://www.warcraftlogs.com/reports/'
default_error_message = 'Something went wrong, check arguments and try again or contact Grumpo.'

logger = logging.getLogger('Discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

chars = {}

client = commands.Bot(command_prefix = '!')



def get_character_parse_for_zone_id(game, characterName, server, region, zoneId):
    print(game)
    if game == "ff" :
        response = requests.get(
            ffl_v1_base_url + 
            characterName + '/' + server + '/' + region + '/' + '?zone=' + zoneId +
            '&api_key=' + keys.ffl_v1_key)
    elif game == "retail" :
        requestUrl = retail_v1_base_url + 'parses/character/' +characterName + '/' + server + '/' + region + '/' + '?zone=' + zoneId +'&api_key=' + keys.retail_v1_key
        response = requests.get(requestUrl)
    json_data = json.loads(response.text)
    return json_data


def get_most_recent_report_for_guild(guildName, server, region):
    response = requests.get(
        'https://www.warcraftlogs.com:443/v1/reports/guild/' + guildName +
        '/' + server + '/' + region + '?api_key=' + keys.wcl_v1_key)
    json_data = json.loads(response.text)
    return json_data


def get_reports_for_guild_by_date(guildName, server, region, startDate):
    timeone = datetime.datetime.strptime(startDate, "%m/%d/%Y")
    modDate = time.mktime(timeone.timetuple())
    timestamp = modDate * 1000
    print(timestamp)
    response = requests.get(
        'https://www.warcraftlogs.com:443/v1/reports/guild/' + guildName +
        '/' + server + '/' + region + '?start=' + str(timestamp) +
        '&api_key=' + keys.wcl_v1_key)
    return json.loads(response.text)

def add_character(user, name, server, region):
    chars[user] = Character(name, server, region)
    print(chars)
    pass

@client.command()
async def addCharacter(ctx, name, server, region):
    logger.info("Adding character")
    add_character(ctx.author, name, server, region)
    pass

@client.command()
async def whisper(ctx):
    print("attempting to whisper")
    member = ctx.author
    await member.send("whisper")

@client.event
async def on_ready():
    print('Ready to use, logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    await client.process_commands(message)
    if message.author == client.user:
        return

    msg = message.content

    if (msg.startswith('!recent-report-for-guild')):
        split_message = msg.split(' ', 4)
        try:
            guild = split_message[1]
            server = split_message[2]
            region = split_message[3]
            await message.channel.send('Getting most recent report for ' +
                                       guild + '...')
            responseJson = get_most_recent_report_for_guild(
                guild, server, region)
            reportId = responseJson[0]['id']
            output = base_report_url + reportId
            await message.channel.send(output)
        except Exception as e:
            print('Error in Recent Report For Guild:\n' + str(e) + '\n')
            await message.channel.send(default_error_message)

    if msg.startswith('!report-for-guild-by-date'):
        split_message = msg.split(' ', 4)
        try:
            guild = split_message[1]
            server = split_message[2]
            region = split_message[3]
            dateString = split_message[4]
            await message.channel.send('Getting report for ' + guild + ' on ' +
                                       dateString + '...')
            reportsJson = get_reports_for_guild_by_date(
                guild, server, region, dateString)
            reportId = reportsJson[-1]['id']
            if reportId is None:
                output = 'Could not load logs, check arguments and try again.'
            else:
                output = base_report_url + reportId
                await message.channel.send(output)
        except Exception as e:
            print('Error in Reports for guild by date!\n' + str(e) + '\n')
            await message.channel.send(default_error_message)

    if msg.startswith('!grumpo-is-cool'):
        await message.add_reaction('👍')

    if msg.startswith('!most-recent-parse-for-character'):
        splitMessage = msg.split(' ', 5)
        try:
            game = splitMessage[1]
            character = splitMessage[2]
            server = splitMessage[3]
            region = splitMessage[4]
            zoneId = str(28)  #Default to most recent raid, i.e. Sanctum of Domination
            stringLength = len(splitMessage)
            if stringLength == 6:
                zoneId = splitMessage[5]
            await message.channel.send('Getting most recent parse for ' +
                                       character + ' in zone id: ' + zoneId +
                                       '...')
            report_json = get_character_parse_for_zone_id(
                game, character, server, region, zoneId)
            parse = report_json[0]
            output = 'Character: ' + parse[
                'characterName'] + '\nClass: ' + parse[
                    'class'] + '\nSpec: ' + parse['spec'] + '\nBoss: ' + parse[
                        'encounterName'] + '\nPercentile: ' + str(
                            parse['percentile']) + '\nRank: ' + str(
                                parse['rank']) + ' out of ' + str(
                                    parse['outOf'])
            await message.channel.send(output)
        except Exception as e:
            logger.error("Error in most recent parse for character:", e)
            print('Error in Most Recent Parse for Character!\n' + str(e) +
                  '\n')
            await message.channel.send(default_error_message)

#keep_alive()
client.run(token)