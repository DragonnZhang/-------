#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版文章爬虫测试
"""

import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path
import time

def test_single_article():
    """测试单篇文章爬取"""
    
    # 读取第一个JSON文件中的文章信息
    with open('data/20250501_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取第一篇文章
    first_page = data[0]
    first_article = first_page['onePageArticleList'][0]
    
    date_str = "20250501"
    page_no = first_page['pageNo']
    article_href = first_article['articleHref']
    
    print(f"测试文章:")
    print(f"  标题: {first_article['mainTitle']}")
    print(f"  作者: {first_article['articleAuthor']}")
    print(f"  字数: {first_article['wordNumber']}")
    print(f"  链接: {article_href}")
    
    # 构建完整URL
    base_url = "https://rmydb.cnii.com.cn/html"
    year = date_str[:4]
    page_dir = f"{date_str}_{page_no}"
    url = f"{base_url}/{year}/{date_str}/{page_dir}/{article_href}"
    
    print(f"\\n完整URL: {url}")
    
    # 请求页面
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print("\\n正在获取文章内容...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print("✅ 页面获取成功")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else '无标题'
            if '_人民邮电报' in title:
                title = title.replace('_人民邮电报', '')
            
            print(f"页面标题: {title}")
            
            # 提取正文内容
            ozoom_div = soup.find('div', {'id': 'ozoom'})
            if ozoom_div:
                print("✅ 找到文章内容区域 (ozoom)")
                
                # 提取段落
                paragraphs = ozoom_div.find_all('p')
                content_parts = []
                
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text:
                        content_parts.append(text)
                
                content = '\\n\\n'.join(content_parts)
                
                print(f"内容段落数: {len(content_parts)}")
                print(f"内容总长度: {len(content)} 字符")
                print(f"\\n内容预览 (前500字符):")
                print(content[:500])
                print("..." if len(content) > 500 else "")
                
                # 保存文章到文件
                article_data = {
                    'metadata': first_article,
                    'url': url,
                    'title': title,
                    'content': content,
                    'paragraphs': content_parts,
                    'content_length': len(content),
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 创建articles目录
                articles_dir = Path('articles')
                articles_dir.mkdir(exist_ok=True)
                
                # 保存文件
                filename = article_href.replace('.html', '.json')
                filepath = articles_dir / f"test_{filename}"
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(article_data, f, ensure_ascii=False, indent=2)
                
                print(f"\\n✅ 文章已保存到: {filepath}")
                
                return True
            else:
                print("❌ 未找到文章内容区域")
                return False
        else:
            print(f"❌ 页面获取失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False

def test_multiple_articles(max_count=5):
    """测试多篇文章爬取"""
    
    print(f"\\n=== 测试多篇文章爬取 (最多{max_count}篇) ===")
    
    # 读取JSON文件
    with open('data/20250501_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    date_str = "20250501"
    success_count = 0
    total_count = 0
    
    for page_data in data:
        if total_count >= max_count:
            break
            
        page_no = page_data['pageNo']
        articles = page_data['onePageArticleList']
        
        for article in articles:
            if total_count >= max_count:
                break
                
            total_count += 1
            
            print(f"\\n--- 文章 {total_count}: {article['mainTitle']} ---")
            
            article_href = article['articleHref']
            base_url = "https://rmydb.cnii.com.cn/html"
            year = date_str[:4]
            page_dir = f"{date_str}_{page_no}"
            url = f"{base_url}/{year}/{date_str}/{page_dir}/{article_href}"
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    ozoom_div = soup.find('div', {'id': 'ozoom'})
                    
                    if ozoom_div:
                        paragraphs = ozoom_div.find_all('p')
                        content_length = sum(len(p.get_text()) for p in paragraphs)
                        
                        print(f"✅ 成功 - {len(paragraphs)}段落, {content_length}字符")
                        success_count += 1
                        
                        # 保存文章
                        content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                        article_data = {
                            'metadata': article,
                            'url': url,
                            'content': '\\n\\n'.join(content_parts),
                            'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        articles_dir = Path('articles')
                        articles_dir.mkdir(exist_ok=True)
                        filename = article_href.replace('.html', '.json')
                        filepath = articles_dir / f"{date_str}_{filename}"
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(article_data, f, ensure_ascii=False, indent=2)
                    else:
                        print("❌ 未找到内容")
                else:
                    print(f"❌ 状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 错误: {e}")
            
            # 添加延迟
            time.sleep(1)
    
    print(f"\\n=== 测试完成 ===")
    print(f"总计: {total_count} 篇")
    print(f"成功: {success_count} 篇")
    print(f"成功率: {success_count/total_count*100:.1f}%")

if __name__ == "__main__":
    print("=== 人民邮电报文章爬虫测试 ===")
    
    # 测试单篇文章
    success = test_single_article()
    
    if success:
        # 测试多篇文章
        test_multiple_articles(5)
    else:
        print("\\n单篇文章测试失败，请检查网络连接或URL格式")
