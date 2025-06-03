#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单个文章URL的页面结构
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

def test_article_url():
    """测试文章URL结构"""
    
    # 从已下载的数据中获取一个真实的articleHref
    with open('data/20250501_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取第一个文章的信息
    first_page = data[0]
    first_article = first_page['onePageArticleList'][0]
    
    date_str = "20250501"
    page_no = first_page['pageNo']
    article_href = first_article['articleHref']
    
    print(f"测试文章信息:")
    print(f"  标题: {first_article['mainTitle']}")
    print(f"  页面: {page_no}")
    print(f"  文件: {article_href}")
    
    # 构建URL
    base_url = "https://rmydb.cnii.com.cn/html"
    year = date_str[:4]
    page_dir = f"{date_str}_{page_no}"
    url = f"{base_url}/{year}/{date_str}/{page_dir}/{article_href}"
    
    print(f"\\n构建的URL: {url}")
    
    # 测试访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        print("\\n正在访问URL...")
        response = requests.get(url, headers=headers, timeout=15)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 保存原始HTML以供分析
            with open('test_article.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("已保存原始HTML到 test_article.html")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print(f"\\n页面分析:")
            print(f"  页面标题: {soup.title.string if soup.title else '无标题'}")
            
            # 查找常见的文章内容区域
            content_selectors = [
                '.article-content', '.content', '#content', 
                '.article-body', '.text-content', 'article',
                '.main-content', '.article-text'
            ]
            
            found_content = False
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"  找到内容区域: {selector} ({len(elements)}个)")
                    content = elements[0].get_text()[:200]
                    print(f"  内容预览: {content}...")
                    found_content = True
                    break
            
            if not found_content:
                print("  未找到明确的内容区域，尝试分析body结构...")
                body = soup.find('body')
                if body:
                    # 显示body中的主要标签
                    tags = {}
                    for tag in body.find_all(True):
                        if tag.name in tags:
                            tags[tag.name] += 1
                        else:
                            tags[tag.name] = 1
                    
                    print(f"  Body中的标签统计: {dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10])}")
                    
                    # 尝试提取所有文本
                    all_text = body.get_text()[:500]
                    print(f"  页面文本预览: {all_text}...")
        else:
            print(f"访问失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"访问出错: {e}")

if __name__ == "__main__":
    test_article_url()
