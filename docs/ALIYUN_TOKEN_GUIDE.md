# 阿里云盘 Token 获取详细指南

本文档详细说明如何获取阿里云盘的 `Authorization: Bearer` Token。

## 🎯 推荐方式：获取 Access Token（最简单）

### 方法一：通过浏览器开发者工具（推荐）⭐

这是**最简单、最直接**的方法！

#### 步骤：

1. **登录阿里云盘**
   - 打开 https://www.aliyundrive.com
   - 登录你的账号

2. **打开开发者工具**
   - 按 `F12` 键
   - 或右键点击页面 → 选择"检查"

3. **切换到 Network 标签**
   - 点击顶部的 `Network`（网络）标签
   - 确保开发者工具处于打开状态

4. **刷新页面**
   - 按 `F5` 刷新页面
   - 或点击浏览器的刷新按钮

5. **查找 API 请求**
   - 在 Filter（过滤器）中输入 `api`
   - 找到任意一个发往 `api.aliyundrive.com` 的请求
   - 推荐找 `file/list` 或 `user/get` 这类请求

6. **复制 Authorization**
   - 点击该请求
   - 在右侧面板找到 `Request Headers`（请求头）
   - 找到 `Authorization:` 这一行
   - 复制 `Bearer` 后面的整个 Token

**示例：**
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI...
```

你只需要复制 `Bearer` 后面的部分：
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI...
```

7. **（可选）获取 Drive ID**
   - 在同一个请求中，查看 `Request Payload` 或 `Response`
   - 找到 `drive_id` 字段并复制
   - 如果不提供，脚本会自动获取

---

## 🔄 备用方式：获取 Refresh Token

如果你希望 Token 长期有效，可以使用 Refresh Token。

### 方法一：通过 Local Storage

1. **登录阿里云盘**
   - 打开 https://www.aliyundrive.com
   - 登录你的账号

2. **打开开发者工具**
   - 按 `F12`
   - 切换到 `Application` 标签（或 `Storage`）

3. **查找 Token**
   - 左侧展开 `Local Storage`
   - 点击 `https://www.aliyundrive.com`
   - 在右侧找到 `token` 键

4. **复制 Refresh Token**
   - 点击 `token` 键，会显示一个 JSON 对象
   - 找到 `refresh_token` 字段
   - 复制它的值（一长串字符）

**示例：**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "c3e8d9f...",
  "expires_in": 7200,
  ...
}
```

复制 `refresh_token` 的值：`c3e8d9f...`

---

## 📝 配置文件填写

### 方式一：使用 Access Token（推荐）

```json
{
  "baidu": {
    "cookie": "你的百度网盘Cookie"
  },
  "aliyun": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "drive_id": "123456789"
  },
  "sync_tasks": [
    {
      "baidu_folder": "/我的文件夹",
      "aliyun_folder": "/备份/我的文件夹"
    }
  ]
}
```

**注意：**
- `access_token` 是必需的
- `drive_id` 是可选的（脚本会自动获取）

### 方式二：使用 Refresh Token

```json
{
  "baidu": {
    "cookie": "你的百度网盘Cookie"
  },
  "aliyun": {
    "refresh_token": "c3e8d9f1234567890abcdef..."
  },
  "sync_tasks": [...]
}
```

### 方式三：简化配置（兼容旧版）

```json
{
  "baidu_cookie": "你的百度网盘Cookie",
  "aliyun_access_token": "你的阿里云盘access_token",
  "aliyun_drive_id": "你的drive_id（可选）",
  "sync_tasks": [...]
}
```

---

## 🔍 如何验证 Token 是否有效

使用测试脚本验证：

```bash
python3 test_auth.py
```

如果看到以下输出，说明 Token 有效：

```
🟢 测试阿里云盘 Access Token...
✅ 阿里云盘 Access Token 验证成功！
   用户ID: 1234567890
   Drive ID: 123456789
   昵称: 你的昵称
   手机: 138****1234
```

---

## ⚠️ 注意事项

### Token 有效期

- **Access Token**：有效期通常为 2 小时
  - 过期后需要重新获取
  - 适合临时使用或测试

- **Refresh Token**：长期有效
  - 可以自动刷新 Access Token
  - 推荐用于定时同步任务

### 安全建议

1. **不要分享 Token**
   - Token 相当于你的账号密码
   - 不要上传到公开仓库

2. **设置文件权限**
   ```bash
   chmod 600 config.json
   ```

3. **定期更换**
   - 建议定期更新 Token
   - 特别是 Access Token

### Token 失效处理

如果提示 Token 失效：

1. **Access Token 失效**
   - 重新从浏览器获取
   - 或使用 Refresh Token 自动刷新

2. **Refresh Token 失效**
   - 重新登录阿里云盘
   - 从 Local Storage 获取新的 Refresh Token

---

## 🛠️ 使用 curl 测试 Token

你可以使用 curl 命令测试 Token 是否有效：

### 测试 Access Token

```bash
curl -X POST 'https://api.aliyundrive.com/v2/user/get' \
  -H 'Authorization: Bearer 你的access_token' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

成功响应示例：
```json
{
  "user_id": "1234567890",
  "nick_name": "你的昵称",
  "default_drive_id": "123456789",
  ...
}
```

### 测试 Refresh Token

```bash
curl -X POST 'https://api.aliyundrive.com/token/refresh' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "你的refresh_token"}'
```

成功响应示例：
```json
{
  "access_token": "新的access_token",
  "refresh_token": "新的refresh_token",
  "expires_in": 7200,
  ...
}
```

---

## 📊 对比：Access Token vs Refresh Token

| 特性 | Access Token | Refresh Token |
|------|-------------|---------------|
| 获取难度 | ⭐⭐⭐⭐⭐ 非常简单 | ⭐⭐⭐ 中等 |
| 有效期 | 2 小时 | 长期有效 |
| 适用场景 | 临时使用、测试 | 定时任务、长期使用 |
| 自动刷新 | ❌ 不支持 | ✅ 支持 |
| 推荐度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**建议：**
- 测试时使用 Access Token（快速简单）
- 生产环境使用 Refresh Token（稳定可靠）

---

## 💡 常见问题

### Q1: Access Token 在哪里找？

**A:** 打开阿里云盘网页 → F12 → Network → 刷新页面 → 找任意 API 请求 → 查看 Request Headers 中的 `Authorization`

### Q2: Drive ID 必须提供吗？

**A:** 不是必须的。如果不提供，脚本会自动从用户信息中获取。

### Q3: Token 多久会过期？

**A:** 
- Access Token：约 2 小时
- Refresh Token：长期有效（除非手动撤销）

### Q4: 如何获取长期有效的认证？

**A:** 使用 Refresh Token，它可以自动刷新 Access Token。

### Q5: 为什么推荐用 Bearer Token 而不是 Cookie？

**A:** 
- Bearer Token 是官方 API 的标准认证方式
- 更稳定、更可靠
- 不受浏览器 Cookie 策略影响

---

## 🎯 快速开始

1. **获取 Access Token**（1 分钟）
   - 登录阿里云盘
   - F12 → Network → 刷新
   - 复制任意请求的 Authorization

2. **填写配置文件**
   ```json
   {
     "aliyun": {
       "access_token": "粘贴你的token"
     }
   }
   ```

3. **测试**
   ```bash
   python3 test_auth.py
   ```

4. **开始同步**
   ```bash
   python3 baidu_to_aliyun_sync.py
   ```

---

**祝你使用愉快！** 🎉

如有问题，请查看 [README.md](README.md) 或 [COOKIE_GUIDE.md](COOKIE_GUIDE.md)。
