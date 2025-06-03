#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复问题文章
使用经过验证的实用爬虫方法
"""

import json
import time
import random
from pathlib import Path
from practical_crawler import PracticalCrawler
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_fix.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_problematic_articles():
    """查找所有问题文章"""
    articles_dir = Path("articles")
    problematic_articles = []
    
    for date_dir in articles_dir.iterdir():
        if not date_dir.is_dir():
            continue
            
        date_str = date_dir.name
        
        for article_file in date_dir.glob("*.json"):
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                content = data.get('content', {})
                title = content.get('title', '')
                article_content = content.get('content', '')
                
                # 检查是否是问题文章
                is_problematic = (
                    title == '491 Forbidden' or
                    article_content == '无内容' or
                    '491 Forbidden' in title or
                    len(article_content) < 50
                )
                
                if is_problematic:
                    metadata = data.get('metadata', {})
                    
                    # 从文件名推断页码
                    filename = article_file.stem  # 不包含.json后缀
                    # 格式：20250520_001_02_2642
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        page_no = parts[1]
                    else:
                        page_no = '001'  # 默认值
                    
                    problematic_articles.append({
                        'date': date_str,
                        'page_no': page_no,
                        'metadata': metadata,
                        'file_path': article_file,
                        'title': metadata.get('mainTitle', '未知标题')
                    })
                    
            except Exception as e:
                logger.error(f"读取文件失败 {article_file}: {e}")
    
    return problematic_articles

def batch_fix_articles(max_articles=10):
    """批量修复问题文章"""
    print("查找问题文章...")
    problematic_articles = find_problematic_articles()
    
    if not problematic_articles:
        print("没有发现问题文章")
        return
    
    print(f"发现 {len(problematic_articles)} 篇问题文章")
    
    # 限制修复数量以避免被封
    if len(problematic_articles) > max_articles:
        print(f"为了避免被封，本次只修复前 {max_articles} 篇文章")
        problematic_articles = problematic_articles[:max_articles]
    
    # 显示将要修复的文章
    print("\\n将要修复的文章:")
    for i, article in enumerate(problematic_articles, 1):
        print(f"{i:2d}. {article['date']}: {article['title']}")
    
    # 确认是否继续
    response = input(f"\\n是否开始修复这 {len(problematic_articles)} 篇文章? (y/n): ")
    if response.lower() != 'y':
        print("操作已取消")
        return
    
    print("\\n开始修复...")
    crawler = PracticalCrawler()
    
    success_count = 0
    
    for i, article in enumerate(problematic_articles, 1):
        print(f"\\n修复第 {i}/{len(problematic_articles)} 篇:")
        print(f"日期: {article['date']}")
        print(f"标题: {article['title']}")
        
        try:
            success = crawler.fix_single_article(
                article['date'],
                article['page_no'],
                article['metadata']
            )
            
            if success:
                success_count += 1
                print(f"✓ 修复成功")
            else:
                print(f"✗ 修复失败")
                
        except Exception as e:
            print(f"✗ 修复出错: {e}")
            logger.error(f"修复文章出错: {e}")
        
        # 在文章之间添加额外的延迟
        if i < len(problematic_articles):
            extra_delay = random.uniform(30, 60)
            print(f"等待 {extra_delay:.1f}s 后继续...")
            time.sleep(extra_delay)
    
    print(f"\\n批量修复完成: {success_count}/{len(problematic_articles)} 篇文章修复成功")
    
    if success_count > 0:
        print("\\n建议:")
        print("1. 检查修复后的文章内容质量")
        print("2. 如果还有文章需要修复，请等待一段时间后再次运行")
        print("3. 可以考虑增加延迟时间来避免触发反爬虫机制")

if __name__ == "__main__":
    # 首次运行只修复5篇文章进行测试
    batch_fix_articles(max_articles=5)
