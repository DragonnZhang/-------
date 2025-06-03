#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实用的反爬虫解决方案 - 专注于有效性
"""

import requests
import json
import time
import random
from pathlib import Path
from datetime import datetime
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PracticalCrawler:
    def __init__(self):
        self.base_url = "https://rmydb.cnii.com.cn/html"
        self.session = requests.Session()
        
        # 设置更真实的请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        self.request_count = 0
        
    def smart_delay(self):
        """智能延迟策略"""
        self.request_count += 1
        
        # 基础延迟：30-60秒（增强生产环境设置）
        base_delay = random.uniform(30, 60)
        
        # 每10个请求后增加额外延迟 - 增强版
        if self.request_count % 10 == 0:
            extra_delay = random.uniform(120, 240)
            logger.info(f"第{self.request_count}个请求，额外等待 {extra_delay:.1f}s")
            time.sleep(extra_delay)
        
        logger.info(f"基础等待 {base_delay:.1f}s (请求#{self.request_count})")
        time.sleep(base_delay)
        
    def build_article_url(self, date_str, page_no, article_href):
        """构建文章URL"""
        year = date_str[:4]
        page_dir = f"{date_str}_{page_no}"
        url = f"{self.base_url}/{year}/{date_str}/{page_dir}/{article_href}"
        return url
        
    def fetch_article_content(self, url):
        """获取文章内容"""
        try:
            # 智能延迟
            self.smart_delay()
            
            logger.info(f"访问URL: {url}")
            
            # 发送请求
            response = self.session.get(url, timeout=30)
            
            logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                return self.parse_html_content(response.text)
            elif response.status_code == 491:
                logger.warning("收到491 Forbidden，需要更长时间等待")
                # 遇到491时等待更长时间
                time.sleep(random.uniform(60, 120))
                return None
            else:
                logger.warning(f"非200状态码: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("请求超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return None
            
    def parse_html_content(self, html_content):
        """解析HTML内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = {
            'title': None,
            'content': None,
            'publish_date': None,
            'author': None
        }
        
        # 提取标题
        title_element = soup.find('h1') or soup.find('title')
        if title_element:
            result['title'] = title_element.get_text().strip()
        
        # 提取主要内容 - 查找id="ozoom"的div
        content_div = soup.find('div', {'id': 'ozoom'})
        if content_div:
            # 移除脚本和样式标签
            for script in content_div(['script', 'style']):
                script.decompose()
            
            # 提取文本内容
            paragraphs = content_div.find_all('p')
            if paragraphs:
                content_parts = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 5:  # 过滤很短的段落
                        content_parts.append(text)
                result['content'] = '\n\n'.join(content_parts)
            else:
                # 如果没有段落，获取div的全部文本
                result['content'] = content_div.get_text().strip()
        
        # 如果没有找到内容，尝试其他方法
        if not result['content']:
            # 尝试找到主要内容区域
            main_content = soup.find('div', class_='article-content') or soup.find('article')
            if main_content:
                result['content'] = main_content.get_text().strip()
        
        # 设置默认值
        if not result['content']:
            result['content'] = '无内容'
        if not result['title']:
            result['title'] = '无标题'
            
        return result
        
    def fix_single_article(self, date_str, page_no, metadata):
        """修复单个文章"""
        article_href = metadata.get('articleHref')
        if not article_href:
            return False
            
        # 构建URL
        url = self.build_article_url(date_str, page_no, article_href)
        
        # 构建文件路径
        articles_dir = Path("articles")
        date_dir = articles_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = article_href.replace('.html', '.json')
        file_path = date_dir / file_name
        
        # 获取文章内容
        main_title = metadata.get('mainTitle', '未知标题')
        logger.info(f"修复文章: {main_title}")
        
        content = self.fetch_article_content(url)
        
        if content is None:
            logger.error(f"无法获取文章内容: {url}")
            return False
            
        # 检查内容质量
        if (content.get('title') == '491 Forbidden' or 
            content.get('content') == '无内容' or
            len(content.get('content', '')) < 50):
            logger.warning(f"获取的内容质量不佳: {content}")
            return False
        
        # 保存文章数据
        article_data = {
            'metadata': metadata,
            'content': content,
            'crawl_time': datetime.now().isoformat(),
            'source_url': url
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            logger.info(f"文章已保存: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存文章失败: {e}")
            return False

def test_fix_one_article():
    """测试修复一个已知问题文章"""
    print("开始测试实用爬虫...")
    
    # 测试文章信息
    test_article = {
        'date': '20250520',
        'page_no': '001', 
        'metadata': {
            "wordNumber": 765,
            "picAuthor": "",
            "mainTitle": "4月信息传输、软件和信息技术服务业生产指数同比增长10.4％",
            "issueNumber": "08582",
            "articleIssueDate": "2025-05-20",
            "articleColumn": "",
            "articleHref": "20250520_001_02_2642.html",
            "articleAuthor": "记者　苏德悦"
        }
    }
    
    crawler = PracticalCrawler()
    
    try:
        success = crawler.fix_single_article(
            test_article['date'],
            test_article['page_no'],
            test_article['metadata']
        )
        
        if success:
            print("✓ 测试成功!")
            
            # 检查保存的文件
            file_path = Path("articles") / test_article['date'] / "20250520_001_02_2642.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = data.get('content', {})
                    print(f"标题: {content.get('title', '无')}")
                    print(f"内容长度: {len(content.get('content', ''))}")
                    if content.get('content') and len(content.get('content', '')) > 100:
                        print(f"内容预览: {content.get('content', '')[:200]}...")
                        print("✓ 内容提取成功!")
                    else:
                        print("⚠ 内容可能仍有问题")
        else:
            print("✗ 测试失败")
            
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fix_one_article()
