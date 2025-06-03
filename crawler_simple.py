#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人民邮电报数据爬虫 - 简化版本
专门处理JavaScript保护的网站
"""

import requests
import json
import time
from pathlib import Path
import logging
import re
import base64

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

class SimpleRenminYoudianCrawler:
    def __init__(self):
        self.base_url = "https://rmydb.cnii.com.cn/html"
        self.session = requests.Session()
        
        # 设置更真实的浏览器headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://rmydb.cnii.com.cn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"'
        })
        
        # 创建数据存储目录
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
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
    
    def try_decode_challenge_url(self, html_content):
        """尝试从JavaScript代码中解码真实的URL"""
        try:
            # 查找base64编码的路径
            base64_pattern = r"'([A-Za-z0-9+/=]{20,})'"
            matches = re.findall(base64_pattern, html_content)
            
            for match in matches:
                try:
                    decoded = base64.b64decode(match).decode('utf-8')
                    if 'data.json' in decoded:
                        logger.info(f"找到可能的真实路径: {decoded}")
                        return f"https://rmydb.cnii.com.cn{decoded}"
                except:
                    continue
                    
            # 查找其他可能的URL模式
            url_patterns = [
                r"url\s*[:=]\s*['\"]([^'\"]+data\.json[^'\"]*)['\"]",
                r"location\s*[:=]\s*['\"]([^'\"]+data\.json[^'\"]*)['\"]",
                r"href\s*[:=]\s*['\"]([^'\"]+data\.json[^'\"]*)['\"]"
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    logger.info(f"找到可能的URL: {matches[0]}")
                    return matches[0] if matches[0].startswith('http') else f"https://rmydb.cnii.com.cn{matches[0]}"
                    
        except Exception as e:
            logger.warning(f"解码URL失败: {e}")
            
        return None
    
    def download_data(self, date_str, url):
        """下载单个data.json文件"""
        try:
            logger.info(f"正在下载: {date_str} - {url}")
            
            # 首先访问原始URL
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 检查是否直接返回JSON
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"直接获取成功 {date_str}: {len(data)} 条数据")
                        self.save_data(date_str, data)
                        return True
                except json.JSONDecodeError:
                    pass
            
            # 如果返回HTML，尝试解析JavaScript保护
            html_content = response.text
            
            if 'Please enable JavaScript' in html_content:
                logger.info(f"{date_str} 检测到JavaScript保护，尝试解析...")
                
                # 尝试从HTML中提取真实URL
                real_url = self.try_decode_challenge_url(html_content)
                
                if real_url and real_url != url:
                    logger.info(f"尝试访问解码后的URL: {real_url}")
                    # 等待一下模拟JavaScript执行时间
                    time.sleep(2)
                    
                    real_response = self.session.get(real_url, timeout=30)
                    real_response.raise_for_status()
                    
                    try:
                        data = real_response.json()
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"解码URL成功 {date_str}: {len(data)} 条数据")
                            self.save_data(date_str, data)
                            return True
                    except json.JSONDecodeError:
                        logger.warning(f"{date_str} 解码URL也未返回有效JSON")
                
                # 如果解码失败，尝试模拟等待后重新请求
                logger.info(f"{date_str} 尝试等待后重新请求...")
                time.sleep(5)
                
                retry_response = self.session.get(url, timeout=30)
                try:
                    data = retry_response.json()
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"重试成功 {date_str}: {len(data)} 条数据")
                        self.save_data(date_str, data)
                        return True
                except json.JSONDecodeError:
                    pass
                
                logger.warning(f"{date_str} 无法绕过JavaScript保护")
                return False
            else:
                # 尝试解析非JavaScript保护的响应
                try:
                    data = json.loads(html_content)
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"解析HTML成功 {date_str}: {len(data)} 条数据")
                        self.save_data(date_str, data)
                        return True
                except json.JSONDecodeError:
                    logger.warning(f"{date_str} 返回的内容无法解析为JSON")
                    return False

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败 {date_str}: {e}")
            return False
        except Exception as e:
            logger.error(f"处理失败 {date_str}: {e}")
            return False
    
    def save_data(self, date_str, data):
        """保存数据到文件"""
        file_path = self.data_dir / f"{date_str}_data.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存到: {file_path}")
    
    def crawl_month(self, year=2025, month=5):
        """爬取指定月份的所有数据"""
        logger.info(f"开始爬取 {year}年{month}月 的数据")

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
            time.sleep(3)

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

def main():
    """主函数"""
    print("开始运行人民邮电报数据爬虫（简化版本）...")
    
    try:
        crawler = SimpleRenminYoudianCrawler()
        
        # 先测试单个日期
        print("测试单个日期...")
        logger.info("测试单个日期...")
        test_success = crawler.crawl_single_date("20250603")
        
        if test_success:
            print("测试成功，开始爬取2025年5月的所有数据...")
            logger.info("测试成功，开始爬取2025年5月的所有数据...")
            crawler.crawl_month(2025, 5)
        else:
            print("测试失败，但仍尝试爬取所有日期...")
            logger.warning("测试失败，但仍尝试爬取所有日期...")
            crawler.crawl_month(2025, 5)
            
    except Exception as e:
        print(f"程序执行出错: {e}")
        logger.error(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
