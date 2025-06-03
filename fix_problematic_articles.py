#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复有问题的文章
"""

import json
import os
from pathlib import Path
import logging
# from improved_crawler import ImprovedArticleCrawler  # 暂时注释掉

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_articles.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_problematic_articles():
    """查找有问题的文章"""
    articles_dir = Path("articles")
    problematic_files = []
    
    for date_dir in articles_dir.iterdir():
        if date_dir.is_dir():
            for article_file in date_dir.glob("*.json"):
                try:
                    with open(article_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    content = data.get('content', {})
                    title = content.get('title', '')
                    article_content = content.get('content', '')
                    
                    # 检查是否有问题
                    is_problematic = (
                        article_content == '无内容' or
                        '491 Forbidden' in title or
                        '403 Forbidden' in title or
                        '404 Not Found' in title or
                        len(article_content.strip()) < 20  # 内容太短
                    )
                    
                    if is_problematic:
                        problematic_files.append({
                            'file_path': article_file,
                            'date': date_dir.name,
                            'metadata': data.get('metadata', {}),
                            'issue': f"标题: {title}, 内容长度: {len(article_content)}"
                        })
                        
                except Exception as e:
                    logger.error(f"读取文件失败 {article_file}: {e}")
    
    return problematic_files

def fix_article(crawler, problematic_info):
    """修复单个文章"""
    metadata = problematic_info['metadata']
    date = problematic_info['date']
    
    # 从文件名中提取页号
    article_href = metadata.get('articleHref', '')
    if not article_href:
        logger.error("无法获取文章链接")
        return False
    
    # 从articleHref中提取页号 (例如: 20250501_008_02_9479.html -> 008)
    parts = article_href.split('_')
    if len(parts) >= 2:
        page_no = parts[1]  # 008
    else:
        page_no = '001'  # 默认值
    
    logger.info(f"开始修复文章: {metadata.get('mainTitle', '未知')} (页号: {page_no})")
    
    # 重新爬取
    success = crawler.crawl_single_article(date, page_no, metadata)
    
    if success:
        logger.info(f"文章修复成功: {problematic_info['file_path']}")
    else:
        logger.error(f"文章修复失败: {problematic_info['file_path']}")
    
    return success

def main():
    """主函数"""
    print("查找有问题的文章...")
    try:
        problematic_files = find_problematic_articles()
        
        if not problematic_files:
            print("没有发现有问题的文章！")
            return
        
        print(f"发现 {len(problematic_files)} 篇有问题的文章:")
        for i, info in enumerate(problematic_files, 1):
            print(f"  {i}. {info['date']}: {info['metadata'].get('mainTitle', '未知')} - {info['issue']}")
        
        response = input(f"\n是否开始修复这 {len(problematic_files)} 篇文章？(y/n): ")
        if response.lower() != 'y':
            print("取消修复")
            return
        
        # 注释掉爬虫部分先测试查找功能
        print("修复功能暂时禁用，仅显示问题文章")
        
        # crawler = None
        # try:
        #     crawler = ImprovedArticleCrawler()
        #     
        #     success_count = 0
        #     for i, info in enumerate(problematic_files, 1):
        #         print(f"\n修复第 {i}/{len(problematic_files)} 篇文章...")
        #         if fix_article(crawler, info):
        #             success_count += 1
        #     
        #     print(f"\n修复完成: {success_count}/{len(problematic_files)} 篇文章修复成功")
        #     
        # except Exception as e:
        #     print(f"修复过程出错: {e}")
        #     logger.error(f"修复过程出错: {e}")
        #     import traceback
        #     traceback.print_exc()
        # finally:
        #     if crawler:
        #         crawler.close()
        
    except Exception as e:
        print(f"程序出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
