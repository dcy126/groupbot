import os
import random
import math
import asyncio
import json
import datetime
from pathlib import Path
from ncatbot.core import GroupMessage

# 引入你现有的数据库操作类
from ..database.dao import UserDao

MAX_BET_GOLD = 1000
BOT_NAME = "本猫咪"

def random_bullet(num: int) -> list:
    bullet_lst = [0, 0, 0, 0, 0, 0, 0]
    for i in random.sample([0, 1, 2, 3, 4, 5, 6], num):
        bullet_lst[i] = 1
    return bullet_lst

class RussianManager:
    def __init__(self):
        self._player_data = {}
        self._current_player = {}
        self.file = Path(os.path.dirname(__file__)) / "russian_data.json"
        
        self.timeout = 30  
        
        if self.file.exists():
            with open(self.file, "r", encoding="utf8") as f:
                self._player_data = json.load(f)

    def save(self):
        with open(self.file, "w", encoding="utf8") as f:
            json.dump(self._player_data, f, ensure_ascii=False, indent=4)

    def _init_player_data(self, group_id: str, user_id: str, nickname: str):
        if group_id not in self._player_data:
            self._player_data[group_id] = {}
        if user_id not in self._player_data[group_id]:
            self._player_data[group_id][user_id] = {
                "nickname": nickname,
                "make_gold": 0,
                "lose_gold": 0,
                "win_count": 0,
                "lose_count": 0,
                "is_benefit": False,
            }

    # ================= 自动超时控制核心 =================
    async def _auto_settle_task(self, event: GroupMessage):
        """后台倒计时任务，到达时间后自动结算"""
        try:
            await asyncio.sleep(self.timeout)
            group_id = str(event.group_id)
            current_game = self._current_player.get(group_id, {})
            # 倒计时结束，检查游戏是否仍在进行（发起人和接受人都存在）
            if current_game.get(1) and current_game.get(2):
                await event.reply("⏳ 决斗已超时，系统自动强行结算...")
                await self.end_game(event, is_timeout=True)
        except asyncio.CancelledError:
            pass

    def _cancel_timeout_task(self, group_id: str):
        """取消当前群聊的超时结算任务"""
        current_game = self._current_player.get(group_id, {})
        task = current_game.get("timeout_task")
        if task and not task.done():
            task.cancel()

    def _start_timeout_task(self, event: GroupMessage):
        """重新启动超时结算任务"""
        group_id = str(event.group_id)
        self._cancel_timeout_task(group_id)
        task = asyncio.create_task(self._auto_settle_task(event))
        if group_id in self._current_player:
            self._current_player[group_id]["timeout_task"] = task
    # ====================================================

    async def get_db_coins(self, user_id: str) -> int:
        row = await UserDao.get_user_coins(user_id)
        return row['coins'] if row else 0

    async def add_db_coins(self, user_id: str, user_name: str, amount: int):
        row = await UserDao.get_user_coins(user_id)
        today = datetime.date.today()
        if row:
            new_coins = row['coins'] + amount
            last_signin = row['last_signin']
            signin_num = row['signin_num']
        else:
            new_coins = amount
            last_signin = today - datetime.timedelta(days=1)
            signin_num = 0
        await UserDao.update_user_coins(user_id, user_name, new_coins, last_signin, signin_num)

    async def benefit(self, event: GroupMessage) -> str:
        group_id = str(event.group_id)
        user_id = str(event.sender.user_id)
        nickname = event.sender.nickname
        self._init_player_data(group_id, user_id, nickname)
        
        if self._player_data[group_id][user_id].get("is_benefit"):
            return "一分也没有了，爪捏..."
            
        current_coins = await self.get_db_coins(user_id)
        if current_coins > 0:
            return "带资本家别来抢穷哥们的饭碗啊！"

        normal = 17 + 15 * (math.sqrt(-2*math.log(1.0-random.random()))*math.cos(2*math.pi*(1.0-random.random())))
        gold = min(max(round(normal), 0), 80)

        await self.add_db_coins(user_id, nickname, gold)
        self._player_data[group_id][user_id]["make_gold"] += gold
        self._player_data[group_id][user_id]["is_benefit"] = True
        self.save()
        
        return random.choice(["\n又输完了，再给你一次机会吧...", "慢点输鸭，低保每天只有一次.", "复活吧，我的朋友！"]) + f"\n你总共获得了 {gold} 金币"

    async def ready_game(self, event: GroupMessage, bullet_num: int, money: int, at_qq: str = None) -> str:
        group_id = str(event.group_id)
        user_id = str(event.sender.user_id)
        player1_name = event.sender.nickname
        
        self._init_player_data(group_id, user_id, player1_name)
        
        # 修复：使用更严谨的字典读取方式
        current_game = self._current_player.get(group_id, {})
        if current_game.get(1):
            if datetime.datetime.now().timestamp() - current_game.get("last_active_time", 0) <= self.timeout:
                return "决斗已开始，请等待上一场结束！"
                
        user_money = await self.get_db_coins(user_id)
        if money > MAX_BET_GOLD:
            return f"太多了！单次金额不能超过{MAX_BET_GOLD}！"
        if money > user_money:
            return "你没有足够的钱支撑起这场挑战"

        self._current_player[group_id] = {
            1: user_id,
            "player1": player1_name,
            2: 0,
            "player2": "",
            "at": at_qq,
            "next": user_id,
            "money": money,
            "bullet": random_bullet(bullet_num),
            "bullet_num": bullet_num,
            "null_bullet_num": 7 - bullet_num,
            "index": 0,
            "last_active_time": datetime.datetime.now().timestamp(),
            "timeout_task": None
        }
        
        msg = f"咔 " * bullet_num + f"，装填完毕\n挑战金额：{money}\n第一枪的概率为：{str(float(bullet_num) / 7.0 * 100)[:5]}%\n"
        if at_qq:
            msg += f"{player1_name} 向 [CQ:at,qq={at_qq}] 发起了决斗！请在{self.timeout}秒内回复‘接受对决’或‘拒绝对决’！"
        else:
            msg += f"若{self.timeout}秒内无人接受挑战则对决作废。"
        
        return msg

    async def accept(self, event: GroupMessage) -> str:
        group_id = str(event.group_id)
        user_id = str(event.sender.user_id)
        nickname = event.sender.nickname
        self._init_player_data(group_id, user_id, nickname)
        
        # 修复：防止空字典导致的异常
        current_game = self._current_player.get(group_id, {})
        if not current_game.get(1):
            return "目前没有发起的对决，速速装弹！"
        if current_game.get(2):
            return "你已经身处决斗中，或已有人接受对决！"
        if current_game.get(1) == user_id:
            return "请不要自己枪毙自己！换人来接受对决..."
        if current_game.get("at") and current_game.get("at") != user_id:
            return f"这场对决是邀请别人的，不要捣乱！"
            
        if datetime.datetime.now().timestamp() - current_game.get("last_active_time", 0) > self.timeout:
            self._cancel_timeout_task(group_id)
            self._current_player[group_id] = {}
            return "对决邀请已过时，请重新发起..."

        user_money = await self.get_db_coins(user_id)
        if user_money < current_game.get("money", 0):
            return "你的金币不足以接受这场对决！"

        self._current_player[group_id][2] = user_id
        self._current_player[group_id]["player2"] = nickname
        self._current_player[group_id]["last_active_time"] = datetime.datetime.now().timestamp()

        # 玩家成功接受后，正式开始真正的倒计时
        self._start_timeout_task(event)

        return f"{nickname}接受了对决！\n请[CQ:at,qq={self._current_player[group_id][1]}]在{self.timeout}秒内先开枪！"

    async def shot(self, event: GroupMessage, count: int = 1) -> str:
        group_id = str(event.group_id)
        user_id = str(event.sender.user_id)
        
        current_game = self._current_player.get(group_id, {})
        if not current_game.get(1):
            return "目前没有对决，请先发送 装弹！"
        if not current_game.get(2):
            return "请等待勇士接受对决..."
            
        if datetime.datetime.now().timestamp() - current_game.get("last_active_time", 0) > self.timeout:
            return "决斗已超时..."
            
        if current_game.get("next") != user_id:
            return "你的左轮不是连发的！该对方开枪了！"

        player1_name = current_game.get("player1")
        player2_name = current_game.get("player2")
        current_index = current_game.get("index", 0)
        
        _tmp = current_game.get("bullet", [])[current_index : current_index + count]
        
        if 1 in _tmp:
            flag = _tmp.index(1) + 1
            await event.reply(f'"嘭！"，你直接去世了\n第 {current_index + flag} 发子弹送走了你...')
            await asyncio.sleep(0.5)
            await self.end_game(event, is_timeout=False)
            return None
        else:
            next_user_id = current_game.get(1) if user_id == current_game.get(2) else current_game.get(2)
            self._current_player[group_id]["null_bullet_num"] -= count
            self._current_player[group_id]["next"] = next_user_id
            self._current_player[group_id]["last_active_time"] = datetime.datetime.now().timestamp()
            self._current_player[group_id]["index"] += count
            
            # 玩家开枪没死，重新开始计时！把定时器交接给下一个人
            self._start_timeout_task(event)
            
            x = str(float(current_game.get("bullet_num")) / float(current_game.get("null_bullet_num") + current_game.get("bullet_num")) * 100)[:5]
            
            return f"呼呼，没有爆裂的声响，你活了下来\n下一枪中弹的概率：{x}%\n轮到 [CQ:at,qq={next_user_id}] 了！(请在{self.timeout}秒内开枪)"

    async def end_game(self, event: GroupMessage, is_timeout=False):
        group_id = str(event.group_id)
        current_game = self._current_player.get(group_id, {})
        
        if not current_game.get(1):
            return
            
        # 结算前一定要先停掉潜在的倒计时任务
        self._cancel_timeout_task(group_id)
            
        # 安全防抖：如果在还没人接受的情况下进到这里，直接静默清理
        if not current_game.get(2):
            self._current_player[group_id] = {}
            return
            
        if is_timeout:
            win_user_id = current_game.get("next")
            lose_user_id = current_game.get(1) if win_user_id == current_game.get(2) else current_game.get(2)
        else:
            lose_user_id = current_game.get("next")
            win_user_id = current_game.get(1) if lose_user_id == current_game.get(2) else current_game.get(2)

        win_name = current_game.get("player1") if win_user_id == current_game.get(1) else current_game.get("player2")
        lose_name = current_game.get("player2") if win_user_id == current_game.get(1) else current_game.get("player1")
        
        gold = current_game.get("money", 0)
        rand = random.randint(0, 5)
        fee = max(int(gold * float(rand) / 100), 1) if rand != 0 else 0
        
        # 操作数据库中的金币
        await self.add_db_coins(win_user_id, win_name, gold - fee)
        await self.add_db_coins(lose_user_id, lose_name, -gold)

        # 记录战绩
        self._player_data[group_id][win_user_id]["make_gold"] += (gold - fee)
        self._player_data[group_id][win_user_id]["win_count"] += 1
        self._player_data[group_id][lose_user_id]["lose_gold"] += gold
        self._player_data[group_id][lose_user_id]["lose_count"] += 1
        self.save()

        win_user = self._player_data[group_id][win_user_id]
        lose_user = self._player_data[group_id][lose_user_id]
        
        bullet_str = "".join(["__ " if x == 0 else "| " for x in current_game.get("bullet", [])])
        self._current_player[group_id] = {}
        
        await event.reply(
            f"结算：\n\t胜者：{win_name}\n\t赢取金币：{gold - fee}\n\t累计胜场：{win_user['win_count']}\n"
            f"-------------------\n\t败者：{lose_name}\n\t输掉金币：{gold}\n\t累计败场：{lose_user['lose_count']}\n"
            f"-------------------\n从中收取了 {float(rand)}%({fee}金币) 作为手续费！\n子弹排列：{bullet_str[:-1]}"
        )

    def reset_benefit(self):
        for group in self._player_data.values():
            for user in group.values():
                user["is_benefit"] = False
        self.save()

russian_manager = RussianManager()