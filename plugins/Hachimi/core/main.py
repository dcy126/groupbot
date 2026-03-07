from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.plugin_system import command_registry,group_filter,admin_filter
from ncatbot.core.event import BaseMessageEvent
from ncatbot.core import GroupMessage, PrivateMessage
from ncatbot.core.event.message_segment import At

from ..database.db import Database
from ..signin import roulette_signin
from ..sgs import sgs_news
from ..ddns import ddns_manager
from ..russian.russian import russian_manager

class Hachimi(NcatBotPlugin):
    name = "Hachimi"
    version = "0.0.2"
    author = "梦中云"
    description = "这是一只不可爱的小猫咪"

    async def on_load(self):
        try:
            # Initialize database tables
            await Database.init_tables()
        except Exception as e:
            print(f"Database initialization failed: {e}")

        self.add_scheduled_task(sgs_news.check_and_push_news, "sgs_news", "10m")
        self.add_scheduled_task(ddns_manager.run_ddns_task, "update_ddns", "1h")

    @command_registry.command("轮盘签到", description="签到获取金币")
    async def Hachimi_signin(self, event: BaseMessageEvent):
        text = await roulette_signin.handle_roulette_signin(event.sender.user_id, event.sender.nickname)
        await event.reply(text)
        return

    @command_registry.command("我的金币", description="查询当前金币数量")
    async def Hachimi_getcoin(self, event: BaseMessageEvent):
        text = await roulette_signin.handle_get_coin(event.sender.user_id)
        await event.reply(text)
        return

    @group_filter
    @command_registry.command("金币排行", description="查询当前金币排行榜")
    async def Hachimi_getcoinrank(self, event: GroupMessage):
        # 获取群成员列表
        res = await self.api.get_group_member_list(group_id=event.group_id)
        # 转化列表格式
        member_ids = [str(m.user_id) for m in res.members]

        if member_ids:
            text = await roulette_signin.handle_get_coin_rank(member_ids)
        else:
            text = "获取群成员列表失败"

        await event.reply(text)
        return

    @admin_filter
    @group_filter   
    @command_registry.command("开启三国杀推送", description="三国杀公告推送")
    async def Hachimi_opensgsnews(self, event: GroupMessage):
        text = await sgs_news.handle_sgs_command(True,event.group_id)
        await event.reply(text)
        return

    @admin_filter
    @group_filter   
    @command_registry.command("关闭三国杀推送", description="关闭三国杀公告推送")
    async def Hachimi_closesgsnews(self, event: GroupMessage):
        text = await sgs_news.handle_sgs_command(False,event.group_id)
        await event.reply(text)
        return

    @command_registry.command("公告", description="获取最新三国杀公告")
    async def Hachimi_getnews(self, event: BaseMessageEvent):
        text = await sgs_news.handle_get_news()
        await event.reply(text)
        return

    @admin_filter
    @command_registry.command("DDNS", description="手动触发DDNS更新")
    async def Hachimi_ddns_update(self, event: BaseMessageEvent):
        text = await ddns_manager.run_ddns_task()
        await event.reply(text)
        return
    
    @group_filter
    @command_registry.command("装弹", description="开启决斗", aliases=["俄罗斯轮盘", "俄罗斯转盘"])
    async def russian_start(self, event: GroupMessage,bullet_num: int,money: int,user: At):
        # 解析参数，例如：装弹 1 200 [CQ:at,qq=12345]
        # parts = event.raw_message.split()
        # bullet_num = 1
        # money = 200
        # at_qq = None
        
        # for part in parts[1:]:
        #     if part.isdigit():
        #         val = int(part)
        #         if 1 <= val <= 6:
        #             bullet_num = val
        #         else:
        #             money = val
        #     elif "CQ:at" in part:
        #         match = re.search(r'qq=(\d+)', part)
        #         if match:
        #             at_qq = match.group(1)
                    
        msg = await russian_manager.ready_game(event, bullet_num, money, user.qq)
        await event.reply(msg)

    @group_filter
    @command_registry.command("接受对决", description="接受决斗", aliases=["接受决斗", "接受挑战"])
    async def russian_accept(self, event: GroupMessage):
        msg = await russian_manager.accept(event)
        await event.reply(f"[CQ:at,qq={event.sender.user_id}] {msg}")

    @group_filter
    @command_registry.command("开枪", description="开枪射击", aliases=["咔", "嘭", "嘣"])
    async def russian_shot(self, event: GroupMessage):
        parts = event.raw_message.split()
        count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        
        msg = await russian_manager.shot(event, count)
        if msg:
            await event.reply(msg)

    @group_filter
    @command_registry.command("结算", description="超时强制结算胜负")
    async def russian_settlement(self, event: GroupMessage):
        group_id = str(event.group_id)
        if group_id in russian_manager._current_player and russian_manager._current_player[group_id].get(2) != 0:
            import time
            if time.time() - russian_manager._current_player[group_id]["time"] > 30:
                await event.reply("决斗已超时，强行结算...")
                await russian_manager.end_game(event, is_timeout=True)
            else:
                await event.reply("决斗尚未超时，不能强行结算！")
        else:
            await event.reply("当前没有可结算的对决。")

    @group_filter
    @command_registry.command("我的战绩", description="查看俄罗斯轮盘战绩")
    async def russian_record(self, event: GroupMessage):
        group_id = str(event.group_id)
        user_id = str(event.sender.user_id)
        if group_id in russian_manager._player_data and user_id in russian_manager._player_data[group_id]:
            user = russian_manager._player_data[group_id][user_id]
            msg = (f"[CQ:at,qq={user_id}]\n俄罗斯轮盘\n"
                   f"胜利场次：{user['win_count']}\n"
                   f"失败场次：{user['lose_count']}\n"
                   f"赚取金币：{user['make_gold']}\n"
                   f"输掉金币：{user['lose_gold']}")
            await event.reply(msg)
        else:
            await event.reply("你还没有参与过对决哦！")