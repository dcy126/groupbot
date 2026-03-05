from ..db import Database

class NewsDao:
    @staticmethod
    async def news_exists(url):
        pool = await Database.get_pool()
        row = await pool.fetchrow('SELECT 1 FROM t_news WHERE url = $1', url)
        return bool(row)

    @staticmethod
    async def add_news(url, title):
        pool = await Database.get_pool()
        await pool.execute('INSERT INTO t_news (url, title) VALUES ($1, $2)', url, title)
