#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 baidupcs-py 的百度网盘客户端
"""

import logging
from typing import Dict, List, Optional
from baidupcs_py.baidupcs import BaiduPCS

logger = logging.getLogger(__name__)


class BaiduPanClientPCS:
    """使用 baidupcs-py 的百度网盘客户端"""
    
    def __init__(self, cookie: str):
        """
        初始化百度网盘客户端
        :param cookie: 百度网盘 Cookie
        """
        self.cookie = cookie
        
        # 提取 BDUSS 和转换 Cookie 为字典
        self.bduss = None
        self.cookies_dict = {}
        
        for item in cookie.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                self.cookies_dict[key] = value
                if key == 'BDUSS':
                    self.bduss = value
        
        if not self.bduss:
            raise ValueError("Cookie 中未找到 BDUSS")
        
        logger.info("成功提取 BDUSS")
        
        # 创建 BaiduPCS 实例
        self.api = BaiduPCS(bduss=self.bduss, cookies=self.cookies_dict)
    
    def list_files(self, dir_path: str = "/", recursion: int = 0) -> List[Dict]:
        """列出目录下的文件"""
        try:
            result = self.api.list(dir_path)
            
            if isinstance(result, dict) and 'list' in result:
                file_list = result['list']
                
                # 如果需要递归
                if recursion:
                    all_files = file_list.copy()
                    folders = [f for f in file_list if f.get('isdir') == 1]
                    
                    for folder in folders:
                        sub_files = self.list_files(folder.get('path'), recursion)
                        all_files.extend(sub_files)
                    
                    return all_files
                
                return file_list
            else:
                logger.error(f"列表获取失败: {result}")
                return []
        except Exception as e:
            logger.error(f"列表获取异常: {str(e)}")
            return []
    
    def download_file(self, remote_path: str, save_path: str) -> bool:
        """下载文件到本地"""
        temp_path = f"{save_path}.downloading"  # 下载中的临时文件
        
        try:
            import os
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 检查是否已经下载完成
            if os.path.exists(save_path):
                logger.info(f"文件已存在，跳过下载: {save_path}")
                return True
            
            # 检查是否有未完成的下载
            resume_size = 0
            if os.path.exists(temp_path):
                resume_size = os.path.getsize(temp_path)
                logger.info(f"发现未完成的下载，已下载: {resume_size / 1024 / 1024:.2f}MB")
                # TODO: 实现断点续传（baidupcs-py 的 file_stream 不支持 range）
                # 暂时删除重新下载
                os.remove(temp_path)
                resume_size = 0
            
            # 使用 baidupcs-py 的 file_stream 方法
            logger.debug(f"开始下载: {remote_path}")
            stream = self.api.file_stream(remote_path)
            
            if not stream:
                logger.error(f"无法获取文件流: {remote_path}")
                return False
            
            # 分块读取并写入临时文件
            total_size = 0
            chunk_size = 256 * 1024  # 256KB 每块
            last_log_size = 0
            
            with open(temp_path, 'wb') as f:
                while True:
                    try:
                        chunk = stream.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        total_size += len(chunk)
                        
                        # 每 10MB 打印一次进度
                        if total_size - last_log_size >= 10 * 1024 * 1024:
                            logger.info(f"  📥 下载进度: {total_size / 1024 / 1024:.2f}MB")
                            last_log_size = total_size
                    except Exception as e:
                        logger.error(f"读取数据块失败: {str(e)}")
                        break
            
            # 检查下载的文件
            if os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                
                # 如果文件大小为 0，认为下载失败
                if file_size == 0:
                    logger.error(f"下载的文件大小为 0")
                    os.remove(temp_path)
                    return False
                
                # 下载完成，重命名为正式文件
                os.rename(temp_path, save_path)
                logger.info(f"文件下载完成: {save_path} ({file_size / 1024 / 1024:.2f}MB)")
                return True
            else:
                logger.error(f"下载的文件不存在: {temp_path}")
                return False
                
        except Exception as e:
            logger.error(f"文件下载失败 {save_path}: {str(e)}")
            # 保留 .downloading 文件，下次可以尝试续传
            # 如果确定失败，可以手动删除
            return False
