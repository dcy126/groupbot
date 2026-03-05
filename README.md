# NcatBot 轮盘签到插件

这是一个基于 NcatBot 的 QQ 机器人插件，实现了轮盘签到功能，并将数据存储在 PostgreSQL 数据库中。

## 目录结构

- `main.py`: 机器人启动入口
- `config.py`: 配置文件（数据库连接等）
- `plugins/roulette_signin.py`: 轮盘签到插件逻辑
- `requirements.txt`: 项目依赖

## 安装步骤

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置数据库**
   - 确保已安装 PostgreSQL。
   - 创建一个名为 `groupbot_db` 的数据库（或者在 `config.py` 中修改为现有的数据库名）。
   - 修改 `config.py` 中的 `user` 和 `password`。

3. **运行 NapCat**
   - 确保你的 NapCat 客户端已启动并登录 QQ。
   - 确保 WebSocket 服务已开启（默认端口 3001）。

4. **运行机器人**
   ```bash
   python main.py
   ```

## 功能说明

- **轮盘签到**: 在群里发送“轮盘签到”，机器人会随机赠送 10-100 金币，并记录在数据库中。
- **重复签到**: 每天只能签到一次。

## 注意事项

- 本代码基于 NcatBot 的通用用法编写。如果遇到属性错误（如 `msg.sender.user_id` 不存在），请参考 NcatBot 的官方文档或打印 `msg` 对象查看实际结构进行调整。
