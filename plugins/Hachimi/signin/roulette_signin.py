import random
import math
import datetime

from ..database.dao import UserDao

async def handle_roulette_signin(user_id: str, user_name: str):
    # 简单的指令匹配
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        try:
            row = await UserDao.get_user_coins(user_id)
            
            if row:
                last_signin = row['last_signin']
                signin_num = row['signin_num']
                current_coins = row['coins']
                
                if last_signin == today:
                    return "贪心的人是不会有好运的..."
                elif last_signin == yesterday:
                    signin_num += 1
                else:
                    signin_num = 1

            else:
                current_coins = 0
                signin_num = 0

            # 随机生成金币 (例如 1 到 100)
            random_1=random.random()
            random_2=random.random()
            variance=math.sqrt(-2*math.log(random_1))*math.cos(2*math.pi*random_2)
            if variance>=0:
                normal=64+10*variance
            else:
                normal=64+15*variance
            if normal>100:
                coins_earned=100
            elif normal<1:
                coins_earned=1
            else:
                coins_earned=round(normal)
            variance=math.sqrt(-2*math.log(random_2))*math.sin(2*math.pi*random_1)
            if variance>5:
                variance=5
            elif variance<-5:
                variance=-5
            coins_extra = int(signin_num/(7+variance))
            coins_earned += coins_extra
            new_coins = current_coins + coins_earned
            
            # 更新数据库
            await UserDao.update_user_coins(user_id, user_name, new_coins, today,signin_num)
            
            # 回复消息
            return f"你已连续签到{signin_num}天,额外奖励{coins_extra}金币"+random.choice([f"\n这是今天的钱，祝你好运...", "今天可别输光光了."]) + f"\n你总共获得了 {coins_earned} 金币"

        except Exception as e:
            return f"系统错误: {e}"

async def handle_get_coin(user_id: str):
    try:
        row = await UserDao.get_user_coins(user_id)
        if row:
            return f"你当前有 {row['coins']} 金币"
        else:
            return "你还没有签到过，无法查询金币数量。"
    except Exception as e:
        return f"系统错误: {e}"

async def handle_get_coin_rank(group_members: list):
    try:
        rows = await UserDao.get_coin_rank(group_members)
        if rows:
            rank_list = "\n".join([f"{i+1}. {row['user_name']} - {row['coins']} 金币" for i, row in enumerate(rows)])
            return f"当前金币排行榜:\n{rank_list}"
        else:
            return "暂无用户签到记录。"
    except Exception as e:
        return f"系统错误: {e}"
