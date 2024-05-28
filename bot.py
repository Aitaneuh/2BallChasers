import aiosqlite

#-------------------------------------------------------------------------------------------------------------------------

# Fonction pour créer une table dans la base de données si elle n'existe pas déjà
async def create_table():
    async with aiosqlite.connect('Main.db') as db:
        cursor = await db.execute("CREATE TABLE IF NOT EXISTS users (discord_id TEXT, discord_username TEXT, epic_username TEXT, elo INTEGER, wins INTEGER, losses INTEGER, tracker_link TEXT)")
        await cursor.close()
        await db.commit()

#-------------------------------------------------------------------------------------------------------------------------  

# Fonction pour insérer des données dans la base de données
async def insert_data(user_id, username, epic_username, elo, wins, losses, tracker_link):
    async with aiosqlite.connect('Main.db') as db:
        await db.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, username, epic_username, elo, wins, losses, tracker_link))
        await db.commit()

#-------------------------------------------------------------------------------------------------------------------------

async def remove_data(user_id):
    async with aiosqlite.connect('Main.db') as db:
        await db.execute("DELETE FROM users WHERE discord_id = ?", (user_id,))
        await db.commit()

#-------------------------------------------------------------------------------------------------------------------------

# Fonction pour récupérer des données de la base de données
async def get_data(user_id):
    async with aiosqlite.connect('Main.db') as db:
        cursor = await db.execute("SELECT * FROM users WHERE discord_id = ?", (user_id,))
        data = await cursor.fetchone()
        await cursor.close()
        return data

#-------------------------------------------------------------------------------------------------------------------------

# Fonction pour récupérer des données de la base de données
async def get_elo(user_id):
    async with aiosqlite.connect('Main.db') as db:
        cursor = await db.execute("SELECT elo FROM users WHERE discord_id = ?", (user_id,))
        elo = await cursor.fetchone()
        await cursor.close()
        if elo:  # Check if elo is not None
            return elo[0]  # Return the first element of the tuple
        else:
            return None  # Return None if elo is None


#-------------------------------------------------------------------------------------------------------------------------

async def update_elo(user_id, delta_elo):
    async with aiosqlite.connect('Main.db') as db:
        cursor = await db.execute("SELECT elo FROM users WHERE discord_id = ?", (user_id,))
        current_elo_tuple = await cursor.fetchone()
        current_elo = current_elo_tuple[0]  # Extract the integer value from the tuple
        new_elo = current_elo + delta_elo
        await db.execute("UPDATE users SET elo = ? WHERE discord_id = ?", (new_elo, user_id,))
        await db.commit()


#-------------------------------------------------------------------------------------------------------------------------

async def add_win(user_id):
    async with aiosqlite.connect('Main.db') as db:
        cursor = await db.execute("SELECT wins FROM users WHERE discord_id = ?", (user_id,))
        wins = await cursor.fetchone()
        wins = wins[0] + 1 if wins else 1
        await db.execute("UPDATE users SET wins = ? WHERE discord_id = ?", (wins, user_id,))
        await db.commit()

#-------------------------------------------------------------------------------------------------------------------------

async def add_loss(user_id):
    async with aiosqlite.connect('Main.db') as db:
        cursor = await db.execute("SELECT losses FROM users WHERE discord_id = ?", (user_id,))
        losses = await cursor.fetchone()
        losses = losses[0] + 1 if losses else 1
        await db.execute("UPDATE users SET losses = ? WHERE discord_id = ?", (losses, user_id,))
        await db.commit()

#-------------------------------------------------------------------------------------------------------------------------

async def change_elo(user_id, new_elo):
    async with aiosqlite.connect('Main.db') as db:
        await db.execute("UPDATE users SET elo = ? WHERE discord_id = ?", (new_elo, user_id,))
        await db.commit()

#-------------------------------------------------------------------------------------------------------------------------