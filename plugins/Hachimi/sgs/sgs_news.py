import asyncio
import requests
from bs4 import BeautifulSoup
import re

from ..database.dao import NewsDao, SubscriptionDao
from ..public.config import SGS_NEWS_URL
from ncatbot.utils import status

async def handle_sgs_command(flag: bool,group_id: str):
    if flag:
        try:
            await SubscriptionDao.add_subscription(group_id, 'sgs_news')
            return "本群已开启三国杀公告推送。" 
        except Exception as e:
            return f"开启失败: {e}"

    else:
        try:
            await SubscriptionDao.remove_subscription(group_id, 'sgs_news')
            return "本群已关闭三国杀公告推送。"
        except Exception as e:
            return f"关闭失败: {e}"

async def fetch_latest_news():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: requests.get(SGS_NEWS_URL, headers=headers))
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = soup.find('ul', class_='press-list')
        if not news_list:
            print("Could not find news list")
            return None

        first_item = news_list.find('li')
        if not first_item:
            print("Could not find first item")
            return None

        link_tag = first_item.find('a')
        if not link_tag:
            print("Could not find link tag")
            return None
            
        href = link_tag.get('href')
        if not href.startswith('http'):
            href = "https://x.sanguosha.com" + href
            
        title_span = link_tag.find('div', class_='press-name')
        if title_span:
            title = re.sub(r'\s+', ' ', title_span.text).strip()
        else:
            title = "无标题公告"
        
        return {"url": href, "title": title}

    except Exception as e:
        print(f"Error fetching news: {e}")
        return None

async def check_and_push_news():
    print("Starting SGS news check task...")
    try:
        
        news = await fetch_latest_news()
        if not news:
            return

        # Check if exists
        if await NewsDao.news_exists(news['url']):
            return
            
        print(f"New SGS news found: {news['title']}")
        
        # Insert into history
        await NewsDao.add_news(news['url'], news['title'])
        
        # Get subscribed groups
        group_ids = await SubscriptionDao.get_subscribed_groups('sgs_news')
        
        message = f"【三国杀新公告】\n\n{news['title']}\n\n{news['url']}"
        
        for group_id in group_ids:
            try:
                await status.global_api.post_group_msg(group_id=group_id, text=message)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to send to group {group_id}: {e}")
                    
    except Exception as e:
        print(f"Error in news loop: {e}")
        import traceback
        traceback.print_exc()

async def handle_get_news():
    news = await fetch_latest_news()
    return f"\n【三国杀新公告】\n{news['title']}\n\n{news['url']}"
    