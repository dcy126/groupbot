import asyncpg
import asyncio
from ..public.config import DB_CONFIG

class Database:
    _pool = None
    _lock = None

    @classmethod
    async def get_pool(cls):
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        # Check if pool exists but is bound to a closed/different loop
        if cls._pool is not None:
            try:
                # asyncpg pool stores the loop in _loop
                pool_loop = getattr(cls._pool, '_loop', None)
                if pool_loop and (pool_loop.is_closed() or pool_loop != asyncio.get_running_loop()):
                    print("Database pool loop mismatch or closed. Resetting pool.")
                    cls._pool = None
            except Exception as e:
                print(f"Error checking pool loop: {e}. Resetting pool.")
                cls._pool = None
            
        if cls._pool is None:
            async with cls._lock:
                # Double-check locking pattern
                if cls._pool is None:
                    try:
                        # Ensure optimal pool configuration
                        pool_config = DB_CONFIG.copy()
                        if 'min_size' not in pool_config:
                            pool_config['min_size'] = 5
                        if 'max_size' not in pool_config:
                            pool_config['max_size'] = 20
                        if 'command_timeout' not in pool_config:
                            pool_config['command_timeout'] = 60
                        
                        # Disable SSL to prevent "Fatal error on SSL transport" on Windows
                        if 'ssl' not in pool_config:
                            pool_config['ssl'] = False
                        
                        # Set loop explicitly to avoid "Event loop is closed" errors
                        # when asyncpg tries to use a different loop
                        pool_config['loop'] = asyncio.get_running_loop()
                            
                        cls._pool = await asyncpg.create_pool(**pool_config)
                        print("Database pool created with optimized settings.")
                    except Exception as e:
                        print(f"Failed to create database pool: {e}")
                        raise
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            print("Database pool closed.")

    @classmethod
    async def init_tables(cls):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            # Table for roulette signin
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS public."t_signin"  (
                    user_id varchar(11)   NOT NULL ,
                    user_name varchar(50)   NOT NULL DEFAULT '小哈基米' ,
                    coins int4 NOT NULL ,
                    last_signin date NOT NULL ,
                    signin_num int2 NOT NULL ,
                    PRIMARY KEY (user_id) 
                ) 
            ''')
            # Table for Sanguosha news history
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS "public"."t_news"  (
                    news_id SERIAL NOT NULL,
                    url text NOT NULL,
                    title text NOT NULL ,
                    PRIMARY KEY (news_id) 
                ) 
            ''')
            # Table for group subscriptions
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS "public"."t_subscription"  (
                    group_id varchar(15)   NOT NULL,
                    feature varchar(10)   NOT NULL ,
                    PRIMARY KEY (group_id,feature) 
                ) 
            ''')
        print("Tables initialized.")
