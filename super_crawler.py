#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超强化反爬虫解决方案
采用多种技术绕过反爬虫检测
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
import subprocess
import platform

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('super_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SuperAntiDetectionCrawler:
    def __init__(self):
        self.base_url = "https://rmydb.cnii.com.cn/html"
        self.setup_session()
        self.setup_driver_pool()
        
        # 创建文章存储目录
        self.articles_dir = Path("articles")
        self.articles_dir.mkdir(exist_ok=True)
        
        # 请求统计
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        
        # 动态延迟参数
        self.base_delay = 3
        self.max_delay = 60
        self.current_delay = self.base_delay
        
    def setup_session(self):
        """设置requests会话"""
        self.session = requests.Session()
        
        # 更真实的请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # 用户代理池
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0'
        ]
        
    def rotate_user_agent(self):
        """轮换用户代理"""
        self.headers['User-Agent'] = random.choice(self.user_agents)
        
    def setup_driver_pool(self):
        """设置WebDriver池"""
        self.drivers = []
        self.current_driver_index = 0
        
    def create_new_driver(self):
        """创建新的WebDriver实例"""
        try:
            chrome_options = Options()
            
            # 更隐蔽的配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # 禁用图片加载以提高速度
            chrome_options.add_argument('--disable-javascript')  # 禁用JavaScript以提高速度
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 随机用户代理
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
            
            # 随机窗口大小
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            chrome_options.add_argument(f'--window-size={width},{height}')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 执行反检测脚本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']})")
            
            driver.set_page_load_timeout(30)
            logger.info("新WebDriver创建成功")
            return driver
        except Exception as e:
            logger.error(f"创建WebDriver失败: {e}")
            return None
            
    def get_driver(self):
        """获取可用的WebDriver"""
        if not self.drivers:
            driver = self.create_new_driver()
            if driver:
                self.drivers.append(driver)
            return driver
        
        # 轮换使用不同的driver
        driver = self.drivers[self.current_driver_index]
        self.current_driver_index = (self.current_driver_index + 1) % len(self.drivers)
        return driver
        
    def adaptive_delay(self, success=True):
        """自适应延迟策略"""
        if success:
            # 成功时减少延迟
            self.current_delay = max(self.base_delay, self.current_delay * 0.9)
            self.success_count += 1
        else:
            # 失败时增加延迟
            self.current_delay = min(self.max_delay, self.current_delay * 1.5)
            self.fail_count += 1
        
        # 添加随机性
        actual_delay = self.current_delay + random.uniform(0, self.current_delay * 0.3)
        
        logger.info(f"等待 {actual_delay:.1f}s (成功率: {self.success_count}/{self.request_count})")
        time.sleep(actual_delay)
        
    def build_article_url(self, date_str, page_no, article_href):
        """构建文章完整URL"""
        year = date_str[:4]
        page_dir = f"{date_str}_{page_no}"
        url = f"{self.base_url}/{year}/{date_str}/{page_dir}/{article_href}"
        return url
        
    def extract_with_requests(self, url):
        """使用requests方式提取内容"""
        try:
            self.rotate_user_agent()
            self.session.headers.update(self.headers)
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return self.parse_article_html(response.text)
            else:
                logger.warning(f"Requests方式返回状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Requests方式失败: {e}")
            return None
            
    def extract_with_selenium(self, url):
        """使用Selenium方式提取内容"""
        driver = self.get_driver()
        if not driver:
            return None
            
        try:
            driver.get(url)
            time.sleep(random.uniform(2, 5))
            
            # 检查页面标题
            page_title = driver.title
            if any(error in page_title.lower() for error in ['403', '404', '500', 'forbidden', 'error']):
                logger.warning(f"检测到错误页面: {page_title}")
                return None
                
            html_content = driver.page_source
            return self.parse_article_html(html_content)
            
        except Exception as e:
            logger.error(f"Selenium方式失败: {e}")
            return None
            
    def extract_article_content(self, url):
        """多策略提取文章内容"""
        self.request_count += 1
        methods = ['requests', 'selenium']
        
        for method in methods:
            try:
                logger.info(f"尝试使用{method}方式访问: {url}")
                
                if method == 'requests':
                    result = self.extract_with_requests(url)
                else:
                    result = self.extract_with_selenium(url)
                    
                if result and result.get('content') and len(result.get('content', '')) > 100:
                    logger.info(f"{method}方式成功!")
                    self.adaptive_delay(success=True)
                    return result
                else:
                    logger.warning(f"{method}方式内容不足")
                    
            except Exception as e:
                logger.error(f"{method}方式异常: {e}")
                
            # 失败后等待
            self.adaptive_delay(success=False)
            
        logger.error(f"所有方式都失败了: {url}")
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
                    if text and len(text) > 10:
                        content_parts.append(text)
                content = '\n\n'.join(content_parts)
            else:
                content = ozoom_div.get_text().strip()
        
        # 如果没有找到ozoom div，尝试其他选择器
        if not content:
            content_selectors = [
                '.article-content', '.content', '#content',
                '.article-body', '.text-content', 'article', '.main-content'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    for script in content_element(["script", "style"]):
                        script.decompose()
                    content = content_element.get_text().strip()
                    break
        
        article_info['content'] = content or '无内容'
        
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
        
        file_name = article_href.replace('.html', '.json')
        file_path = date_dir / file_name
        
        # 检查是否已存在有效内容
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_content = existing_data.get('content', {})
                    if (existing_content.get('content') != '无内容' and 
                        existing_content.get('title') != '491 Forbidden' and
                        existing_content.get('content') and
                        len(existing_content.get('content', '')) > 100):
                        logger.info(f"文章已存在且有效，跳过: {file_path}")
                        return True
            except:
                pass
        
        # 提取文章内容
        main_title = article_metadata.get('mainTitle', '未知标题')
        logger.info(f"正在爬取文章: {main_title}")
        
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
    
    def close(self):
        """关闭所有资源"""
        for driver in self.drivers:
            try:
                driver.quit()
            except:
                pass
        self.session.close()
        logger.info("所有资源已关闭")

def test_single_problematic_article():
    """测试单个问题文章"""
    print("开始测试超强化反爬虫解决方案...")
    
    # 选择一个已知的问题文章进行测试
    test_article = {
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
    }
    
    crawler = None
    try:
        print("初始化超强化爬虫...")
        crawler = SuperAntiDetectionCrawler()
        
        print(f"测试文章: {test_article['metadata']['mainTitle']}")
        
        success = crawler.crawl_single_article(
            test_article['date'],
            test_article['page_no'],
            test_article['metadata']
        )
        
        if success:
            print("✓ 测试成功!")
            
            # 检查文件内容
            file_path = Path("articles") / test_article['date'] / "20250501_008_01_5438.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = data.get('content', {})
                    print(f"标题: {content.get('title', '未知')}")
                    print(f"内容长度: {len(content.get('content', ''))}")
                    print(f"内容预览: {content.get('content', '')[:200]}...")
        else:
            print("✗ 测试失败")
            
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if crawler:
            crawler.close()

if __name__ == "__main__":
    test_single_problematic_article()
