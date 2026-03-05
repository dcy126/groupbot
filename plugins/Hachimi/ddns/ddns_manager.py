import aiohttp
import logging
from ..public.config import CF_CONFIG

_logger = logging.getLogger(__name__)

async def get_public_ip():
    """获取当前公网IP"""
    services = [
        ('https://api.ipify.org?format=json', 'json', 'ip'),
        ('https://ifconfig.me/ip', 'text', None),
        ('https://checkip.amazonaws.com', 'text', None),
        ('https://icanhazip.com', 'text', None)
    ]

    async with aiohttp.ClientSession() as session:
        for url, rtype, key in services:
            try:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        if rtype == 'json':
                            data = await response.json()
                            ip = data.get(key)
                        else:
                            ip = await response.text()
                            ip = ip.strip()
                        
                        if ip:
                            return ip
            except Exception as e:
                _logger.warning(f"Failed to get IP from {url}: {e}")
                continue
                
    _logger.error("Failed to get public IP from all services")
    return None

async def get_dns_record(session, zone_id, record_name):
    """获取Cloudflare上的DNS记录"""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_CONFIG['api_token']}",
        "Content-Type": "application/json"
    }
    params = {
        "name": record_name,
        "type": CF_CONFIG['record_type']
    }
    
    try:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data['success'] and data['result']:
                    return data['result'][0]
            else:
                _logger.error(f"Failed to get DNS record: {await response.text()}")
    except Exception as e:
        _logger.error(f"Error fetching DNS record: {e}")
    return None

async def update_dns_record(session, zone_id, record_id, record_name, ip):
    """更新DNS记录"""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {CF_CONFIG['api_token']}",
        "Content-Type": "application/json"
    }
    data = {
        "type": CF_CONFIG['record_type'],
        "name": record_name,
        "content": ip,
        "ttl": 1,  # Auto
        "proxied": CF_CONFIG['proxied']
    }
    
    try:
        async with session.put(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                if result['success']:
                    _logger.info(f"Successfully updated DNS record {record_name} to {ip}")
                    return True
                else:
                    _logger.error(f"Cloudflare update failed: {result['errors']}")
            else:
                _logger.error(f"Failed to update DNS record: {await response.text()}")
    except Exception as e:
        _logger.error(f"Error updating DNS record: {e}")
    return False

async def run_ddns_task():
    """DDNS主任务"""
    # 检查配置是否填写
    if CF_CONFIG['api_token'] == "YOUR_API_TOKEN":
        _logger.warning("Cloudflare DDNS configuration not set. Skipping task.")
        return "DDNS未配置"

    current_ip = await get_public_ip()
    if not current_ip:
        _logger.error("Could not obtain public IP")
        return "无法获取公网IP"

    async with aiohttp.ClientSession() as session:
        record = await get_dns_record(session, CF_CONFIG['zone_id'], CF_CONFIG['record_name'])
        
        if not record:
            _logger.error(f"DNS record {CF_CONFIG['record_name']} not found")
            return "未找到DNS记录"
            
        dns_ip = record['content']
        
        if current_ip != dns_ip:
            _logger.info(f"IP changed from {dns_ip} to {current_ip}. Updating...")
            success = await update_dns_record(session, CF_CONFIG['zone_id'], record['id'], CF_CONFIG['record_name'], current_ip)
            if success:
                return f"DDNS已更新: {dns_ip} -> {current_ip}"
            else:
                return "DDNS更新失败"
        else:
            _logger.debug("IP has not changed.")
            return "IP未变动"
