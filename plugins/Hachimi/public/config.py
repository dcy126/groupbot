# 数据库配置
DB_CONFIG = {
    "user": "",
    "password": "",
    "database": "groupbot",
    "host": "192.168.0.104",
    "port": 5432
}

SGS_NEWS_URL = "https://x.sanguosha.com/news"

# Cloudflare DDNS配置
CF_CONFIG = {
    "api_token": "",
    "zone_id": "",
    "record_name": "",  # 需要更新的域名
    "record_type": "A",
    "proxied": False  # 是否开启CF代理
}