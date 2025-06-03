#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用的完整文章爬虫 - 用于爬取所有遗漏的文章
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
        logging.FileHandler('universal_crawler.log', encoding='utf-8'),
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
        
        # 获取所有文章的详细信息
        all_articles = []
        for page_data in data:
            page_no = page_data.get('pageNo', '001')
            articles = page_data.get('onePageArticleList', [])
            for article in articles:
                article['_page_no'] = page_no  # 添加页号信息
                all_articles.append(article)
        
        # 统计应有的文章数
        total_expected = len(all_articles)
        
        # 检查已爬取的文章
        date_articles_dir = articles_dir / date_str
        missing_articles = []
        
        if not date_articles_dir.exists():
            # 整个目录都不存在
            missing_articles = all_articles
        else:
            # 检查每篇文章
            for article in all_articles:
                article_href = article.get('articleHref', '')
                if article_href:
                    file_name = article_href.replace('.html', '.json')
                    file_path = date_articles_dir / file_name
                    
                    if not file_path.exists():
                        missing_articles.append(article)
                    else:
                        # 检查文件内容是否有效
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                article_data = json.load(f)
                            content = article_data.get('content', {})
                            title = content.get('title', '')
                            article_content = content.get('content', '')
                            
                            # 检查是否为无效内容
                            is_invalid = (
                                article_content == '无内容' or
                                '491 Forbidden' in title or
                                '403 Forbidden' in title or
                                '404 Not Found' in title or
                                len(article_content.strip()) < 20
                            )
                            
                            if is_invalid:
                                missing_articles.append(article)
                                
                        except Exception as e:
                            logger.warning(f"读取文件失败 {file_path}: {e}")
                            missing_articles.append(article)
        
        total_missing = len(missing_articles)
        if total_missing > 0:
            missing_info.append({
                'date': date_str,
                'expected': total_expected,
                'missing': total_missing,
                'missing_articles': missing_articles
            })
            
        logger.info(f"{date_str}: 应有{total_expected}篇, 遗漏{total_missing}篇")
    
    return missing_info

def crawl_missing_articles(missing_info):
    """爬取遗漏的文章"""
    crawler = None
    try:
        crawler = ImprovedArticleCrawler()
        
        total_success = 0
        total_attempts = 0
        
        for info in missing_info:
            date_str = info['date']
            missing_articles = info['missing_articles']
            
            logger.info(f"开始爬取 {date_str} 的 {len(missing_articles)} 篇遗漏文章")
            
            success_count = 0
            for i, article in enumerate(missing_articles, 1):
                page_no = article.get('_page_no', '001')
                main_title = article.get('mainTitle', '未知标题')
                
                logger.info(f"正在爬取 {date_str} 第 {i}/{len(missing_articles)} 篇: {main_title}")
                
                total_attempts += 1
                if crawler.crawl_single_article(date_str, page_no, article):
                    success_count += 1
                    total_success += 1
            
            logger.info(f"{date_str} 爬取完成: {success_count}/{len(missing_articles)}")
        
        logger.info(f"总体爬取完成: {total_success}/{total_attempts}")
        return total_success, total_attempts
        
    except Exception as e:
        logger.error(f"爬取过程失败: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0
    finally:
        if crawler:
            crawler.close()

def main():
    """主函数"""
    print("检查遗漏的文章...")
    missing_info = check_missing_articles()
    
    if missing_info:
        total_missing = sum(info['missing'] for info in missing_info)
        print(f"\n发现 {len(missing_info)} 个日期有遗漏文章:")
        print(f"总共遗漏 {total_missing} 篇文章")
        
        for info in missing_info:
            print(f"  {info['date']}: 遗漏 {info['missing']} 篇 (应有 {info['expected']} 篇)")
        
        response = input(f"\n是否开始爬取这 {total_missing} 篇遗漏文章？(y/n): ")
        if response.lower() == 'y':
            success, total = crawl_missing_articles(missing_info)
            print(f"\n爬取完成: {success}/{total} 篇文章成功")
        else:
            print("取消爬取")
    else:
        print("所有文章都已爬取完成且有效！")

if __name__ == "__main__":
    main()
