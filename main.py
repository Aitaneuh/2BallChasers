import discord
import aiosqlite
import schedule
import asyncio
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from register import *
from match import *
from elo_calculator import *
from bot import *

#-------------------------------------------------------------------------------------------------------------------------

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#-------------------------------------------------------------------------------------------------------------------------

activity = discord.Game(name="Chasing the ball as always.")
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), activity=activity, status=discord.Status.online)

#-------------------------------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():
    # Connexion à la base de données
    bot.db = await aiosqlite.connect('Main.db')

    # Création de la table si elle n'existe pas
    await create_table()

    print("Bot is online ! ", "| Name :", bot.user.name, "| ID :", bot.user.id)
    print("//////////////////////////////////")
    try:
        synced = await bot.tree.sync()
        synced_names = [command.name for command in synced]  # Récupère les noms des commandes synchronisées
        print(f"{len(synced)} commandes ont été synchronisées : {', '.join(synced_names)}")
    except Exception as e:
        print(e)

    run_scheduler()
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

#-------------------------------------------------------------------------------------------------------------------------

@bot.event
async def on_member_join(member):
    # Récupérer le serveur (guild) où le membre a rejoint
    guild = member.guild
    
    # Récupérer le rôle que vous souhaitez attribuer au membre
    role = discord.utils.get(guild.roles, id=1231237281608765594)

    # Vérifier si le rôle existe et si le membre n'a pas déjà ce rôle
    if role is not None and role not in member.roles:
        # Ajouter le rôle au membre
        await member.add_roles(role)

#-------------------------------------------------------------------------------------------------------------------------

# Définissez une tâche planifiée pour poster le leaderboard chaque nuit à minuit
async def scheduled_leaderboard_post():
    await post_leaderboard()

def run_scheduler():
    schedule.every().day.at("00:00").do(lambda: asyncio.run_coroutine_threadsafe(scheduled_leaderboard_post(), bot.loop))


#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="admin_update_leaderboard", description="update the leaderboard")
@commands.has_permissions(administrator=True)
async def admin_update_leaderbord(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        await post_leaderboard()
        embed = discord.Embed(color=0x000000, description="The leaderboard has been updated.")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"{interaction.user.mention}, vous n'êtes pas administrateur.", ephemeral=True)

#-------------------------------------------------------------------------------------------------------------------------

# Votre fonction pour poster le leaderboard
async def post_leaderboard():
    # Ici, vous pouvez appeler la fonction leaderboard() que nous avons créée précédemment
    leaderboard_embed = await leaderboard_elo()

    # Récupérez le canal dans lequel vous souhaitez poster le leaderboard
    channel = bot.get_channel(1231249386122510547)

    # Envoyez le message du leaderboard dans le canal spécifié
    await channel.purge()
    await channel.send(embed=leaderboard_embed)

#-------------------------------------------------------------------------------------------------------------------------

async def leaderboard_elo():
    leaderboard_data = []

    # Récupérer les données des utilisateurs depuis la base de données
    async with aiosqlite.connect('Main.db') as db:
        cursor = await db.execute("SELECT discord_username, elo, wins, losses FROM users WHERE wins + losses != 0 ORDER BY elo DESC LIMIT 10")
        rows = await cursor.fetchall()
        await cursor.close()

        # Parcourir les données récupérées et les stocker dans une liste
        for row in rows:
            username, elo, wins, losses = row
            leaderboard_data.append((username, elo, wins, losses))

    embed = discord.Embed(title="Top 10 ELO Leaderboard", description="This leaderboard is updated every day at midnight.", color=0xff00ff)
    

    # Ajouter les champs dans l'embed
    for rank, (username, elo, wins, losses) in enumerate(leaderboard_data, start=1):
        if (losses == 0 and wins > 0):
            winrate = round(wins / (losses + 1), 5)
            win_per_game = round(wins / (wins + losses), 5)
        elif (losses == 0 and wins == 0):
            winrate = "No game played"
            win_per_game = "No game played"
        else:
            winrate = round(wins / losses, 5)
            win_per_game = round(wins / (wins + losses), 5)
        embed.add_field(name=f"#{rank} - {username}", value=f"ELO: {elo}\nWins: {wins}\nLosses: {losses}\nWinrate: {winrate}\nWin per Game: {win_per_game}", inline=False)

    embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
    
    return embed

#-------------------------------------------------------------------------------------------------------------------------


@bot.tree.command(name="register", description="Register yourself to 2Ballchasers")
@app_commands.describe(epic_username="What's your epic username ?", tracker_link="The link to your Tracker")
async def register(interaction: discord.Interaction, epic_username: str, tracker_link: str):
    guild = interaction.guild
    view = ButtonView(epic_username, tracker_link, guild, interaction.user.id)

    embed = discord.Embed(
    title=f"Thank you {interaction.user.name} for your registration to 2Ballchasers",
    description="Let's see if your informations are correct",
    color=0x000000
    )
    embed.add_field(name="Discord Username (cant be wrong) :", value=f"{interaction.user.name}", inline=False)
    embed.add_field(name="Epic Username :", value=f"{epic_username}", inline=False)
    embed.add_field(name="Link to your tracker :", value=f"{tracker_link}", inline=False)
    embed.add_field(name="Do you confirm that these informations are correct ?", value="use buttons below to Confirm or Cancel", inline=False)
    embed.set_author(name=f"registration of {interaction.user.name}")
    embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
    embed.timestamp = discord.utils.utcnow()
    await interaction.response.send_message(embed=embed, ephemeral=False, view=view)

#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="unregister", description="Unregister yourself from 2Ballchasers")
async def unregister(interaction: discord.Interaction):
    guild = interaction.guild

    # Vérifier si l'utilisateur est inscrit
    async with aiosqlite.connect('Main.db') as db:
        async with db.execute("SELECT 1 FROM users WHERE discord_id = ?", (interaction.user.id,)) as cursor:
            row = await cursor.fetchone()

    if row is None:
        # Si l'utilisateur n'est pas inscrit
        embed = discord.Embed(
            description="You are not registered.",
            color=0xFF0000
        )
        embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Suppression de l'utilisateur de la base de données
    await remove_data(user_id=interaction.user.id)


    # Retirer le rôle de rang de l'utilisateur
    role_names = ["Rank S", "Rank X", "Rank A", "Rank BPLUS", "Rank B", "Rank C", "Rank D", "Rank E", "Rank F", "Rank S (Muted)", "Rank X (Muted)", "Rank A (Muted)", "Rank BPLUS (Muted)", "Rank B (Muted)", "Rank C (Muted)", "Rank D (Muted)", "Rank E (Muted)", "Rank F (Muted)"] 
    roles = [discord.utils.get(guild.roles, name=role_name) for role_name in role_names]
    for role in roles:
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            break  # On suppose que l'utilisateur ne peut avoir qu'un seul rôle de rang

    player_role = guild.get_role(1231237373434531880)
    if player_role in interaction.user.roles:
        await interaction.user.remove_roles(player_role)

    # Création d'un embed pour la réponse
    embed = discord.Embed(
        description="You have been unregistered and your rank role has been removed.",
        color=0x000000
    )

    # Ajout du pied de page avec une icône
    embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")

    # Ajout d'un timestamp
    embed.timestamp = discord.utils.utcnow()

    # Envoi du message en mode éphémère
    await interaction.response.send_message(embed=embed, ephemeral=True)


#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="2bc_mute", description="Mute the ping of a new 1v1 request")
async def mute(interaction: discord.Interaction):
    guild = interaction.guild
    normal_rank_roles = ["Rank S", "Rank X", "Rank A", "Rank BPLUS", "Rank B", "Rank C", "Rank D", "Rank E", "Rank F"]
    user_rank_role = None
    
    for role in interaction.user.roles:
        if role.name in normal_rank_roles:
            user_rank_role = role
            break

    if user_rank_role:
        muted_role_name = f"{user_rank_role.name} (Muted)"
        muted_role = discord.utils.get(guild.roles, name=muted_role_name)
        if muted_role:
            await interaction.user.remove_roles(user_rank_role)
            await interaction.user.add_roles(muted_role)
            embed = discord.Embed(color=0x000000, description=f"Queue notifications are now disactivated.")
            embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"The '{muted_role_name}' role was not found.", ephemeral=True)

    else:
        await interaction.response.send_message("You do not have a rank role.", ephemeral=True)

#-----------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="2bc_unmute", description="Unmute the ping of a new 1v1 request")
async def unmute(interaction: discord.Interaction):
    guild = interaction.guild
    muted_rank_roles = ["Rank S (Muted)", "Rank X (Muted)", "Rank A (Muted)", "Rank BPLUS (Muted)", "Rank B (Muted)", "Rank C (Muted)", "Rank D (Muted)", "Rank E (Muted)", "Rank F (Muted)"]
    user_rank_role = None
    
    for role in interaction.user.roles:
        if role.name in muted_rank_roles:
            user_rank_role = role
            break

    if user_rank_role:
        normal_role_name = user_rank_role.name[:6]
        normal_role = discord.utils.get(guild.roles, name=normal_role_name)
        if normal_role:
            await interaction.user.remove_roles(user_rank_role)
            await interaction.user.add_roles(normal_role)
            embed = discord.Embed(color=0x000000, description=f"Queue notifications are now activated.")
            embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"The '{normal_role_name}' role was not found.", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have a muted rank role.", ephemeral=True)

#-------------------------------------------------------------------------------------------------------------------------

queues_by_rank = {}
current_matches = {}

@bot.tree.command(name="q", description="Enter the queue")
async def q(interaction: discord.Interaction):
    user = interaction.user
    guild = interaction.guild
    channel = interaction.channel

    # Vérifier si l'utilisateur est déjà dans un match
    if user.id in current_matches:
        await interaction.response.send_message(f"{user.name}, you are currently in a match and cannot join a queue.", ephemeral=True)
        return

    # Vérifier si l'utilisateur est déjà dans une file d'attente
    for queue_name, queue_users in queues_by_rank.items():
        if user in queue_users:
            await interaction.response.send_message(f"{user.name}, you are already in the game queue for {queue_name}.", ephemeral=True)
            return

    # Déterminer le nom de la file d'attente en fonction du salon
    if channel.id == 1232780943996092428:
        queue_name = "Rank S"
        queue_id = 1231192753623531661
    elif channel.id == 1231250003448696872:
        queue_name = "Rank X"
        queue_id = 1231192851514396703
    elif channel.id == 1231250140627599390:
        queue_name = "Rank A"
        queue_id = 1231192964881977414
    elif channel.id == 1231250211108687913:
        queue_name = "Rank BPLUS"
        queue_id = 1231194853279531079
    elif channel.id == 1231250401672560730:
        queue_name = "Rank B"
        queue_id = 1231193036352913498
    elif channel.id == 1231250591502827581:
        queue_name = "Rank C"
        queue_id = 1231193165982208070
    elif channel.id == 1231250618774061148:
        queue_name = "Rank D"
        queue_id = 1231193325865009163
    elif channel.id == 1231250642849239060:
        queue_name = "Rank E"
        queue_id = 1231193393414275072
    elif channel.id == 1231250688378540083:
        queue_name = "Rank F"
        queue_id = 1231193462326427668
    elif channel.id == 1231287398395023440:
        queue_name = "Rank All"
        queue_id = None  # Aucun rôle à ping pour "Rank All"
    else:
        await interaction.response.send_message("You are not in a queue channel.", ephemeral=True)
        return
    
    role = discord.utils.get(guild.roles, name=queue_name)
    color = role.color if role else 0x000000 # Couleur par défaut si le rôle n'est pas trouvé

    # Ajouter le joueur à la file d'attente
    if queue_name not in queues_by_rank:
        queues_by_rank[queue_name] = []
    queues_by_rank[queue_name].append(user)

    # Vérifier si la file d'attente contient maintenant deux joueurs
    if len(queues_by_rank[queue_name]) == 2:
        # Envoyer un message de confirmation dans le salon
        embed = discord.Embed(
            title=f"{user.name} has joined the game queue for {queue_name}.",
            description=f"A match will soon be created",
            color=color
        )
        # Ajout d'un timestamp
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
        await interaction.response.send_message(embed=embed)

        # Récupérer les deux joueurs de la file d'attente
        player1, player2 = queues_by_rank[queue_name]

        # Supprimer les joueurs de la file d'attente
        del queues_by_rank[queue_name]

        # Ajouter les joueurs à la liste des matchs en cours
        current_matches[player1.id] = queue_name
        current_matches[player2.id] = queue_name

        # Créer une partie ou un match
        match_rank = queue_name
        channel = guild.get_channel(channel.id)
        match_id = await create_match(guild, channel, player1, player2, match_rank)
        matches[match_id] = Match(match_id, player1, player2, match_rank)

    else:
        # Envoyer un message de confirmation dans le salon
        embed = discord.Embed(
            title=f"{user.name} has joined the game queue for {queue_name}.",
            description=f"Type /queue to challenge him in a 2Ballchaser",
            color=color
        )
        # Ajout d'un timestamp
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
        if queue_id:
            role = guild.get_role(queue_id)
            await interaction.response.send_message(content=role.mention, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        else:
            await interaction.response.send_message(embed=embed)

#-------------------------------------------------------------------------------------------------------------------------


@bot.tree.command(name="q_leave", description="Leave the queue")
async def q_leave(interaction: discord.Interaction):
    user = interaction.user
    guild = interaction.guild
    channel = interaction.channel
    

    # Déterminer le nom de la file d'attente en fonction du salon
    if channel.id == 1232780943996092428:
        queue_name = "Rank S"
    elif channel.id == 1231250003448696872:
        queue_name = "Rank X"
    elif channel.id == 1231250140627599390:
        queue_name = "Rank A"
    elif channel.id == 1231250211108687913:
        queue_name = "Rank BPLUS"
    elif channel.id == 1231250401672560730:
        queue_name = "Rank B"
    elif channel.id == 1231250591502827581:
        queue_name = "Rank C"
    elif channel.id == 1231250618774061148:
        queue_name = "Rank D"
    elif channel.id == 1231250642849239060:
        queue_name = "Rank E"
    elif channel.id == 1231250688378540083:
        queue_name = "Rank F"
    elif channel.id == 1231287398395023440:
        queue_name = "Rank All"
    else:
        await interaction.response.send_message("You are not in a queue channel.", ephemeral=True)
        return
    
    role = discord.utils.get(guild.roles, name=queue_name)
    color = role.color if role else 0x000000 # Couleur par défaut si le rôle n'est pas trouvé

    # Vérifier si le joueur est dans la file d'attente
    if user in queues_by_rank.get(queue_name, []):
        queues_by_rank[queue_name].remove(user)
        embed = discord.Embed(
            title=f"{user.name} has left the game queue for {queue_name}.",
            description=f"Type /queue to take his place in the 2Ballchaser {queue_name} queue.",
            color=color
        )
        # Ajout d'un timestamp
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"{user.name}, you are not in the game queue for {queue_name}.")


#-------------------------------------------------------------------------------------------------------------------------

class ButtonView(discord.ui.View):
    def __init__(self, epic_username, tracker_link, guild, author_id):
        super().__init__()
        self.guild = guild
        self.epic_username = epic_username
        self.tracker_link = tracker_link
        self.author_id = author_id
        self.add_buttons()


    async def btnConfirm(self, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            await register_people(self.epic_username, self.tracker_link, self.guild, interaction)
            await interaction.message.delete()
        else:
            await interaction.response.send_message("You are not authorized to confirm this registration.", ephemeral=True)


    async def btnCancel(self, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            await interaction.response.send_message("You Cancelled your registration.", ephemeral=True, delete_after=5)
            await interaction.message.delete()
        else:
            await interaction.response.send_message("You are not authorized to cancel this registration.", ephemeral=True)

    def add_buttons(self):
        confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green, custom_id="btnConfirm")
        confirm_button.callback = self.btnConfirm
        
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="btnCancel")
        cancel_button.callback = self.btnCancel

        self.add_item(confirm_button)
        self.add_item(cancel_button)

#-------------------------------------------------------------------------------------------------------------------------

# Créer une classe pour représenter un match
class Match:
    def __init__(self, match_id, player1, player2, match_rank):
        self.match_id = match_id
        self.match_rank = match_rank
        self.player1 = player1
        self.player2 = player2

# Créer un dictionnaire pour stocker les matchs
matches = {}

#-------------------------------------------------------------------------------------------------------------------------


@bot.tree.command(name="report", description="Report the result of a match")
@app_commands.describe(match_id="id of the match", result="win or loss")
async def report(interaction: discord.Interaction, match_id: int, result: str):
    user = interaction.user
    guild = interaction.guild
    channel = bot.get_channel(1231572432234745876)

    # Vérifier si le résultat est valide (par exemple, "win" ou "loss")
    valid_results = ["win", "loss"]
    if result.lower() not in valid_results:
        await interaction.response.send_message("Invalid result. Please use 'win' or 'loss'.", ephemeral=True)
        return

    # Vérifier si le match existe dans la liste des matchs
    match = matches.get(match_id)
    if not match:
        await interaction.response.send_message("Match not found. Please enter a valid match ID.", ephemeral=True)
        return
    
    # Vérifier si le joueur est l'un des deux joueurs du match
    if user.id != match.player1.id and user.id != match.player2.id:
        await interaction.response.send_message("Error: You are not one of the players in this match.", ephemeral=True)
        return

    # Déterminer le joueur gagnant et perdant en fonction de celui qui rapporte le score
    if result == 'win':
        if user.id == match.player1.id:
            winner_id = match.player1.id
            loser_id = match.player2.id
        else:
            winner_id = match.player2.id
            loser_id = match.player1.id
    elif result == 'loss':
        if user.id == match.player1.id:
            winner_id = match.player2.id
            loser_id = match.player1.id
        else:
            winner_id = match.player1.id
            loser_id = match.player2.id

    # Récupérer les Elo des deux joueurs
    elo_winner = await get_elo(winner_id)
    elo_loser = await get_elo(loser_id)

    # Calculer le changement d'Elo pour les deux joueurs en fonction du résultat
    if result.lower() == "win":
        delta_elo_winner, delta_elo_loser = await calculate_elo_change(elo_winner, elo_loser, 'win')
    elif result.lower() == "loss":
        delta_elo_loser, delta_elo_winner = await calculate_elo_change(elo_winner, elo_loser, 'loss')

    if (match.match_rank != "Rank All"):
        await update_elo(winner_id, delta_elo_winner)
        await update_elo(loser_id, delta_elo_loser)
        await update_player_role(winner_id, elo_winner + delta_elo_winner)
        await update_player_role(loser_id, elo_loser + delta_elo_loser)
        # Ajouter une victoire au joueur gagnant et une défaite au joueur perdant
        await add_win(winner_id)
        await add_loss(loser_id)

    
    del current_matches[match.player1.id]
    del current_matches[match.player2.id]
    matches.pop(match_id)

    embed = discord.Embed(color=0x000000, description=f"Match {match_id} succesfully reported.")
    embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
    embed.timestamp = discord.utils.utcnow()
    await interaction.response.send_message(embed=embed)

    # Envoyer un message en MP aux deux joueurs du match avec les détails du rapport de match
    player1 = guild.get_member(match.player1.id)
    player2 = guild.get_member(match.player2.id)
    if player1 and player2:
        embed = discord.Embed(
            title="Match Result Reported",
            description=f"Match ID: {match_id}\nReported by: {user.name}\nResult (from {user.name}'s POV): {result.capitalize()}",
            color=0x000000
        )
        embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)
        await player1.send(embed=embed)
        await player2.send(embed=embed)

    else:
        await interaction.response.send_message("Error: One or both players are not found in the server.", ephemeral=True)


#-------------------------------------------------------------------------------------------------------------------------

async def update_player_role(user_id, new_elo):
    try:
        guild = bot.get_guild(1231191798081261650)
        if guild is None:
            raise ValueError("Guild not found.")

        member = guild.get_member(user_id)
        if member is None:
            raise ValueError("User not found.")

        new_role_id = await update_role(member, new_elo)
        if new_role_id is None:
            raise ValueError("New role ID not found.")

        current_roles = member.roles

        # List of rank role IDs
        rank_role_ids = [
            1231192753623531661, 1231288586746204171, 1231192851514396703, 
            1231288701217407016, 1231192964881977414, 1231288778367176744, 
            1231194853279531079, 1231288840304463872, 1231193036352913498, 
            1231288912165474384, 1231193165982208070, 1231288970516758559, 
            1231193325865009163, 1231289036937760930, 1231193393414275072, 
            1231289085583298680, 1231193462326427668, 1231289178617151579
        ]

        # Find the old rank role
        old_rank_role = next((role for role in current_roles if role.id in rank_role_ids), None)

        if old_rank_role:
            # Remove the old rank role
            await member.remove_roles(old_rank_role)

        # Add the new rank role
        new_role = guild.get_role(new_role_id)
        if new_role:
            await member.add_roles(new_role)
        else:
            raise ValueError("New role not found.")
            
    except Exception as e:
        # Handle errors
        print(f"An error occurred: {e}")


#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="stats", description="Display your statistics")
async def stats_command(interaction: discord.Interaction):
    user = interaction.user
    
    # Récupérer les données de l'utilisateur à partir de la base de données
    user_data = await get_data(user.id)
    
    if user_data:
        # Extraire les données de l'utilisateur
        username = user_data[1]
        elo = user_data[3]
        wins = user_data[4]
        losses = user_data[5]
        tracker_link = user_data[6]

        # Créer un embed pour afficher les statistiques de l'utilisateur
        embed = discord.Embed(
            title=f"Statistics for {username}",
            color=discord.Color.dark_embed()
        )
        embed.add_field(name="Elo", value=elo, inline=True)
        embed.add_field(name="Wins", value=wins, inline=True)
        embed.add_field(name="Losses", value=losses, inline=True)
        if (losses == 0 and wins > 0):
            embed.add_field(name="Winrate", value=round(wins / (losses + 1), 5), inline=False)
            embed.add_field(name="Win per Game", value=round(wins / (wins + losses), 5), inline=False)
        elif (losses == 0 and wins == 0):
            embed.add_field(name="Winrate", value="No game played", inline=False)
            embed.add_field(name="Win per Game", value="No game played", inline=False)
        else:
            embed.add_field(name="Winrate", value=round(wins / losses, 5), inline=False)
            embed.add_field(name="Win per Game", value=round(wins / (wins + losses), 5), inline=False)
        
        embed.add_field(name="Tracker Link", value=tracker_link, inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")

        # Envoyer l'embed en réponse à la commande
        await interaction.response.send_message(embed=embed)
    else:
        # Si aucune donnée n'est trouvée pour l'utilisateur
        await interaction.response.send_message("No statistics found for this user.", ephemeral=True)

#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="admin_stats", description="Display your statistics")
@commands.has_permissions(administrator=True)
@app_commands.describe(user_id="ID of the player you want to see stats.")
async def stats_command(interaction: discord.Interaction, user_id: str):
    
    if interaction.user.guild_permissions.administrator:
        # Récupérer les données de l'utilisateur à partir de la base de données
        user_data = await get_data(user_id)
        
        if user_data:
            # Extraire les données de l'utilisateur
            username = user_data[1]
            elo = user_data[3]
            wins = user_data[4]
            losses = user_data[5]
            tracker_link = user_data[6]

            # Créer un embed pour afficher les statistiques de l'utilisateur
            embed = discord.Embed(
                title=f"Statistics for {username}",
                color=discord.Color.dark_embed()
            )
            embed.add_field(name="Elo", value=elo, inline=True)
            embed.add_field(name="Wins", value=wins, inline=True)
            embed.add_field(name="Losses", value=losses, inline=True)
            if (losses == 0 and wins > 0):
                embed.add_field(name="Winrate", value=round(wins / (losses + 1), 5), inline=False)
                embed.add_field(name="Win per Game", value=round(wins / (wins + losses), 5), inline=False)
            elif (losses == 0 and wins == 0):
                embed.add_field(name="Winrate", value="No game played", inline=False)
                embed.add_field(name="Win per Game", value="No game played", inline=False)
            else:
                embed.add_field(name="Winrate", value=round(wins / losses, 5), inline=False)
                embed.add_field(name="Win per Game", value=round(wins / (wins + losses), 5), inline=False)
            
            embed.add_field(name="Tracker Link", value=tracker_link, inline=False)
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")

            # Envoyer l'embed en réponse à la commande
            await interaction.response.send_message(embed=embed)
        else:
            # Si aucune donnée n'est trouvée pour l'utilisateur
            await interaction.response.send_message("No statistics found for this user.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{interaction.user.mention}, vous n'êtes pas administrateur.", ephemeral=True)

#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="admin_clear", description="clear a channel")
@commands.has_permissions(administrator=True)
async def admin_clear(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        channel = interaction.channel
        await channel.purge()
    else:
        await interaction.response.send_message(f"{interaction.user.mention}, vous n'êtes pas administrateur.", ephemeral=True)

#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="admin_set_elo", description="Set a ELO for a user")
@commands.has_permissions(administrator=True)
@app_commands.describe(user_id="ID of the player you want to change ELO.", new_elo="Value of the new ELO.")
async def admin_set_elo(interaction: discord.Interaction, user_id: str, new_elo: str):
    if interaction.user.guild_permissions.administrator:
        try:
            # Convert user_id and new_elo to integers
            user_id = int(user_id)
            new_elo = int(new_elo)
            
            # Change the user's Elo in the database
            await change_elo(user_id, new_elo)
            
            # Update the user's role based on the new Elo
            await update_player_role(user_id, new_elo)
            
            # Send a confirmation message
            embed = discord.Embed(color=0x000000, description=f"Player `{user_id}` ELO has been changed to {new_elo}.")
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
            await interaction.response.send_message(embed=embed)
        except ValueError:
            # Handle type conversion errors
            await interaction.response.send_message("Invalid user ID or Elo. Please enter valid integers.")
        except Exception as e:
            # Handle other errors
            await interaction.response.send_message(f"An error occurred: {e}")
    else:
        # Inform the user that they are not an administrator
        await interaction.response.send_message(f"{interaction.user.mention}, you do not have administrator permissions.", ephemeral=True)

#-------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="admin_report", description="Report the result of a match as an admin")
@commands.has_permissions(administrator=True)
@app_commands.describe(match_id="ID of the match", winner_id="ID of the winning player", loser_id="ID of the losing player", issue="Description of the issue (optional)")
async def admin_report(interaction: discord.Interaction, match_id: int, winner_id: int, loser_id: int, issue: str = None):
    user = interaction.user
    guild = interaction.guild
    channel = bot.get_channel(1231572432234745876)

    # Verify if the match exists in the list of matches
    match = matches.get(match_id)
    if not match:
        await interaction.response.send_message("Match not found. Please enter a valid match ID.", ephemeral=True)
        return
    
    # Verify if the provided player IDs are part of the match
    if winner_id not in [match.player1.id, match.player2.id] or loser_id not in [match.player1.id, match.player2.id]:
        await interaction.response.send_message("Error: The specified players are not part of this match.", ephemeral=True)
        return

    # Fetch ELO ratings for both players
    elo_winner = await get_elo(winner_id)
    elo_loser = await get_elo(loser_id)

    # Calculate the change in ELO for both players based on the result
    delta_elo_winner, delta_elo_loser = await calculate_elo_change(elo_winner, elo_loser, 'win')

    # Update ELO and roles if applicable
    await update_elo(winner_id, elo_winner + delta_elo_winner)
    await update_elo(loser_id, elo_loser + delta_elo_loser)
    await update_player_role(winner_id, elo_winner + delta_elo_winner)
    await update_player_role(loser_id, elo_loser + delta_elo_loser)

    # Add win to the winner and loss to the loser
    await add_win(winner_id)
    await add_loss(loser_id)

    # Remove the match from the matches list
    if (match.match_rank != "Rank All"):
        await update_elo(winner_id, delta_elo_winner)
        await update_elo(loser_id, delta_elo_loser)
        await update_player_role(winner_id, elo_winner + delta_elo_winner)
        await update_player_role(loser_id, elo_loser + delta_elo_loser)
        # Ajouter une victoire au joueur gagnant et une défaite au joueur perdant
        await add_win(winner_id)
        await add_loss(loser_id)

    
    del current_matches[match.player1.id]
    del current_matches[match.player2.id]
    matches.pop(match_id)

    # Send confirmation message
    embed = discord.Embed(color=0x000000, description=f"Match {match_id} successfully reported by admin.")
    if issue:
        embed.add_field(name="Reported Issue", value=issue, inline=False)
    embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
    embed.timestamp = discord.utils.utcnow()
    await interaction.response.send_message(embed=embed)

    # Notify both players and the reporting channel
    player1 = guild.get_member(match.player1.id)
    player2 = guild.get_member(match.player2.id)
    if player1 and player2:
        embed = discord.Embed(
            title="Match Result Reported by Admin",
            description=f"Match ID: {match_id}\nReported by Admin: {user.name}\nWinner: <@{winner_id}>\nLoser: <@{loser_id}>",
            color=0x000000
        )
        if issue:
            embed.add_field(name="Reported Issue", value=issue, inline=False)
        embed.set_footer(text="Powered By 2Ballchasers", icon_url="https://i.imgur.com/Qnltn2h.png")
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)
        await player1.send(embed=embed)
        await player2.send(embed=embed)
    else:
        await interaction.response.send_message("Error: One or both players are not found in the server.", ephemeral=True)

#-------------------------------------------------------------------------------------------------------------------------

# initialition du token
bot.run(TOKEN)
