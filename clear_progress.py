#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除同步进度文件
用于重新开始完整同步
"""

import os
import sys

def clear_progress(temp_dir: str = "/tmp/pan_sync"):
    """清除进度文件"""
    progress_file = os.path.join(temp_dir, ".sync_progress.pkl")
    
    if os.path.exists(progress_file):
        try:
            os.remove(progress_file)
            print(f"✅ 已清除进度文件: {progress_file}")
            print("下次运行将重新开始完整同步")
        except Exception as e:
            print(f"❌ 清除失败: {str(e)}")
            sys.exit(1)
    else:
        print(f"ℹ️  进度文件不存在: {progress_file}")
        print("无需清除")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清除同步进度文件")
    parser.add_argument("--temp-dir", default="/tmp/pan_sync", help="临时目录路径")
    
    args = parser.parse_args()
    clear_progress(args.temp_dir)
