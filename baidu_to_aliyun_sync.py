#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度云盘到阿里云盘文件夹同步脚本
支持 Linux CentOS 系统
"""

import os
import sys
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle

# 导入新的百度网盘客户端
try:
    from baidu_client_pcs import BaiduPanClientPCS
    USE_BAIDUPCS = True
except ImportError:
    USE_BAIDUPCS = False
    logger.warning("baidupcs-py 未安装，将使用原始方法（可能会遇到下载限制）")

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # INFO 级别，简洁清晰
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 如果需要调试，可以设置为 DEBUG
# logger.setLevel(logging.DEBUG)


class BaiduPanClient:
    """百度网盘客户端"""
    
    def __init__(self, cookie: str = None, access_token: str = None):
        """
        初始化百度网盘客户端
        :param cookie: 百度网盘 Cookie（推荐）
        :param access_token: 百度网盘 Access Token（备用）
        """
        self.cookie = cookie
        self.access_token = access_token
        self.base_url = "https://pan.baidu.com/rest/2.0/xpan"
        self.web_url = "https://pan.baidu.com"
        
        # 如果使用 Cookie，需要提取 BDUSS
        if cookie and not access_token:
            self._extract_bduss()
    
    def _extract_bduss(self):
        """从 Cookie 中提取 BDUSS"""
        try:
            for item in self.cookie.split(';'):
                item = item.strip()
                if item.startswith('BDUSS='):
                    self.bduss = item.split('=', 1)[1]
                    logger.info("成功提取 BDUSS")
                    return
            logger.warning("Cookie 中未找到 BDUSS")
        except Exception as e:
            logger.error(f"提取 BDUSS 失败: {str(e)}")
    
    def _get_headers(self) -> Dict:
        """获取请求头"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://pan.baidu.com/disk/main"
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers
        
    def list_files(self, dir_path: str = "/", recursion: int = 0) -> List[Dict]:
        """列出目录下的文件"""
        logger.debug(f"列出文件: {dir_path}, 递归: {recursion}")
        
        # 使用 Cookie 方式
        if self.cookie:
            url = f"{self.web_url}/api/list"
            params = {
                "dir": dir_path,
                "num": 1000,
                "order": "name",
                "desc": 0,
                "web": 1
                # 不设置 folder 参数,获取所有文件和文件夹
            }
            
            try:
                logger.debug(f"请求百度云盘 API: {url}")
                response = requests.get(url, params=params, headers=self._get_headers(), timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data.get("errno") == 0:
                    file_list = data.get("list", [])
                    logger.debug(f"获取到 {len(file_list)} 个项目")
                    
                    # 如果需要递归，获取子文件夹内容
                    if recursion:
                        all_files = file_list.copy()
                        folders = [f for f in file_list if f.get("isdir") == 1]
                        logger.debug(f"需要递归 {len(folders)} 个子文件夹")
                        for folder in folders:
                            logger.debug(f"递归获取: {folder.get('path')}")
                            sub_files = self.list_files(folder.get("path"), recursion)
                            all_files.extend(sub_files)
                        logger.debug(f"递归完成，总共 {len(all_files)} 个项目")
                        return all_files
                    
                    return file_list
                else:
                    logger.error(f"百度云盘列表获取失败: {data.get('errmsg', '未知错误')}")
                    return []
            except Exception as e:
                logger.error(f"百度云盘API调用失败: {str(e)}")
                return []
        
        # 使用 Access Token 方式（备用）
        else:
            url = f"{self.base_url}/file"
            params = {
                "method": "list",
                "access_token": self.access_token,
                "dir": dir_path,
                "recursion": recursion,
                "web": 1
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data.get("errno") == 0:
                    return data.get("list", [])
                else:
                    logger.error(f"百度云盘列表获取失败: {data.get('errmsg', '未知错误')}")
                    return []
            except Exception as e:
                logger.error(f"百度云盘API调用失败: {str(e)}")
                return []
    
    def get_download_link(self, fs_id: int) -> Optional[str]:
        """获取文件下载链接"""
        # 使用 Cookie 方式
        if self.cookie:
            # 使用 /api/filemetas 接口获取下载链接
            url = f"{self.web_url}/api/filemetas"
            params = {
                "fsids": json.dumps([fs_id]),
                "dlink": 1,
                "web": 1
            }
            
            try:
                logger.debug(f"请求下载链接: fs_id={fs_id}")
                response = requests.get(url, params=params, headers=self._get_headers(), timeout=30)
                logger.debug(f"响应状态码: {response.status_code}")
                
                data = response.json()
                
                if data.get("errno") == 0:
                    info_list = data.get("info", [])
                    if info_list and len(info_list) > 0:
                        dlink = info_list[0].get("dlink")
                        if dlink:
                            logger.debug(f"成功获取下载链接: {dlink[:100]}...")
                            return dlink
                        else:
                            logger.error(f"响应中没有 dlink 字段")
                    else:
                        logger.error(f"响应中没有 info 列表")
                else:
                    logger.error(f"获取下载链接失败: errno={data.get('errno')}, errmsg={data.get('errmsg', '未知错误')}")
                return None
            except Exception as e:
                logger.error(f"获取下载链接异常: {str(e)}")
                return None
        
        # 使用 Access Token 方式（备用）
        else:
            url = f"{self.base_url}/file"
            params = {
                "method": "filemetas",
                "access_token": self.access_token,
                "fsids": json.dumps([fs_id]),
                "dlink": 1
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data.get("errno") == 0 and data.get("list"):
                    return data["list"][0].get("dlink")
                return None
            except Exception as e:
                logger.error(f"获取下载链接失败: {str(e)}")
                return None
    
    def download_file(self, download_url: str, save_path: str) -> bool:
        """下载文件到本地"""
        # 百度网盘下载需要特定的请求头
        headers = {
            "User-Agent": "pan.baidu.com",  # 关键：使用百度网盘的 User-Agent
            "Referer": "https://pan.baidu.com/",
            "Cookie": self.cookie if self.cookie else ""
        }
        
        try:
            response = requests.get(download_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"文件下载成功: {save_path}")
            return True
        except Exception as e:
            logger.error(f"文件下载失败 {save_path}: {str(e)}")
            return False


class AliyunPanClient:
    """阿里云盘客户端"""
    
    def __init__(self, cookie: str = None, refresh_token: str = None, access_token: str = None, drive_id: str = None):
        """
        初始化阿里云盘客户端
        :param cookie: 阿里云盘 Cookie（可选）
        :param refresh_token: 阿里云盘 Refresh Token（推荐）
        :param access_token: 阿里云盘 Access Token（可选，配合 drive_id 使用）
        :param drive_id: 阿里云盘 Drive ID（使用 access_token 时必需）
        """
        self.cookie = cookie
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.drive_id = drive_id
        self.base_url = "https://api.aliyundrive.com"
        self.web_url = "https://www.aliyundrive.com"
        
        # 优先级：access_token > refresh_token > cookie
        if access_token and drive_id:
            # 直接使用提供的 access_token 和 drive_id
            logger.info("使用 Access Token 认证阿里云盘")
            self._verify_access_token()
        elif refresh_token:
            # 使用 refresh_token 获取 access_token
            logger.info("使用 Refresh Token 认证阿里云盘")
            self._refresh_access_token()
        elif cookie:
            # 尝试从 Cookie 中提取或使用 Cookie 认证
            logger.info("尝试使用 Cookie 认证阿里云盘")
            success = self._extract_token_from_cookie()
            if not success:
                raise ValueError("Cookie 认证失败，建议使用 refresh_token 或 access_token")
        else:
            raise ValueError("必须提供 access_token+drive_id、refresh_token 或 cookie 之一")
    
    def _verify_access_token(self):
        """验证 Access Token 是否有效"""
        try:
            url = f"{self.base_url}/v2/user/get"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json={}, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                # 如果没有提供 drive_id，从响应中获取
                if not self.drive_id:
                    self.drive_id = result.get("default_drive_id")
                logger.info(f"Access Token 验证成功，用户: {result.get('nick_name', 'N/A')}")
            else:
                logger.error(f"Access Token 验证失败，状态码: {response.status_code}")
                raise ValueError("Access Token 无效或已过期")
        except Exception as e:
            logger.error(f"验证 Access Token 失败: {str(e)}")
            raise
    
    def _extract_token_from_cookie(self) -> bool:
        """从 Cookie 中提取 token 信息或直接使用 Cookie 认证"""
        try:
            logger.info("尝试使用 Cookie 认证阿里云盘...")
            
            # 方法1: 尝试从 Cookie 中提取 token 字段
            # 有些浏览器插件会将 token 存入 Cookie
            token_found = False
            for item in self.cookie.split(';'):
                item = item.strip()
                if item.startswith('token=') or item.startswith('refresh_token='):
                    token_value = item.split('=', 1)[1]
                    if len(token_value) > 50:  # token 通常很长
                        self.refresh_token = token_value
                        logger.info("从 Cookie 中提取到 refresh_token")
                        return self._refresh_access_token()
            
            # 方法2: 尝试通过 Cookie 直接访问 API
            # 获取用户信息和 drive_id
            url = f"{self.base_url}/v2/user/get"
            headers = {
                "Cookie": self.cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json={}, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.drive_id = result.get("default_drive_id")
                
                if self.drive_id:
                    logger.info("通过 Cookie 获取用户信息成功")
                    # 尝试从响应头或其他地方获取 access_token
                    # 注意：这种方式可能不稳定，建议使用 refresh_token
                    return True
                else:
                    logger.warning("未能获取 drive_id")
                    return False
            else:
                logger.warning(f"Cookie 认证失败，状态码: {response.status_code}")
                logger.info("建议使用 refresh_token 方式，更稳定可靠")
                return False
                
        except Exception as e:
            logger.error(f"Cookie 认证失败: {str(e)}")
            logger.info("建议使用 refresh_token 方式")
            return False
        
    def _refresh_access_token(self):
        """刷新访问令牌"""
        url = f"{self.base_url}/token/refresh"
        data = {
            "refresh_token": self.refresh_token
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
            self.drive_id = result.get("default_drive_id")
            
            logger.info("阿里云盘令牌刷新成功")
        except Exception as e:
            logger.error(f"阿里云盘令牌刷新失败: {str(e)}")
            raise
    
    def _get_headers(self) -> Dict:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        if self.cookie:
            headers["Cookie"] = self.cookie
            
        return headers
    
    def get_file_by_path(self, file_path: str) -> Optional[Dict]:
        """根据路径获取文件信息"""
        url = f"{self.base_url}/v2/file/get_by_path"
        data = {
            "drive_id": self.drive_id,
            "file_path": file_path
        }
        
        try:
            response = requests.post(url, json=data, headers=self._get_headers(), timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.debug(f"文件不存在: {file_path}")
                return None
            else:
                logger.debug(f"获取文件信息失败: {file_path}, 状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.debug(f"获取文件信息异常: {file_path}, {str(e)}")
            return None
    
    def create_folder(self, parent_file_id: str, folder_name: str) -> Optional[str]:
        """创建文件夹"""
        url = f"{self.base_url}/adrive/v2/file/createWithFolders"
        data = {
            "drive_id": self.drive_id,
            "parent_file_id": parent_file_id,
            "name": folder_name,
            "check_name_mode": "auto_rename",  # 改为自动重命名，避免冲突
            "type": "folder"
        }
        
        try:
            response = requests.post(url, json=data, headers=self._get_headers(), timeout=30)
            
            # 详细的错误信息
            # 201 Created 也是成功状态
            if response.status_code not in [200, 201]:
                error_msg = f"状态码: {response.status_code}, 响应: {response.text}"
                logger.error(f"文件夹创建失败 '{folder_name}': {error_msg}")
                
                # 尝试解析错误信息
                try:
                    error_data = response.json()
                    if error_data.get("code") == "AlreadyExist.File":
                        logger.info(f"文件夹已存在: {folder_name}，尝试获取...")
                        # 文件夹已存在，尝试通过列表获取
                        return self._get_folder_id_by_name(parent_file_id, folder_name)
                except:
                    pass
                
                return None
            
            result = response.json()
            file_id = result.get("file_id")
            logger.info(f"文件夹创建成功: {folder_name} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"文件夹创建异常 '{folder_name}': {str(e)}")
            return None
    
    def _get_folder_id_by_name(self, parent_file_id: str, folder_name: str) -> Optional[str]:
        """通过名称获取文件夹ID"""
        try:
            url = f"{self.base_url}/adrive/v3/file/list"
            data = {
                "drive_id": self.drive_id,
                "parent_file_id": parent_file_id,
                "limit": 100,
                "type": "folder"
            }
            
            response = requests.post(url, json=data, headers=self._get_headers(), timeout=30)
            if response.status_code == 200:
                result = response.json()
                items = result.get("items", [])
                for item in items:
                    if item.get("name") == folder_name:
                        return item.get("file_id")
            return None
        except Exception as e:
            logger.error(f"获取文件夹ID失败: {str(e)}")
            return None
    
    def create_file(self, parent_file_id: str, file_name: str, file_size: int) -> Optional[Dict]:
        """创建文件（获取上传URL）"""
        url = f"{self.base_url}/adrive/v2/file/createWithFolders"
        
        # 计算文件的预创建hash（这里简化处理）
        data = {
            "drive_id": self.drive_id,
            "parent_file_id": parent_file_id,
            "name": file_name,
            "type": "file",
            "check_name_mode": "auto_rename",
            "size": file_size,
            "part_info_list": [{"part_number": 1}]
        }
        
        try:
            response = requests.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            result = response.json()
            
            return result
        except Exception as e:
            logger.error(f"文件创建失败 {file_name}: {str(e)}")
            return None
    
    def upload_file(self, local_path: str, parent_file_id: str, file_name: str) -> bool:
        """上传文件"""
        file_size = os.path.getsize(local_path)
        
        # 创建文件
        create_result = self.create_file(parent_file_id, file_name, file_size)
        if not create_result:
            return False
        
        # 如果文件已存在（秒传）
        if create_result.get("rapid_upload"):
            logger.info(f"文件秒传成功: {file_name}")
            return True
        
        # 获取上传URL
        upload_url = create_result.get("part_info_list", [{}])[0].get("upload_url")
        if not upload_url:
            logger.error(f"未获取到上传URL: {file_name}")
            return False
        
        file_id = create_result.get("file_id")
        upload_id = create_result.get("upload_id")
        
        # 上传文件内容
        try:
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            headers = {
                "Content-Type": ""
            }
            response = requests.put(upload_url, data=file_data, headers=headers, timeout=300)
            response.raise_for_status()
            
            # 完成上传
            complete_url = f"{self.base_url}/v2/file/complete"
            complete_data = {
                "drive_id": self.drive_id,
                "file_id": file_id,
                "upload_id": upload_id
            }
            
            response = requests.post(complete_url, json=complete_data, 
                                    headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            logger.info(f"文件上传成功: {file_name}")
            return True
        except Exception as e:
            logger.error(f"文件上传失败 {file_name}: {str(e)}")
            return False
    
    def get_or_create_folder_by_path(self, folder_path: str) -> Optional[str]:
        """根据路径获取或创建文件夹，返回文件夹ID"""
        logger.debug(f"获取/创建文件夹: {folder_path}")
        
        # 规范化路径
        folder_path = folder_path.strip()
        if folder_path == "/" or folder_path == "" or folder_path == ".":
            logger.debug("返回根目录 ID: root")
            return "root"
        
        # 移除开头的斜杠
        folder_path = folder_path.lstrip("/")
        
        # 检查文件夹是否存在
        logger.debug(f"检查文件夹是否存在: /{folder_path}")
        existing = self.get_file_by_path(f"/{folder_path}")
        if existing:
            file_id = existing.get("file_id")
            logger.debug(f"文件夹已存在，ID: {file_id}")
            return file_id
        
        # 分割路径，逐层创建
        parts = folder_path.split("/")
        current_path = ""
        current_parent_id = "root"
        
        for part in parts:
            if not part:
                continue
            
            current_path = f"{current_path}/{part}" if current_path else part
            full_path = f"/{current_path}"
            
            logger.debug(f"处理路径: {full_path}")
            
            # 检查当前层是否存在
            existing = self.get_file_by_path(full_path)
            if existing:
                current_parent_id = existing.get("file_id")
                logger.debug(f"文件夹已存在: {part}, ID: {current_parent_id}")
            else:
                # 创建当前层
                logger.debug(f"创建文件夹: {part} (父ID: {current_parent_id})")
                folder_id = self.create_folder(current_parent_id, part)
                if not folder_id:
                    logger.error(f"创建文件夹失败: {part}")
                    return None
                current_parent_id = folder_id
        
        return current_parent_id


class BaiduToAliyunSync:
    """百度云盘到阿里云盘同步器"""
    
    def __init__(self, baidu_config: Dict, aliyun_config: Dict, temp_dir: str = "/tmp/pan_sync"):
        """
        初始化同步器
        :param baidu_config: 百度网盘配置 {"cookie": "..."} 或 {"access_token": "..."}
        :param aliyun_config: 阿里云盘配置，支持以下格式：
            - {"access_token": "...", "drive_id": "..."}  # 推荐：直接使用 Bearer Token
            - {"refresh_token": "..."}  # 推荐：使用 Refresh Token
            - {"cookie": "..."}  # 备用：使用 Cookie
        """
        # 初始化百度网盘客户端
        if "cookie" in baidu_config and USE_BAIDUPCS:
            # 优先使用 baidupcs-py（可以绕过下载限制）
            logger.info("使用 baidupcs-py 客户端")
            self.baidu_client = BaiduPanClientPCS(cookie=baidu_config["cookie"])
        elif "cookie" in baidu_config:
            self.baidu_client = BaiduPanClient(cookie=baidu_config["cookie"])
        else:
            self.baidu_client = BaiduPanClient(access_token=baidu_config.get("access_token"))
        
        # 初始化阿里云盘客户端
        if "access_token" in aliyun_config:
            # 使用 Access Token + Drive ID 方式
            self.aliyun_client = AliyunPanClient(
                access_token=aliyun_config["access_token"],
                drive_id=aliyun_config.get("drive_id")
            )
        elif "refresh_token" in aliyun_config:
            # 使用 Refresh Token 方式
            self.aliyun_client = AliyunPanClient(refresh_token=aliyun_config["refresh_token"])
        elif "cookie" in aliyun_config:
            # 使用 Cookie 方式
            self.aliyun_client = AliyunPanClient(cookie=aliyun_config["cookie"])
        else:
            raise ValueError("阿里云盘配置必须包含 access_token、refresh_token 或 cookie")
        
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        
        # 断点续传：记录已完成的文件
        self.progress_file = os.path.join(temp_dir, ".sync_progress.pkl")
        self.completed_files: Set[str] = self._load_progress()
    
    def _load_progress(self) -> Set[str]:
        """加载同步进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'rb') as f:
                    progress = pickle.load(f)
                logger.info(f"加载断点续传记录: {len(progress)} 个已完成文件")
                return progress
            except Exception as e:
                logger.warning(f"加载进度文件失败: {str(e)}")
        return set()
    
    def _save_progress(self):
        """保存同步进度"""
        try:
            with open(self.progress_file, 'wb') as f:
                pickle.dump(self.completed_files, f)
        except Exception as e:
            logger.error(f"保存进度文件失败: {str(e)}")
    
    def _mark_completed(self, file_path: str):
        """标记文件为已完成"""
        self.completed_files.add(file_path)
        self._save_progress()
    
    def _is_completed(self, file_path: str) -> bool:
        """检查文件是否已完成"""
        return file_path in self.completed_files
        
    def sync_folder(self, baidu_folder: str, aliyun_folder: str, max_workers: int = 3):
        """
        流式同步文件夹（不预先统计，边扫描边同步）
        支持断点续传
        """
        logger.info(f"开始同步: {baidu_folder} -> {aliyun_folder}")
        logger.info(f"并发数: {max_workers}")
        
        # 确保阿里云盘目标文件夹存在
        logger.info(f"检查目标文件夹: {aliyun_folder}")
        target_folder_id = self.aliyun_client.get_or_create_folder_by_path(aliyun_folder)
        if not target_folder_id:
            logger.error("无法创建目标文件夹")
            return
        
        # 统计计数器
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 流式处理：边扫描边同步
        logger.info("开始流式扫描和同步...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            # 递归处理目录
            def process_directory(dir_path: str, target_base: str):
                nonlocal success_count, fail_count, skip_count
                
                logger.info(f"📁 扫描目录: {dir_path}")
                
                # 获取当前目录的文件列表（不递归）
                items = self.baidu_client.list_files(dir_path, recursion=0)
                
                if not items:
                    logger.debug(f"目录为空: {dir_path}")
                    return
                
                # 分类文件和文件夹
                folders = [f for f in items if f.get("isdir") == 1]
                files = [f for f in items if f.get("isdir") == 0]
                
                logger.info(f"  发现: {len(files)} 个文件, {len(folders)} 个子文件夹")
                
                # 处理文件
                for file_info in files:
                    file_path = file_info.get("path")
                    file_name = file_info.get("server_filename")
                    
                    # 检查是否已完成（断点续传）
                    if self._is_completed(file_path):
                        skip_count += 1
                        logger.info(f"⏭️  跳过已完成: {file_name} (总计跳过: {skip_count})")
                        continue
                    
                    # 提交同步任务
                    logger.info(f"📤 提交任务: {file_name}")
                    future = executor.submit(
                        self._sync_single_file, 
                        file_info, 
                        baidu_folder, 
                        aliyun_folder
                    )
                    futures[future] = file_info
                
                # 递归处理子文件夹
                for folder in folders:
                    folder_path = folder.get("path")
                    folder_name = folder.get("server_filename")
                    
                    # 计算阿里云盘路径
                    relative_path = folder_path.replace(baidu_folder, "").lstrip("/")
                    aliyun_path = os.path.join(aliyun_folder, relative_path).replace("\\", "/")
                    
                    # 创建文件夹
                    logger.info(f"📁 创建文件夹: {folder_name}")
                    self.aliyun_client.get_or_create_folder_by_path(aliyun_path)
                    
                    # 递归处理子目录
                    process_directory(folder_path, aliyun_folder)
            
            # 开始处理根目录
            process_directory(baidu_folder, aliyun_folder)
            
            # 等待所有任务完成
            if futures:
                logger.info(f"等待 {len(futures)} 个文件同步任务完成...")
                
                for future in as_completed(futures):
                    file_info = futures[future]
                    file_name = file_info.get("server_filename")
                    
                    try:
                        if future.result():
                            success_count += 1
                            logger.info(f"✅ 完成: {file_name} (成功: {success_count}, 失败: {fail_count}, 跳过: {skip_count})")
                        else:
                            fail_count += 1
                            logger.warning(f"❌ 失败: {file_name} (成功: {success_count}, 失败: {fail_count}, 跳过: {skip_count})")
                    except Exception as e:
                        fail_count += 1
                        logger.error(f"❌ 异常: {file_name} - {str(e)}")
        
        # 最终统计
        logger.info("=" * 60)
        logger.info(f"同步完成！")
        logger.info(f"  ✅ 成功: {success_count}")
        logger.info(f"  ❌ 失败: {fail_count}")
        logger.info(f"  ⏭️  跳过: {skip_count}")
        logger.info(f"  📊 总计: {success_count + fail_count + skip_count}")
        logger.info("=" * 60)
    
    def _sync_single_file(self, file_info: Dict, baidu_base: str, aliyun_base: str) -> bool:
        """同步单个文件（支持断点续传）"""
        file_path = file_info.get("path")
        file_name = file_info.get("server_filename")
        fs_id = file_info.get("fs_id")
        file_size = file_info.get("size", 0)
        
        # 格式化文件大小
        size_mb = file_size / (1024 * 1024)
        size_str = f"{size_mb:.2f}MB" if size_mb >= 1 else f"{file_size / 1024:.2f}KB"
        
        # 计算相对路径
        relative_path = file_path.replace(baidu_base, "").lstrip("/")
        relative_dir = os.path.dirname(relative_path)
        
        # 计算阿里云盘路径
        if relative_dir:
            aliyun_dir = os.path.join(aliyun_base, relative_dir).replace("\\", "/")
        else:
            aliyun_dir = aliyun_base
        
        aliyun_file_path = os.path.join(aliyun_dir, file_name).replace("\\", "/")
        
        logger.info(f"🔄 同步: {file_name} ({size_str})")
        
        # 检查文件是否已存在
        existing_file = self.aliyun_client.get_file_by_path(aliyun_file_path)
        if existing_file:
            logger.info(f"  文件已存在于阿里云盘，标记为完成")
            self._mark_completed(file_path)
            return True
        
        # 下载到临时目录
        temp_file = os.path.join(self.temp_dir, f"{fs_id}_{file_name}")
        logger.info(f"  ⬇️  下载中...")
        
        # 根据客户端类型选择下载方式
        if USE_BAIDUPCS and isinstance(self.baidu_client, BaiduPanClientPCS):
            # 使用 baidupcs-py 直接下载
            if not self.baidu_client.download_file(file_path, temp_file):
                return False
        else:
            # 使用原始方法：先获取下载链接，再下载
            logger.debug(f"  获取下载链接...")
            download_url = self.baidu_client.get_download_link(fs_id)
            if not download_url:
                logger.error(f"  ❌ 无法获取下载链接")
                return False
            
            if not self.baidu_client.download_file(download_url, temp_file):
                return False
        
        # 获取阿里云盘父文件夹ID
        logger.debug(f"  获取父文件夹 ID...")
        parent_folder_id = self.aliyun_client.get_or_create_folder_by_path(aliyun_dir)
        if not parent_folder_id:
            logger.error(f"  ❌ 无法创建父文件夹: {aliyun_dir}")
            try:
                os.remove(temp_file)
            except:
                pass
            return False
        
        # 上传到阿里云盘
        logger.info(f"  ⬆️  上传中...")
        success = self.aliyun_client.upload_file(temp_file, parent_folder_id, file_name)
        
        # 清理临时文件
        try:
            os.remove(temp_file)
        except:
            pass
        
        # 标记为已完成（断点续传）
        if success:
            self._mark_completed(file_path)
            logger.info(f"  ✅ 同步成功")
        else:
            logger.error(f"  ❌ 同步失败")
        
        return success


def load_config(config_file: str = "config.json") -> Dict:
    """加载配置文件"""
    if not os.path.exists(config_file):
        logger.error(f"配置文件不存在: {config_file}")
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"配置文件加载失败: {str(e)}")
        return {}


def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    if not config:
        logger.error("请创建 config.json 配置文件")
        print("\n配置文件示例（推荐使用 Cookie 方式）:")
        print(json.dumps({
            "baidu": {
                "cookie": "你的百度网盘Cookie（推荐）"
            },
            "aliyun": {
                "refresh_token": "你的阿里云盘refresh_token（推荐）"
            },
            "sync_tasks": [
                {
                    "baidu_folder": "/我的文件夹",
                    "aliyun_folder": "/备份/我的文件夹"
                }
            ],
            "temp_dir": "/tmp/pan_sync",
            "max_workers": 3
        }, indent=2, ensure_ascii=False))
        print("\n或使用旧版配置格式:")
        print(json.dumps({
            "baidu_cookie": "你的百度网盘Cookie",
            "aliyun_refresh_token": "你的阿里云盘refresh_token",
            "sync_tasks": [
                {
                    "baidu_folder": "/我的文件夹",
                    "aliyun_folder": "/备份/我的文件夹"
                }
            ]
        }, indent=2, ensure_ascii=False))
        return
    
    # 获取配置参数（支持新旧两种格式）
    sync_tasks = config.get("sync_tasks", [])
    temp_dir = config.get("temp_dir", "/tmp/pan_sync")
    max_workers = config.get("max_workers", 3)
    
    # 解析百度网盘配置
    baidu_config = {}
    if "baidu" in config:
        baidu_config = config["baidu"]
    elif "baidu_cookie" in config:
        baidu_config = {"cookie": config["baidu_cookie"]}
    elif "baidu_access_token" in config:
        baidu_config = {"access_token": config["baidu_access_token"]}
    
    # 解析阿里云盘配置
    aliyun_config = {}
    if "aliyun" in config:
        aliyun_config = config["aliyun"]
    elif "aliyun_access_token" in config:
        # 支持直接使用 access_token
        aliyun_config = {
            "access_token": config["aliyun_access_token"],
            "drive_id": config.get("aliyun_drive_id")
        }
    elif "aliyun_cookie" in config:
        aliyun_config = {"cookie": config["aliyun_cookie"]}
    elif "aliyun_refresh_token" in config:
        aliyun_config = {"refresh_token": config["aliyun_refresh_token"]}
    
    if not baidu_config or not aliyun_config:
        logger.error("请在配置文件中设置百度网盘和阿里云盘的认证信息")
        return
    
    if not sync_tasks:
        logger.error("请在配置文件中设置 sync_tasks")
        return
    
    # 创建同步器
    try:
        syncer = BaiduToAliyunSync(baidu_config, aliyun_config, temp_dir)
    except Exception as e:
        logger.error(f"初始化同步器失败: {str(e)}")
        return
    
    # 执行同步任务
    for task in sync_tasks:
        baidu_folder = task.get("baidu_folder")
        aliyun_folder = task.get("aliyun_folder")
        
        if not baidu_folder or not aliyun_folder:
            logger.warning(f"跳过无效任务: {task}")
            continue
        
        try:
            syncer.sync_folder(baidu_folder, aliyun_folder, max_workers)
        except Exception as e:
            logger.error(f"同步任务失败: {str(e)}")
    
    logger.info("所有同步任务完成")


if __name__ == "__main__":
    main()
