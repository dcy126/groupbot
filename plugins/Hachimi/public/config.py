# 数据库配置
DB_CONFIG = {
    "user": "postgres",
    "password": "postgres",
    "database": "groupbot",
    "host": "192.168.0.104",
    "port": 5432
}

SGS_NEWS_URL = "https://x.sanguosha.com/news"

# Cloudflare DDNS配置
CF_CONFIG = {
    "api_token": "lAxI9UcRxB-3uuWS90lmtAqQUKYtNI-tZyN7llNR",
    "zone_id": "ca035a98b93548a274725893d9e12d1b",
    "record_name": "dcy126.cn",  # 需要更新的域名
    "record_type": "A",
    "proxied": False  # 是否开启CF代理
}