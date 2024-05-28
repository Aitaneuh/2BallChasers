from typing import Tuple
import discord
from discord.ext import commands

async def calculate_elo_change(elo_winner: int, elo_loser: int, result: str) -> Tuple[int, int]:
    # Calculer la probabilité de victoire pour chaque joueur
    expected_score_winner = 1 / (1 + 10 ** ((elo_loser - elo_winner) / 200))
    expected_score_loser = 1 - expected_score_winner

    # Déterminer le résultat du match
    if result.lower() == "win":
        # Si le joueur 1 a gagné
        actual_score_player1 = 1
        actual_score_player2 = 0
    elif result.lower() == "loss":
        # Si le joueur 1 a perdu
        actual_score_player1 = 0
        actual_score_player2 = 1
    else:
        # Gestion d'une éventualité d'erreur
        raise ValueError("Invalid result. Must be 'win' or 'loss'.")

    # Calculer le changement d'Elo pour chaque joueur
    k_factor = 30  # Facteur K pour ajuster la vitesse de changement d'Elo
    delta_elo_player1 = int(round(k_factor * (actual_score_player1 - expected_score_winner)))
    delta_elo_player2 = int(round(k_factor * (actual_score_player2 - expected_score_loser)))

    return delta_elo_player1, delta_elo_player2

#-------------------------------------------------------------------------------------------------------------------------

muted_rank_roles = ["Rank S (Muted)", "Rank X (Muted)", "Rank A (Muted)", "Rank BPLUS (Muted)", "Rank B (Muted)", "Rank C (Muted)", "Rank D (Muted)", "Rank E (Muted)", "Rank F (Muted)"]
muted = False

async def update_role(user: discord.Member, elo: int):

    for role in user.roles:
        if role.name in muted_rank_roles:
            muted = True
            break

    if elo >= 2400:
        if muted:
            new_id_role = 1231288586746204171
        else:
            new_id_role = 1231192753623531661
        return new_id_role    # Rank S top 50 world

    elif 2200 <= elo < 2400:
        if muted:
            new_id_role = 1231288701217407016
        else:
            new_id_role = 1231192851514396703
        return new_id_role     # Rank X top 200 world

    elif 2000 <= elo < 2200:
        if muted:
            new_id_role = 1231288778367176744
        else:
            new_id_role = 1231192964881977414
        return new_id_role   # Rank A top 1000 world

    elif 1800 <= elo < 2000:
        if muted:
            new_id_role = 1231288840304463872
        else:
            new_id_role = 1231194853279531079
        return new_id_role     # Rank B+ SSL

    elif 1600 <= elo < 1800:
        if muted:
            new_id_role = 1231288912165474384
        else:
            new_id_role = 1231193036352913498
        return new_id_role     # Rank B GC3 and GC2

    elif 1400 <= elo < 1600:
        if muted:
            new_id_role = 1231288970516758559
        else:
            new_id_role = 1231193165982208070
        return new_id_role     # Rank C GC1 and Champ 3

    elif 1200 <= elo < 1400:
        if muted:
            new_id_role = 1231289036937760930
        else:
            new_id_role = 1231193325865009163
        return new_id_role     # Rank D Champ 2 and Champ 1
 
    elif 1000 <= elo < 1200:
        if muted:
            new_id_role = 1231289085583298680
        else:
            new_id_role = 1231193393414275072
        return new_id_role     # Rank E Diamonds

    elif elo < 1000:
        if muted:
            new_id_role = 1231289178617151579
        else:
            new_id_role = 1231193462326427668
        return new_id_role     # Rank F Below Diamonds