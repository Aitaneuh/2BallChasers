import random
import string
import discord
import aiosqlite
from discord.ext import commands
from discord import app_commands

from bot import get_elo

match_counter = 0  # Compteur global pour les ID de match

async def create_match(guild, channel, player1, player2, match_rank):
    global match_counter  # Utilisation du compteur global

    player1_elo = await get_elo(player1.id)
    player2_elo = await get_elo(player2.id)


    # Incrémentation du compteur pour obtenir un ID unique pour le match
    match_counter += 1
    match_id = match_counter

    # Formater le Match Name
    if match_rank != "Rank All":
        match_name = match_rank.lower()[5:] + str(match_id)
        if (len(match_name) < 3):
            match_name = match_name + "x"
    else:
        match_name = match_rank.lower()[5:] + str(match_id)


    # Générer un mot de passe aléatoire de 4 caractères (lettres ou chiffres)
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
    password = password.lower()

    # Sélection aléatoire de l'hôte du match
    host = random.choice([player1, player2])

    role = discord.utils.get(guild.roles, name=match_name)
    color = role.color if role else 0x000000 # Couleur par défaut si le rôle n'est pas trouvé

    # Envoi d'un message dans le canal approprié avec les détails du match
    embed = discord.Embed(
            title=f"A new {match_rank} match has been created !",
            description=f"you can create a new 2Ballchaser by typing /queue",
            color=color
        )
        # Ajout d'un timestamp
    embed.timestamp = discord.utils.utcnow()
    embed.add_field(name="Match ID :", value=f"{match_id}", inline=False)
    embed.add_field(name="Players :",value=f"{player1.name} | {player1_elo} ELO vs {player2.name} | {player2_elo} ELO", inline=False)
    embed.add_field(name="Host :",value=host.name, inline=False)
    embed.set_footer(text="Powered By 2Ballchasers")
    await channel.send(embed=embed)

    # Envoi d'un message privé à chaque joueur avec les informations du match
    embed = discord.Embed(
            title="Match Found !",
            description="join the match with the following information",
            color=color
        )
        # Ajout d'un timestamp
    embed.timestamp = discord.utils.utcnow()
    embed.add_field(name="Match Best Of :", value="Best Of 5", inline=False)
    embed.add_field(name="Match Mutators :", value="None", inline=False)
    embed.add_field(name="Match Map :", value="Any standard map you want", inline=False)
    embed.add_field(name="Match ID :", value=f"{match_id}", inline=False)
    embed.add_field(name="Players :",value=f"{player1.name} | {player1_elo} ELO vs {player2.name} | {player2_elo} ELO", inline=False)
    embed.add_field(name="Host :", value=f"{host.name}", inline=False)
    embed.add_field(name="Match Name :", value=f"{match_name}", inline=False)
    embed.add_field(name="Match Password :", value=f"{password}", inline=False)
    embed.set_footer(text="Powered By 2Ballchasers")
    match_info = embed
    await player1.send(embed=match_info)
    await player2.send(embed=match_info)

    # Retourner l'ID du match pour référence ultérieure
    return match_id
