# 快速开始指南

5 分钟快速上手百度网盘到阿里云盘同步工具！

## 📋 准备工作

- ✅ Python 3.6+
- ✅ 百度网盘账号
- ✅ 阿里云盘账号
- ✅ 网络连接

## 🚀 三步开始

### 第一步：安装依赖

```bash
pip3 install requests
```

### 第二步：获取认证信息

#### 百度网盘 Cookie

1. 打开 https://pan.baidu.com 并登录
2. 按 `F12` 打开开发者工具
3. 刷新页面，在 Network 中找到任意请求
4. 复制 Request Headers 中的 `Cookie` 值

#### 阿里云盘 Access Token（推荐，最简单）⭐

1. 打开 https://www.aliyundrive.com 并登录
2. 按 `F12` -> Network 标签
3. 刷新页面，点击任意 API 请求
4. 在 Request Headers 中找到 `Authorization: Bearer xxx`
5. 复制 `Bearer` 后面的 Token

> 💡 详细图文教程请查看 [ALIYUN_TOKEN_GUIDE.md](ALIYUN_TOKEN_GUIDE.md)

### 第三步：配置并运行

1. **创建配置文件**

```bash
cp config.json.example config.json
vim config.json  # 或使用其他编辑器
```

2. **填写配置**

```json
{
  "baidu": {
    "cookie": "粘贴你的百度网盘Cookie"
  },
  "aliyun": {
    "access_token": "粘贴你的阿里云盘Access Token"
  },
  "sync_tasks": [
    {
      "baidu_folder": "/我的文件夹",
      "aliyun_folder": "/备份/我的文件夹"
    }
  ]
}
```

3. **测试认证**

```bash
python3 test_auth.py
```

看到 `🎉 所有认证测试通过！` 就可以继续了。

4. **开始同步**

```bash
python3 baidu_to_aliyun_sync.py
```

## 📊 查看进度

同步过程中会实时显示进度（流式处理，无需等待统计）：

```
2024-01-01 10:00:00 - INFO - 开始同步: /我的文件夹 -> /备份/我的文件夹
2024-01-01 10:00:01 - INFO - 📁 扫描目录: /我的文件夹
2024-01-01 10:00:02 - INFO -   发现: 5 个文件, 2 个子文件夹
2024-01-01 10:00:03 - INFO - 📤 提交任务: 文档.pdf
2024-01-01 10:00:04 - INFO - 🔄 同步: 文档.pdf (2.5MB)
2024-01-01 10:00:05 - INFO -   ⬇️  下载中...
2024-01-01 10:00:08 - INFO -   ⬆️  上传中...
2024-01-01 10:00:10 - INFO -   ✅ 同步成功
2024-01-01 10:00:11 - INFO - ✅ 完成: 文档.pdf (成功: 1, 失败: 0, 跳过: 0)
```

**断点续传示例：**

```
2024-01-01 10:05:00 - INFO - 加载断点续传记录: 3 个已完成文件
2024-01-01 10:05:01 - INFO - ⏭️  跳过已完成: 文档1.pdf (总计跳过: 1)
2024-01-01 10:05:02 - INFO - ⏭️  跳过已完成: 文档2.pdf (总计跳过: 2)
2024-01-01 10:05:03 - INFO - 📤 提交任务: 文档3.pdf
```

查看日志文件：

```bash
tail -f sync.log
```

## ⚙️ 常用配置

### 同步多个文件夹

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
    }
  ]
}
```

### 调整并发数

```json
{
  "max_workers": 5
}
```

- 网络好：可设置 5-10
- 网络一般：建议 3-5
- 网络差：设置 1-2

### 自定义临时目录

```json
{
  "temp_dir": "/home/user/pan_temp"
}
```

## 🔄 定时同步

使用 crontab 设置定时任务：

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点同步
0 2 * * * cd /path/to/b2apan && /usr/bin/python3 baidu_to_aliyun_sync.py

# 每 6 小时同步一次
0 */6 * * * cd /path/to/b2apan && /usr/bin/python3 baidu_to_aliyun_sync.py
```

## ❓ 常见问题

### Q: Cookie 多久会过期？

**A:** 百度网盘 Cookie 通常 30 天左右，阿里云盘 Token 会自动刷新。

### Q: 如何跳过已存在的文件？

**A:** 脚本会自动检测并跳过已存在的文件，并支持断点续传。

### Q: 同步中断了怎么办？

**A:** 直接重新运行脚本即可，会自动从中断处继续，已完成的文件会被跳过。

### Q: 如何重新开始完整同步？

**A:** 运行 `python3 clear_progress.py` 清除进度记录。

### Q: 大文件同步很慢怎么办？

**A:** 
- 检查网络速度
- 减少并发数（`max_workers`）
- 使用有线网络而非 WiFi

### Q: 同步失败了怎么办？

**A:** 
1. 查看 `sync.log` 日志
2. 重新运行脚本（会自动跳过已同步文件）
3. 检查 Cookie/Token 是否过期

### Q: 可以同步整个网盘吗？

**A:** 可以，设置 `baidu_folder: "/"` 即可，但建议分批同步。

## 📚 更多文档

- [完整文档](README.md) - 详细功能说明
- [阿里云盘 Token 教程](ALIYUN_TOKEN_GUIDE.md) - Bearer Token 获取详细教程（推荐）
- [Cookie 获取教程](COOKIE_GUIDE.md) - 百度网盘 Cookie 教程
- [配置示例](config.json.example) - 配置模板

## 💡 小贴士

1. **安全第一**：不要分享你的 Cookie/Token
2. **定期备份**：建议定期运行同步任务
3. **检查日志**：遇到问题先查看 `sync.log`
4. **测试先行**：正式使用前先用小文件夹测试
5. **网络稳定**：建议在网络稳定时运行

## 🎯 下一步

- ✅ 设置定时任务实现自动备份
- ✅ 配置多个同步任务
- ✅ 监控日志文件
- ✅ 定期更新 Cookie/Token

---

**祝你使用愉快！** 🎉

如有问题，请查看 [README.md](README.md) 或提交 Issue。
