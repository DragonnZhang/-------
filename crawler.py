#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人民邮电报数据爬虫
爬取2025年5月的所有data.json文件
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

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


class RenminYoudianCrawler:
    def __init__(self):
        self.base_url = "https://rmydb.cnii.com.cn/html"
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

    def download_data(self, date_str, url):
        """下载单个data.json文件"""
        try:
            logger.info(f"正在下载: {date_str} - {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # 检查响应内容类型
            content_type = response.headers.get('content-type', '').lower()
            
            # 尝试解析JSON
            try:
                data = response.json()
                
                # 检查是否是有效的新闻数据
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
                if response_text.startswith('<!DOCTYPE') or '<html' in response_text.lower():
                    if 'Please enable JavaScript' in response_text:
                        logger.warning(f"{date_str} 需要JavaScript，可能该日期无数据或需要浏览器访问")
                    else:
                        logger.warning(f"{date_str} 返回HTML页面而非JSON数据")
                    return False
                else:
                    logger.error(f"{date_str} 返回未知格式数据: {response_text[:100]}...")
                    return False

        except requests.exceptions.RequestException as e:
            logger.error(f"下载失败 {date_str}: {e}")
            return False
        except Exception as e:
            logger.error(f"处理失败 {date_str}: {e}")
            return False

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
            time.sleep(1)

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
    print("开始运行人民邮电报数据爬虫...")

    try:
        crawler = RenminYoudianCrawler()

        # 先测试单个日期
        print("测试单个日期...")
        logger.info("测试单个日期...")
        test_success = crawler.crawl_single_date("20250603")

        if test_success:
            print("测试成功，开始爬取2025年5月的所有数据...")
            logger.info("测试成功，开始爬取2025年5月的所有数据...")
            crawler.crawl_month(2025, 5)
        else:
            print("测试失败，请检查网络连接或URL格式")
            logger.error("测试失败，请检查网络连接或URL格式")
    except Exception as e:
        print(f"程序执行出错: {e}")
        logger.error(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
