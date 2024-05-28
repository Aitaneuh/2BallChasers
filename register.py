import discord
from discord.ext import commands
from discord import app_commands
from bot import *
import requests
from datetime import datetime

#-------------------------------------------------------------------------------------------------------------------------

# Utilisation de la méthode now() pour obtenir le temps actuel
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#-------------------------------------------------------------------------------------------------------------------------

async def get_player_mmr(epic_username):
    
    url = f"https://api.tracker.gg/v2/rocket-league/standard/profile/epic/{epic_username}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if response.status_code == 200 and 'data' in data:
            #Accédez aux données du mode de jeu 1v1
            mmr_1v1 = data['stats']['rating']['value']
            return mmr_1v1
        else:
            print("Erreur lors de la récupération des données.")
            return None
    else:
        print("Erreur lors de la requête :", response.status_code)

#-------------------------------------------------------------------------------------------------------------------------

async def register_people(epic_username, tracker_link, guild, interaction):
    role = None
    elo = None
    member = interaction.user
    # mmr_1v1 = await get_player_mmr(epic_username)
    mmr_1v1 = 1115 # like if you were Champ 3 in 1s
    if mmr_1v1 is not None:
        if mmr_1v1 >= 1651:
            role = discord.utils.get(guild.roles, id=1231192753623531661) # Rank S top 50 world
            elo = 2500
        elif 1550 <= mmr_1v1 < 1651:
            role = discord.utils.get(guild.roles, id=1231192851514396703) # Rank X top 200 world
            elo = 2300
        elif 1450 <= mmr_1v1 < 1550:
            role = discord.utils.get(guild.roles, id=1231192964881977414) # Rank A top 1000 world
            elo = 2100
        elif 1350 <= mmr_1v1 < 1450:
            role = discord.utils.get(guild.roles, id=1231194853279531079) # Rank B+ SSL
            elo = 1900
        elif 1220 <= mmr_1v1 < 1350:
            role = discord.utils.get(guild.roles, id=1231193036352913498) # Rank B GC3 and GC2
            elo = 1700
        elif 1115 <= mmr_1v1 < 1220:
            role = discord.utils.get(guild.roles, id=1231193165982208070) # Rank C GC1 and Champ 3
            elo = 1500
        elif 995 <= mmr_1v1 < 1115:
            role = discord.utils.get(guild.roles, id=1231193325865009163) # Rank D Champ 2 and Champ 1
            elo = 1300
        elif 815 <= mmr_1v1 < 950:
            role = discord.utils.get(guild.roles, id=1231193393414275072) # Rank E Diamonds
            elo = 1100
        elif mmr_1v1 < 815:
            role = discord.utils.get(guild.roles, id=1231193462326427668) # Rank F Below Diamonds
            elo = 900
    else:
        await interaction.response.send_message(f"Failed to get your 1v1 mmr. Please try again later.", ephemeral=True)

    player_role = discord.utils.get(guild.roles, id=1231237373434531880) # Player Role

    if role is not None:
        await member.add_roles(role)
        await member.add_roles(player_role)
        embed = discord.Embed(
            title="Registration Confirmation",
            description=f"Thank you {member.mention} for your registration to 2Ballchasers !",
            color=0x00ff00
        )
        embed.add_field(name="Discord Username", value=f"{member.name} ({member.id})", inline=False)
        embed.add_field(name="Epic Username", value=epic_username, inline=False)
        embed.add_field(name="Link to your tracker", value=tracker_link, inline=False)
        embed.add_field(name="Rank", value=role.name, inline=False)
        # Ajout d'un timestamp
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Powered By 2Ballchasers")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await insert_data(member.id, member.name, epic_username, elo, 0, 0, tracker_link)

#-------------------------------------------------------------------------------------------------------------------------

    # Envoi du message dans un canal spécifique
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel) and channel.id == 1231249240865509376:
            embed = discord.Embed(
            title="Registration Confirmation",
            description=f"New Registration of {member.mention} !",
            color=0xffffff
            )
            embed.add_field(name="Discord Username", value=f"{member.name} ({member.id})", inline=False)
            embed.add_field(name="Epic Username", value=epic_username, inline=False)
            embed.add_field(name="Link to his tracker", value=tracker_link, inline=False)
            embed.add_field(name="Rank", value=role.name, inline=False)
            # Ajout d'un timestamp
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="Powered By 2Ballchasers")
            await channel.send(embed=embed)
            return
        
#-------------------------------------------------------------------------------------------------------------------------