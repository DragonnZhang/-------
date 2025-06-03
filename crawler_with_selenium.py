#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人民邮电报数据爬虫 - 支持JavaScript渲染
使用Selenium处理需要JavaScript才能加载的页面
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
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

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RenminYoudianCrawlerWithJS:
    def __init__(self, use_selenium=True):
        self.base_url = "https://rmydb.cnii.com.cn/html"
        self.use_selenium = use_selenium
        
        if use_selenium:
            self.setup_driver()
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://rmydb.cnii.com.cn/'
            })
        
        # 创建数据存储目录
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def setup_driver(self):
        """设置Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 使用webdriver-manager自动管理ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                # 如果webdriver-manager不可用，尝试使用系统PATH中的chromedriver
                logger.warning("webdriver-manager不可用，尝试使用系统chromedriver")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.set_page_load_timeout(30)
            logger.info("Chrome WebDriver 初始化成功")
        except Exception as e:
            logger.error(f"Chrome WebDriver 初始化失败: {e}")
            logger.info("尝试使用requests模式...")
            self.use_selenium = False
            
    def generate_date_urls(self, year=2025, month=5):
        """生成指定年月的所有日期URL"""
        urls = []
        
        # 计算该月的天数
        if month in [1, 3, 5, 7, 8, 10, 12]:
            days = 31
        elif month in [4, 6, 9, 11]:
            days = 30
        elif month == 2:
            # 简单判断闰年
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                days = 29
            else:
                days = 28
        
        for day in range(1, days + 1):
            date_str = f"{year}{month:02d}{day:02d}"
            url = f"{self.base_url}/{year}/{date_str}/data.json"
            urls.append((date_str, url))
            
        return urls
    
    def download_data_with_selenium(self, date_str, url):
        """使用Selenium下载数据"""
        try:
            logger.info(f"使用Selenium下载: {date_str} - {url}")
            
            self.driver.get(url)
            
            # 等待页面加载完成或者检测到数据
            try:
                # 尝试等待页面出现JSON数据或者确认加载完成
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # 额外等待一下让JavaScript执行
                time.sleep(3)
                
                # 获取页面内容
                page_source = self.driver.page_source
                
                # 检查是否包含JavaScript错误页面
                if 'Please enable JavaScript' in page_source or '<!DOCTYPE' in page_source:
                    logger.warning(f"{date_str} 页面需要JavaScript处理，但未获取到JSON数据")
                    return False
                
                # 尝试解析JSON
                try:
                    # 如果页面直接返回JSON
                    page_text = self.driver.find_element(By.TAG_NAME, "pre").text
                    data = json.loads(page_text)
                except:
                    # 如果页面源代码中包含JSON
                    try:
                        data = json.loads(page_source)
                    except:
                        logger.warning(f"{date_str} 无法从页面中提取有效JSON数据")
                        return False
                
                if isinstance(data, list) and len(data) > 0:
                    logger.info(f"成功下载 {date_str}: {len(data)} 条数据")
                    
                    # 保存JSON数据
                    file_path = self.data_dir / f"{date_str}_data.json"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"已保存到: {file_path}")
                    return True
                else:
                    logger.warning(f"{date_str} 返回空数据或无效数据格式")
                    return False
                    
            except TimeoutException:
                logger.warning(f"{date_str} 页面加载超时")
                return False
                
        except WebDriverException as e:
            logger.error(f"Selenium处理失败 {date_str}: {e}")
            return False
        except Exception as e:
            logger.error(f"下载失败 {date_str}: {e}")
            return False
    
    def download_data_with_requests(self, date_str, url):
        """使用requests下载数据（作为备用方案）"""
        try:
            logger.info(f"使用requests下载: {date_str} - {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 尝试解析JSON
            try:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    logger.info(f"成功下载 {date_str}: {len(data)} 条数据")
                    
                    # 保存JSON数据
                    file_path = self.data_dir / f"{date_str}_data.json"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"已保存到: {file_path}")
                    return True
                else:
                    logger.warning(f"{date_str} 返回空数据或无效数据格式")
                    return False
                    
            except json.JSONDecodeError:
                # 检查是否返回HTML页面
                response_text = response.text.strip()
                if 'Please enable JavaScript' in response_text:
                    logger.warning(f"{date_str} 需要JavaScript，建议使用Selenium模式")
                else:
                    logger.warning(f"{date_str} 返回非JSON数据")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"requests下载失败 {date_str}: {e}")
            return False
        except Exception as e:
            logger.error(f"处理失败 {date_str}: {e}")
            return False
    
    def download_data(self, date_str, url):
        """下载单个data.json文件"""
        if self.use_selenium:
            return self.download_data_with_selenium(date_str, url)
        else:
            return self.download_data_with_requests(date_str, url)
    
    def crawl_month(self, year=2025, month=5):
        """爬取指定月份的所有数据"""
        logger.info(f"开始爬取 {year}年{month}月 的数据")
        logger.info(f"使用模式: {'Selenium' if self.use_selenium else 'Requests'}")

        urls = self.generate_date_urls(year, month)
        success_count = 0
        failed_count = 0
        success_dates = []
        failed_dates = []

        for date_str, url in urls:
            success = self.download_data(date_str, url)
            if success:
                success_count += 1
                success_dates.append(date_str)
            else:
                failed_count += 1
                failed_dates.append(date_str)

            # 添加延迟，避免请求过于频繁
            time.sleep(2)

        logger.info(f"爬取完成! 成功: {success_count}, 失败: {failed_count}")
        
        if success_dates:
            logger.info(f"成功下载的日期: {', '.join(success_dates)}")
        
        if failed_dates:
            logger.info(f"失败或无数据的日期: {', '.join(failed_dates)}")
            
        return success_count, failed_count
    
    def crawl_single_date(self, date_str):
        """爬取单个日期的数据"""
        year = int(date_str[:4])
        url = f"{self.base_url}/{year}/{date_str}/data.json"
        return self.download_data(date_str, url)
    
    def close(self):
        """关闭浏览器"""
        if self.use_selenium and hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("浏览器已关闭")

def main():
    """主函数"""
    print("开始运行人民邮电报数据爬虫（支持JavaScript）...")
    
    crawler = None
    try:
        # 优先尝试使用Selenium
        crawler = RenminYoudianCrawlerWithJS(use_selenium=True)
        
        # 先测试单个日期
        print("测试单个日期...")
        logger.info("测试单个日期...")
        test_success = crawler.crawl_single_date("20250603")
        
        if test_success:
            print("测试成功，开始爬取2025年5月的所有数据...")
            logger.info("测试成功，开始爬取2025年5月的所有数据...")
            crawler.crawl_month(2025, 5)
        else:
            print("测试失败，该日期可能无数据或需要其他处理方式")
            logger.warning("测试失败，该日期可能无数据或需要其他处理方式")
            
            # 如果是因为需要JavaScript而失败，可以尝试其他日期
            print("尝试爬取其他日期...")
            crawler.crawl_month(2025, 5)
            
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
