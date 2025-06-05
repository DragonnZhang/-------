#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实用的反爬虫解决方案 - 基于Selenium的强化版本
"""

import json
import time
import random
from pathlib import Path
from datetime import datetime
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

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('practical_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PracticalCrawler:
    def __init__(self):
        self.base_url = "https://rmydb.cnii.com.cn/html"
        self.setup_driver()
        self.request_count = 0
        self.max_requests_per_session = 15  # 每个会话最多请求数

    def setup_driver(self):
        """设置Chrome WebDriver with anti-detection"""
        try:
            chrome_options = Options()

            # 更隐蔽的浏览器配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(
                '--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)

            # 随机User-Agent
            user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(
                f'--user-agent={random.choice(user_agents)}')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)

            # 执行反检测脚本
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.driver.set_page_load_timeout(60)
            logger.info("Chrome WebDriver 初始化成功")
        except Exception as e:
            logger.error(f"Chrome WebDriver 初始化失败: {e}")
            raise

    def smart_delay(self):
        """智能延迟策略 - 基于Selenium的增强版"""
        self.request_count += 1

        if self.request_count > self.max_requests_per_session:
            # 重新创建浏览器会话
            logger.info("达到最大请求数，重新创建浏览器会话")
            self.driver.quit()
            time.sleep(random.uniform(120, 180))  # 长时间休息 2-3分钟
            self.setup_driver()
            self.request_count = 0

        # 根据请求数量动态调整延迟
        if self.request_count < 8:
            delay = random.uniform(60, 90)  # 60-90秒的随机值
        elif self.request_count < 15:
            delay = random.uniform(70, 100)  # 70-100秒的随机值
        else:
            delay = random.uniform(80, 120)  # 80-120秒的随机值

        logger.info(f"等待 {delay:.1f} 秒 (请求数: {self.request_count})")
        time.sleep(delay)

    def build_article_url(self, date_str, page_no, article_href):
        """构建文章URL"""
        year = date_str[:4]
        page_dir = f"{date_str}_{page_no}"
        url = f"{self.base_url}/{year}/{date_str}/{page_dir}/{article_href}"
        return url

    def fetch_article_content(self, url):
        """获取文章内容 - 基于Selenium的增强版"""
        max_retries = 3

        for retry in range(max_retries):
            try:
                logger.info(f"正在访问: {url} (尝试 {retry + 1}/{max_retries})")

                # 智能延迟
                self.smart_delay()

                # 访问页面
                self.driver.get(url)

                # 等待页面加载
                time.sleep(random.uniform(8, 15))

                # 检查是否被重定向或返回错误页面
                current_url = self.driver.current_url
                if current_url != url:
                    logger.warning(f"页面被重定向: {current_url}")

                # 获取页面HTML
                html_content = self.driver.page_source

                # 检查HTML内容是否包含错误信息
                if any(error in html_content.lower() for error in ['403 forbidden', '404 not found', '500 internal server error', '491 forbidden']):
                    logger.warning("页面内容包含错误信息")
                    if retry < max_retries - 1:
                        logger.info("等待后重试...")
                        time.sleep(random.uniform(60, 120))
                        continue

                # 解析HTML
                return self.parse_html_content(html_content)

            except TimeoutException:
                logger.warning(f"页面加载超时 (尝试 {retry + 1}/{max_retries})")
                if retry < max_retries - 1:
                    time.sleep(random.uniform(30, 60))
            except Exception as e:
                logger.error(f"获取文章内容失败 (尝试 {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(random.uniform(20, 40))

        logger.error(f"所有重试都失败了: {url}")
        return None

    def parse_html_content(self, html_content):
        """解析HTML内容 - 增强版"""
        soup = BeautifulSoup(html_content, 'html.parser')

        result = {
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
                result['title'] = title_element.get_text().strip()
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

        result['content'] = content or '无内容'

        # 提取发布日期
        date_selectors = ['.publish-date', '.date', '.article-date', 'time']
        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                result['publish_date'] = date_element.get_text().strip()
                break

        # 提取作者
        author_selectors = ['.author', '.article-author', '.byline']
        for selector in author_selectors:
            author_element = soup.select_one(selector)
            if author_element:
                result['author'] = author_element.get_text().strip()
                break

        # 设置默认标题
        if not result['title']:
            result['title'] = '无标题'

        return result

    def fix_single_article(self, date_str, page_no, metadata):
        """修复单个文章 - 基于Selenium的增强版"""
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

        # 如果文件已存在且内容不是错误的，跳过
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_content = existing_data.get('content', {})
                    if (existing_content.get('content') != '无内容' and
                        existing_content.get('title') != '491 Forbidden' and
                        existing_content.get('content') and
                            len(existing_content.get('content', '')) > 50):
                        logger.info(f"文章已存在且有效，跳过: {file_path}")
                        return True
            except:
                pass

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
                len(content.get('content', '')) < 5):
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

    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("浏览器已关闭")


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
            file_path = Path("articles") / \
                test_article['date'] / "20250520_001_02_2642.json"
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
