#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理无效的HTML文件，只保留有效的JSON数据文件
"""

import os
import json
from pathlib import Path

def clean_invalid_files():
    """清理无效的文件"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        print("data目录不存在")
        return
    
    print(f"开始清理 {data_dir} 目录...")
    
    valid_count = 0
    invalid_count = 0
    
    files = list(data_dir.glob("*.json"))
    print(f"找到 {len(files)} 个文件")
    
    for file_path in files:
        try:
            print(f"检查文件: {file_path.name}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # 检查是否是HTML内容
            if content.startswith('<!DOCTYPE') or '<html' in content.lower():
                print(f"删除HTML文件: {file_path.name}")
                file_path.unlink()
                invalid_count += 1
            else:
                # 尝试解析JSON
                try:
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) > 0:
                        print(f"保留有效文件: {file_path.name} ({len(data)} 条数据)")
                        valid_count += 1
                    else:
                        print(f"删除空数据文件: {file_path.name}")
                        file_path.unlink()
                        invalid_count += 1
                except json.JSONDecodeError as e:
                    print(f"删除非JSON文件: {file_path.name} (JSON解析错误: {str(e)[:50]}...)")
                    file_path.unlink()
                    invalid_count += 1
                    
        except Exception as e:
            print(f"处理文件 {file_path.name} 时出错: {e}")
    
    print(f"\n清理完成! 保留有效文件: {valid_count}, 删除无效文件: {invalid_count}")

if __name__ == "__main__":
    clean_invalid_files()
