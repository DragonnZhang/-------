#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充爬取所有遗漏的文章内容
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
        logging.FileHandler('complete_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_missing_articles():
    """检查每个日期遗漏的文章"""
    data_dir = Path("data")
    articles_dir = Path("articles")
    
    missing_info = []
    
    for json_file in sorted(data_dir.glob("*.json")):
        date_str = json_file.stem.replace('_data', '')
        
        # 读取JSON数据
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 统计应有的文章数
        total_expected = 0
        for page_data in data:
            total_expected += len(page_data.get('onePageArticleList', []))
        
        # 统计已爬取的文章数
        date_articles_dir = articles_dir / date_str
        if date_articles_dir.exists():
            total_crawled = len(list(date_articles_dir.glob("*.json")))
        else:
            total_crawled = 0
        
        missing_count = total_expected - total_crawled
        if missing_count > 0:
            missing_info.append({
                'date': date_str,
                'expected': total_expected,
                'crawled': total_crawled,
                'missing': missing_count
            })
            
        logger.info(f"{date_str}: 应有{total_expected}篇, 已爬{total_crawled}篇, 遗漏{missing_count}篇")
    
    return missing_info

def crawl_missing_articles(missing_info):
    """爬取遗漏的文章"""
    crawler = None
    try:
        crawler = ImprovedArticleCrawler()
        
        for info in missing_info:
            date_str = info['date']
            logger.info(f"开始补充爬取 {date_str} 的遗漏文章")
            
            json_file = Path(f"data/{date_str}_data.json")
            if json_file.exists():
                # 爬取所有遗漏的文章
                success, total = crawler.crawl_articles_from_json(json_file)
                logger.info(f"{date_str} 补充爬取完成: {success}/{total}")
            
    except Exception as e:
        logger.error(f"补充爬取失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if crawler:
            crawler.close()

def main():
    """主函数"""
    print("检查遗漏的文章...")
    try:
        missing_info = check_missing_articles()
        
        if missing_info:
            print(f"\n发现 {len(missing_info)} 个日期有遗漏文章:")
            total_missing = sum(info['missing'] for info in missing_info)
            print(f"总共遗漏 {total_missing} 篇文章")
            
            for info in missing_info:
                print(f"  {info['date']}: 遗漏 {info['missing']} 篇")
            
            response = input("\n是否开始补充爬取？(y/n): ")
            if response.lower() == 'y':
                crawl_missing_articles(missing_info)
            else:
                print("取消爬取")
        else:
            print("所有文章都已爬取完成！")
    except Exception as e:
        print(f"程序出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
