from ncatbot.core import BotClient, GroupMessage, PrivateMessage
from ncatbot.utils import get_log,ncatbot_config



bot = BotClient()
_log = get_log()

# ========== 菜单功能 ==========
@bot.on_group_message()
async def on_group_message(msg: GroupMessage):
    menu_text=""
    if msg.raw_message == "帮助":
        menu_text = """
            这里是帮助
        """
    elif msg.raw_message == "群内数据":  
        menu_text = "dcy126.cn:1080"
    else:
        return

    await msg.reply(menu_text)

@bot.on_private_message()
async def on_private_message(msg: PrivateMessage):
    menu_text=""
    if msg.raw_message == "帮助":
        menu_text = """
            这里是帮助
        """

    elif msg.raw_message == "群内数据":  
        menu_text = "dcy126.cn:1080"
    else:
        return

    await msg.reply(menu_text)

def main():
    ncatbot_config.update_from_file("config.yaml")
    bot.run_frontend()

if __name__ == "__main__":
    main()
