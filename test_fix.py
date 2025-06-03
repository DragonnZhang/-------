#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复脚本 - 只修复5月1日的2篇问题文章
"""

import json
import os
from pathlib import Path
import logging
from improved_crawler import ImprovedArticleCrawler

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_fix.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """测试修复5月1日的2篇问题文章"""
    print("测试修复5月1日的问题文章...")
    
    # 手动指定要修复的文章
    problematic_articles = [
        {
            'date': '20250501',
            'page_no': '008',
            'metadata': {
                "wordNumber": 494,
                "picAuthor": "",
                "mainTitle": "国际电信联盟无线电通信部门第四研究组相关工作组会议在上海开幕（附图片）",
                "issueNumber": "08572",
                "articleIssueDate": "2025-05-01",
                "articleColumn": "",
                "articleHref": "20250501_008_01_5438.html",
                "articleAuthor": "帅又榕"
            }
        },
        {
            'date': '20250501',
            'page_no': '008',
            'metadata': {
                "wordNumber": 872,
                "picAuthor": "",
                "mainTitle": "南平市无管局保障福建省文旅经济发展大会无线电安全",
                "issueNumber": "08572",
                "articleIssueDate": "2025-05-01",
                "articleColumn": "",
                "articleHref": "20250501_008_02_9479.html",
                "articleAuthor": "白静波"
            }
        }
    ]
    
    crawler = None
    try:
        print("初始化爬虫...")
        crawler = ImprovedArticleCrawler()
        
        success_count = 0
        for i, article_info in enumerate(problematic_articles, 1):
            print(f"\n修复第 {i}/{len(problematic_articles)} 篇文章...")
            print(f"标题: {article_info['metadata']['mainTitle']}")
            
            success = crawler.crawl_single_article(
                article_info['date'], 
                article_info['page_no'], 
                article_info['metadata']
            )
            
            if success:
                success_count += 1
                print(f"✓ 修复成功")
            else:
                print(f"✗ 修复失败")
        
        print(f"\n测试完成: {success_count}/{len(problematic_articles)} 篇文章修复成功")
        
    except Exception as e:
        print(f"测试过程出错: {e}")
        logger.error(f"测试过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if crawler:
            crawler.close()

if __name__ == "__main__":
    main()
