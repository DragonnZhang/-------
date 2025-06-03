#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试URL返回内容
"""

import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_with_requests():
    """使用requests测试"""
    print("=== 使用requests测试 ===")
    url = "https://rmydb.cnii.com.cn/html/2025/20250501/data.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://rmydb.cnii.com.cn/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        content = response.text[:500]  # 只显示前500字符
        print(f"内容类型: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"响应内容(前500字符):\n{content}")
        
        # 检查是否是JSON
        try:
            data = response.json()
            print(f"JSON解析成功，数据类型: {type(data)}")
            if isinstance(data, list):
                print(f"列表长度: {len(data)}")
            elif isinstance(data, dict):
                print(f"字典键: {list(data.keys())}")
        except:
            print("不是有效的JSON数据")
            
    except Exception as e:
        print(f"requests测试失败: {e}")

def test_with_selenium():
    """使用Selenium测试"""
    print("\n=== 使用Selenium测试 ===")
    url = "https://rmydb.cnii.com.cn/html/2025/20250501/data.json"
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("正在加载页面...")
        driver.get(url)
        time.sleep(5)  # 等待JavaScript执行
        
        page_source = driver.page_source[:500]  # 只显示前500字符
        print(f"页面源码(前500字符):\n{page_source}")
        
        # 尝试查找pre标签
        try:
            from selenium.webdriver.common.by import By
            pre_element = driver.find_element(By.TAG_NAME, "pre")
            pre_text = pre_element.text[:500]
            print(f"Pre标签内容(前500字符):\n{pre_text}")
            
            # 尝试解析JSON
            try:
                data = json.loads(pre_element.text)
                print(f"JSON解析成功，数据类型: {type(data)}")
                if isinstance(data, list):
                    print(f"列表长度: {len(data)}")
            except:
                print("Pre标签内容不是有效JSON")
        except:
            print("未找到pre标签")
            
        driver.quit()
        
    except Exception as e:
        print(f"Selenium测试失败: {e}")

def test_browser_visit():
    """测试浏览器访问页面的基本信息"""
    print("\n=== 测试页面基本信息 ===")
    url = "https://rmydb.cnii.com.cn/html/2025/20250501/data.json"
    
    try:
        chrome_options = Options()
        # 不使用无头模式，看看实际页面
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("正在加载页面...")
        driver.get(url)
        time.sleep(3)
        
        # 获取页面标题
        title = driver.title
        print(f"页面标题: {title}")
        
        # 获取当前URL（可能会重定向）
        current_url = driver.current_url
        print(f"当前URL: {current_url}")
        
        # 检查是否有JavaScript错误或特殊标识
        page_source = driver.page_source
        if "Please enable JavaScript" in page_source:
            print("发现JavaScript提示")
        if "<!DOCTYPE" in page_source:
            print("返回HTML页面")
        if page_source.strip().startswith('[') or page_source.strip().startswith('{'):
            print("可能是JSON数据")
            
        print(f"页面内容长度: {len(page_source)}")
        
        input("按Enter关闭浏览器...")
        driver.quit()
        
    except Exception as e:
        print(f"浏览器测试失败: {e}")

if __name__ == "__main__":
    test_with_requests()
    test_with_selenium()
    # test_browser_visit()  # 取消注释以手动查看页面
