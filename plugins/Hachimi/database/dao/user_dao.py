from ..db import Database

class UserDao:
    @staticmethod
    async def get_user_coins(user_id):
        pool = await Database.get_pool()
        return await pool.fetchrow('SELECT * FROM t_signin WHERE user_id = $1', user_id)

    @staticmethod
    async def update_user_coins(user_id, user_name, coins, date, signin_num):
        pool = await Database.get_pool()
        await pool.execute('''
            INSERT INTO t_signin (user_id, user_name, coins, last_signin, signin_num)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id)
            DO UPDATE SET coins = $3, last_signin = $4, signin_num = $5
        ''', user_id, user_name, coins, date, signin_num)


    @staticmethod
    async def get_coin_rank(group_members: list):
        pool = await Database.get_pool()
        rows = await pool.fetch('''
            SELECT user_id, user_name, coins, last_signin, signin_num
            FROM t_signin
            WHERE user_id = ANY($1)
            ORDER BY coins DESC
            LIMIT 10
        ''', group_members)
        return rows
