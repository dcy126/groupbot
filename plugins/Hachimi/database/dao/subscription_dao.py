from ..db import Database

class SubscriptionDao:
    @staticmethod
    async def add_subscription(group_id, feature):
        pool = await Database.get_pool()
        await pool.execute('''
            INSERT INTO t_subscription (group_id, feature)
            VALUES ($1, $2)
            ON CONFLICT (group_id, feature) DO NOTHING
        ''', group_id, feature)

    @staticmethod
    async def remove_subscription(group_id, feature):
        pool = await Database.get_pool()
        await pool.execute('''
            DELETE FROM t_subscription
            WHERE group_id = $1 AND feature = $2
        ''', group_id, feature)

    @staticmethod
    async def get_subscribed_groups(feature):
        pool = await Database.get_pool()
        rows = await pool.fetch('SELECT group_id FROM t_subscription WHERE feature = $1', feature)
        return [row['group_id'] for row in rows]
