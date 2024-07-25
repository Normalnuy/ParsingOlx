import aiosqlite

class UsersDataBase:
    def __init__(self):
        self.name = 'dbs/admins.db'
        
    async def create_table(self):
        async with aiosqlite.connect(self.name) as db:
            cursor = await db.cursor()
            create_users_table = '''
                CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY, 
                name TEXT
                );
                '''
            await cursor.execute(create_users_table)
            await db.commit()
            
    async def add_user(self, id: int, name: str):
        async with aiosqlite.connect(self.name) as db:
            if not await self.get_user(id):
                cursor = await db.cursor()
                query = 'INSERT INTO admins (id, name) VALUES (?, ?)'
                await cursor.execute(query, (id, name))
                await db.commit()
                
    async def get_user(self, id: int):
        async with aiosqlite.connect(self.name) as db:
            cursor = await db.cursor()
            query = 'SELECT * FROM admins WHERE id = ?'
            await cursor.execute(query, (id,))
            return await cursor.fetchone()
        
    async def get_all_users(self):
        async with aiosqlite.connect(self.name) as db:
            cursor = await db.cursor()
            query = 'SELECT * FROM admins ORDER BY id DESC'
            await cursor.execute(query)
            return await cursor.fetchall()
