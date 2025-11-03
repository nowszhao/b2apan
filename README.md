# 百度云盘到阿里云盘同步工具

一个用于将百度云盘文件夹同步到阿里云盘的 Python 脚本，支持在 Linux CentOS 系统上运行。

## 功能特性

- ✅ **流式同步**：边扫描边同步，不预先统计，大文件夹也不卡顿
- ✅ **断点续传**：支持文件级别断点续传，中断后可继续同步
- ✅ **智能跳过**：自动跳过已存在和已完成的文件
- ✅ **多线程并发**：支持多线程同时上传，提高效率
- ✅ **自动创建目录**：自动在阿里云盘创建对应的文件夹结构
- ✅ **实时进度**：显示已完成文件数，无需等待统计
- ✅ **详细日志**：记录所有操作到 `sync.log` 文件
- ✅ **阿里云盘秒传**：支持秒传功能，节省时间

## 系统要求

- Python 3.6+
- CentOS 7/8 或其他 Linux 发行版
- 网络连接

## 安装步骤

### 1. 安装 Python 3（如果未安装）

```bash
# CentOS 7
sudo yum install -y python3 python3-pip

# CentOS 8
sudo dnf install -y python3 python3-pip
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

或者直接安装：

```bash
pip3 install requests
```

## 配置说明

### 1. 复制配置文件

```bash
cp config.json.example config.json
```

### 2. 获取认证信息（推荐使用 Cookie）

**🔵 百度网盘 Cookie 获取（推荐）**

1. 登录 [百度网盘网页版](https://pan.baidu.com)
2. 按 `F12` 打开开发者工具
3. 切换到 `Network` 标签，刷新页面
4. 点击任意请求，在 `Request Headers` 中找到 `Cookie`
5. 复制整个 Cookie 值

**🟢 阿里云盘 Access Token 获取（推荐，最简单）⭐**

1. 登录 [阿里云盘网页版](https://www.aliyundrive.com/)
2. 按 `F12` 打开开发者工具
3. 切换到 `Network` 标签，刷新页面
4. 点击任意 API 请求，在 Request Headers 中找到 `Authorization: Bearer xxx`
5. 复制 `Bearer` 后面的 Token

**备用方式：Refresh Token（长期有效）**

1. 登录阿里云盘后，按 `F12` -> `Application` -> `Local Storage`
2. 找到 `token` 键，复制其中的 `refresh_token` 值

**📖 详细图文教程**

- [ALIYUN_TOKEN_GUIDE.md](ALIYUN_TOKEN_GUIDE.md) - 阿里云盘 Token 获取详细教程（推荐）
- [COOKIE_GUIDE.md](COOKIE_GUIDE.md) - Cookie 获取教程

### 3. 编辑配置文件

编辑 `config.json`：

```json
{
  "baidu": {
    "cookie": "你的百度网盘Cookie"
  },
  "aliyun": {
    "access_token": "你的阿里云盘access_token（推荐）",
    "drive_id": "你的drive_id（可选）"
  },
  "sync_tasks": [
    {
      "baidu_folder": "/我的文件夹",
      "aliyun_folder": "/备份/我的文件夹"
    }
  ],
  "temp_dir": "/tmp/pan_sync",
  "max_workers": 3
}
```

**配置参数说明：**

- `baidu.cookie`: 百度网盘 Cookie（推荐）或 `baidu.access_token`
- `aliyun.access_token`: 阿里云盘 Access Token（推荐，从 `Authorization: Bearer` 获取）
- `aliyun.drive_id`: 阿里云盘 Drive ID（可选，会自动获取）
- `aliyun.refresh_token`: 阿里云盘 Refresh Token（备用，长期有效）
- `sync_tasks`: 同步任务列表
  - `baidu_folder`: 百度云盘源文件夹路径
  - `aliyun_folder`: 阿里云盘目标文件夹路径
- `temp_dir`: 临时文件存储目录（默认 `/tmp/pan_sync`）
- `max_workers`: 并发上传线程数（建议 3-5）

**阿里云盘认证方式（按推荐度排序）：**

1. ⭐⭐⭐⭐⭐ `access_token` - 最简单，从浏览器 Network 获取
2. ⭐⭐⭐⭐ `refresh_token` - 长期有效，适合定时任务
3. ⭐⭐ `cookie` - 不推荐，可能不稳定

**兼容旧版配置格式：**

```json
{
  "baidu_cookie": "你的百度网盘Cookie",
  "aliyun_access_token": "你的阿里云盘access_token",
  "aliyun_drive_id": "你的drive_id（可选）",
  "sync_tasks": [...]
}
```

## 使用方法

### 测试认证（推荐先执行）

在正式同步前，建议先测试 Cookie/Token 是否有效：

```bash
python3 test_auth.py
```

如果测试通过，会显示：
```
🎉 所有认证测试通过！可以开始同步了
```

### 基本使用

```bash
python3 baidu_to_aliyun_sync.py
```

### 后台运行

```bash
nohup python3 baidu_to_aliyun_sync.py > output.log 2>&1 &
```

### 断点续传

如果同步中断，直接重新运行即可继续：

```bash
python3 baidu_to_aliyun_sync.py
```

脚本会自动跳过已完成的文件，从中断处继续。

### 清除进度（重新开始）

如果需要重新开始完整同步：

```bash
python3 clear_progress.py
```

### 定时同步（使用 crontab）

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天凌晨 2 点执行）
0 2 * * * cd /path/to/script && /usr/bin/python3 baidu_to_aliyun_sync.py
```

## 日志查看

同步日志会保存在 `sync.log` 文件中：

```bash
# 实时查看日志
tail -f sync.log

# 查看最近 100 行
tail -n 100 sync.log
```

## 注意事项

1. **认证信息安全**
   - Cookie 和 Token 相当于账号密码，请妥善保管
   - 建议设置配置文件权限：`chmod 600 config.json`
   - 不要将配置文件上传到公开仓库

2. **Cookie/Token 有效期**
   - 百度网盘 Cookie 有效期通常为 30 天
   - 阿里云盘 refresh_token 会自动刷新，长期有效
   - 如果认证失败，请重新获取

3. **文件大小限制**
   - 大文件上传可能需要较长时间
   - 建议根据网络情况调整 `max_workers` 参数

4. **存储空间**
   - 确保临时目录有足够空间存储下载的文件
   - 脚本会在上传完成后自动清理临时文件
   - 采用边下载边上传模式，不会占用太多磁盘空间

5. **网络稳定性**
   - 建议在网络稳定的环境下运行
   - 失败的文件会记录在日志中，可以重新运行脚本

6. **权限问题**
   - 确保脚本有权限访问临时目录
   - 如需要，使用 `chmod +x baidu_to_aliyun_sync.py` 添加执行权限

## 故障排查

### 1. 导入错误

```bash
# 确认 Python 版本
python3 --version

# 重新安装依赖
pip3 install --upgrade requests
```

### 2. Cookie/Token 失效

- 百度云盘：重新获取 Cookie（参考 COOKIE_GUIDE.md）
- 阿里云盘：重新获取 refresh_token
- 检查是否复制完整，没有遗漏字符

### 3. 网络超时

- 增加超时时间（修改脚本中的 `timeout` 参数）
- 减少并发数（降低 `max_workers` 值）

### 4. 权限不足

```bash
# 创建临时目录
sudo mkdir -p /tmp/pan_sync
sudo chmod 777 /tmp/pan_sync
```

## 高级用法

### 同步多个文件夹

在 `config.json` 中添加多个同步任务：

```json
{
  "sync_tasks": [
    {
      "baidu_folder": "/文档",
      "aliyun_folder": "/备份/文档"
    },
    {
      "baidu_folder": "/照片",
      "aliyun_folder": "/备份/照片"
    },
    {
      "baidu_folder": "/视频",
      "aliyun_folder": "/备份/视频"
    }
  ]
}
```

### 自定义临时目录

```json
{
  "temp_dir": "/home/user/pan_temp"
}
```

## 许可证

MIT License

## 免责声明

本工具仅供学习交流使用，请遵守百度网盘和阿里云盘的服务条款。使用本工具产生的任何问题由使用者自行承担。
