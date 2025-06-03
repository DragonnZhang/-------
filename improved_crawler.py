#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的文章内容爬虫 - 加强反爬虫对策
"""

import requests
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedArticleCrawler:
    def __init__(self):
        self.base_url = "https://rmydb.cnii.com.cn/html"
        self.setup_driver()
        
        # 创建文章存储目录
        self.articles_dir = Path("articles")
        self.articles_dir.mkdir(exist_ok=True)
        
        # 创建按日期分组的目录
        self.data_dir = Path("data")
        
        # 请求计数器和延迟控制
        self.request_count = 0
        self.max_requests_per_session = 50  # 每个会话最多请求数
        
    def setup_driver(self):
        """设置Chrome WebDriver with anti-detection"""
        try:
            chrome_options = Options()
            
            # 更隐蔽的浏览器配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 随机User-Agent
            user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 执行反检测脚本
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.set_page_load_timeout(60)
            logger.info("Chrome WebDriver 初始化成功")
        except Exception as e:
            logger.error(f"Chrome WebDriver 初始化失败: {e}")
            raise
    
    def build_article_url(self, date_str, page_no, article_href):
        """构建文章完整URL"""
        year = date_str[:4]
        page_dir = f"{date_str}_{page_no}"
        url = f"{self.base_url}/{year}/{date_str}/{page_dir}/{article_href}"
        return url
    
    def smart_delay(self):
        """智能延迟 - 根据请求数量调整延迟时间"""
        self.request_count += 1
        
        if self.request_count > self.max_requests_per_session:
            # 重新创建浏览器会话
            logger.info("达到最大请求数，重新创建浏览器会话")
            self.driver.quit()
            time.sleep(random.uniform(30, 60))  # 长时间休息
            self.setup_driver()
            self.request_count = 0
        
        # 根据请求数量动态调整延迟
        if self.request_count < 10:
            delay = random.uniform(2, 5)
        elif self.request_count < 25:
            delay = random.uniform(5, 10)
        else:
            delay = random.uniform(10, 20)
        
        logger.info(f"等待 {delay:.1f} 秒 (请求数: {self.request_count})")
        time.sleep(delay)
    
    def extract_article_content(self, url):
        """提取文章内容 - 增强错误处理"""
        max_retries = 3
        
        for retry in range(max_retries):
            try:
                logger.info(f"正在访问: {url} (尝试 {retry + 1}/{max_retries})")
                
                # 智能延迟
                self.smart_delay()
                
                # 访问页面
                self.driver.get(url)
                
                # 等待页面加载
                time.sleep(random.uniform(3, 6))
                
                # 检查是否被重定向或返回错误页面
                current_url = self.driver.current_url
                if current_url != url:
                    logger.warning(f"页面被重定向: {current_url}")
                
                # 检查页面标题是否包含错误信息
                page_title = self.driver.title
                if any(error in page_title.lower() for error in ['403', '404', '500', 'forbidden', 'error']):
                    logger.warning(f"检测到错误页面标题: {page_title}")
                    if retry < max_retries - 1:
                        logger.info(f"等待更长时间后重试...")
                        time.sleep(random.uniform(30, 60))
                        continue
                
                # 获取页面HTML
                html_content = self.driver.page_source
                
                # 检查HTML内容是否包含错误信息
                if any(error in html_content.lower() for error in ['403 forbidden', '404 not found', '500 internal server error']):
                    logger.warning("页面内容包含错误信息")
                    if retry < max_retries - 1:
                        logger.info("等待后重试...")
                        time.sleep(random.uniform(20, 40))
                        continue
                
                # 解析HTML
                return self.parse_article_html(html_content)
                
            except TimeoutException:
                logger.warning(f"页面加载超时 (尝试 {retry + 1}/{max_retries})")
                if retry < max_retries - 1:
                    time.sleep(random.uniform(15, 30))
            except Exception as e:
                logger.error(f"提取文章内容失败 (尝试 {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(random.uniform(10, 20))
        
        logger.error(f"所有重试都失败了: {url}")
        return None
    
    def parse_article_html(self, html_content):
        """解析HTML内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        article_info = {
            'title': None,
            'content': None,
            'publish_date': None,
            'author': None
        }
        
        # 提取标题
        title_selectors = ['h1', '.title', '.article-title', '#title']
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                article_info['title'] = title_element.get_text().strip()
                break
        
        # 提取内容 - 优先查找 id="ozoom" 的div
        content = None
        ozoom_div = soup.find('div', {'id': 'ozoom'})
        if ozoom_div:
            # 移除script和style标签
            for script in ozoom_div(["script", "style"]):
                script.decompose()
            
            # 提取所有段落文本
            paragraphs = ozoom_div.find_all('p')
            if paragraphs:
                content_parts = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 10:  # 过滤太短的段落
                        content_parts.append(text)
                content = '\n\n'.join(content_parts)
            else:
                # 如果没有段落，直接获取div中的文本
                content = ozoom_div.get_text().strip()
        
        # 如果没有找到ozoom div，尝试其他选择器
        if not content:
            content_selectors = [
                '.article-content',
                '.content',
                '#content',
                '.article-body',
                '.text-content',
                'article',
                '.main-content'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # 移除script和style标签
                    for script in content_element(["script", "style"]):
                        script.decompose()
                    content = content_element.get_text().strip()
                    break
        
        article_info['content'] = content or '无内容'
        
        # 提取发布日期
        date_selectors = ['.publish-date', '.date', '.article-date', 'time']
        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                article_info['publish_date'] = date_element.get_text().strip()
                break
        
        # 提取作者
        author_selectors = ['.author', '.article-author', '.byline']
        for selector in author_selectors:
            author_element = soup.select_one(selector)
            if author_element:
                article_info['author'] = author_element.get_text().strip()
                break
        
        return article_info
    
    def crawl_single_article(self, date_str, page_no, article_metadata):
        """爬取单篇文章"""
        article_href = article_metadata.get('articleHref')
        if not article_href:
            logger.warning("文章链接为空")
            return False
        
        # 构建文章URL
        url = self.build_article_url(date_str, page_no, article_href)
        
        # 构建文件路径
        date_dir = self.articles_dir / date_str
        date_dir.mkdir(exist_ok=True)
        
        # 从articleHref中提取文件名（去掉.html后缀）
        file_name = article_href.replace('.html', '.json')
        file_path = date_dir / file_name
        
        # 如果文件已存在且内容不是错误的，跳过
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_content = existing_data.get('content', {})
                    if (existing_content.get('content') != '无内容' and 
                        existing_content.get('title') != '491 Forbidden' and
                        existing_content.get('content')):
                        logger.info(f"文章已存在且有效，跳过: {file_path}")
                        return True
            except:
                pass
        
        # 提取文章内容
        main_title = article_metadata.get('mainTitle', '未知标题')
        logger.info(f"正在爬取文章: {main_title} - {url}")
        
        article_content = self.extract_article_content(url)
        
        if article_content is None:
            logger.error(f"无法提取文章内容: {url}")
            return False
        
        # 组装完整的文章数据
        article_data = {
            'metadata': article_metadata,
            'content': article_content,
            'crawl_time': datetime.now().isoformat(),
            'source_url': url
        }
        
        # 保存文章数据
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            logger.info(f"文章已保存: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存文章失败: {e}")
            return False
    
    def crawl_articles_from_json(self, json_file_path, start_from_article=0):
        """从JSON文件爬取文章"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取日期
            date_str = Path(json_file_path).stem.replace('_data', '')
            logger.info(f"开始爬取 {date_str} 的文章 (从第 {start_from_article + 1} 篇开始)")
            
            success_count = 0
            total_articles = 0
            current_article_index = 0
            
            for page_data in data:
                page_no = page_data.get('pageNo', '001')
                articles = page_data.get('onePageArticleList', [])
                
                for article in articles:
                    if current_article_index < start_from_article:
                        current_article_index += 1
                        continue
                    
                    total_articles += 1
                    
                    if self.crawl_single_article(date_str, page_no, article):
                        success_count += 1
                    
                    current_article_index += 1
            
            logger.info(f"{date_str} 爬取完成: 成功 {success_count}/{total_articles}")
            return success_count, total_articles
            
        except Exception as e:
            logger.error(f"处理JSON文件失败 {json_file_path}: {e}")
            return 0, 0
    
    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("浏览器已关闭")

def main():
    """主函数 - 修复5月1日的文章"""
    print("开始修复5月1日的文章...")
    
    crawler = None
    try:
        crawler = ImprovedArticleCrawler()
        
        # 专门修复5月1日的文章
        json_file = Path("data/20250501_data.json")
        if json_file.exists():
            # 从第11篇开始爬取（前10篇已经有了）
            success, total = crawler.crawl_articles_from_json(json_file, start_from_article=10)
            print(f"5月1日修复结果: {success}/{total}")
        else:
            print("未找到5月1日数据文件")
            
    except Exception as e:
        print(f"程序执行出错: {e}")
        logger.error(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if crawler:
            crawler.close()

if __name__ == "__main__":
    main()
