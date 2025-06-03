#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境批量修复脚本
使用经过验证的反爬虫解决方案
"""

import json
import time
import random
from pathlib import Path
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_fix.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 从practical_crawler导入核心功能
from practical_crawler import PracticalCrawler

def get_problematic_articles():
    """获取所有问题文章列表"""
    articles_dir = Path("articles")
    problematic = []
    
    print("正在扫描问题文章...")
    
    for date_dir in articles_dir.iterdir():
        if not date_dir.is_dir():
            continue
            
        for article_file in date_dir.glob("*.json"):
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                content = data.get('content', {})
                title = content.get('title', '')
                article_content = content.get('content', '')
                
                # 检查是否是问题文章
                is_problematic = (
                    title == '491 Forbidden' or
                    article_content == '无内容' or
                    '491 Forbidden' in title or
                    len(article_content) < 50
                )
                
                if is_problematic:
                    metadata = data.get('metadata', {})
                    
                    # 从文件名推断页码
                    filename = article_file.stem
                    parts = filename.split('_')
                    page_no = parts[1] if len(parts) >= 3 else '001'
                    
                    problematic.append({
                        'date': date_dir.name,
                        'page_no': page_no,
                        'metadata': metadata,
                        'file_path': article_file,
                        'title': metadata.get('mainTitle', '未知标题')[:50] + "..."
                    })
                    
            except Exception as e:
                logger.error(f"读取文件失败 {article_file}: {e}")
    
    return problematic

def production_batch_fix():
    """生产环境批量修复"""
    print("="*60)
    print("人民邮电报爬虫 - 生产环境批量修复工具")
    print("="*60)
    
    # 获取问题文章
    problematic_articles = get_problematic_articles()
    
    if not problematic_articles:
        print("🎉 没有发现问题文章！所有文章都已成功爬取。")
        return
    
    total_articles = len(problematic_articles)
    print(f"\\n📊 发现 {total_articles} 篇问题文章需要修复")
    
    # 显示前10篇文章
    print("\\n📋 前10篇问题文章:")
    for i, article in enumerate(problematic_articles[:10], 1):
        print(f"{i:2d}. {article['date']}: {article['title']}")
    
    if total_articles > 10:
        print(f"    ... 还有 {total_articles - 10} 篇")
    
    # 设置批次大小
    batch_size = 5
    print(f"\\n⚙️ 配置:")
    print(f"   - 批次大小: {batch_size} 篇/批次")
    print(f"   - 文章间延迟: 60秒 (1分钟)")
    print(f"   - 批次间延迟: 120-240秒 (2-4分钟)")
    print(f"   - 预计总时间: {total_articles * 60 / 60:.0f}-{total_articles * 80 / 60:.0f} 分钟")
    
    # 确认执行
    print("\\n⚠️  注意事项:")
    print("   - 请确保网络连接稳定")
    print("   - 过程中请勿关闭程序")
    print("   - 如遇到连续失败，程序会自动暂停")
    
    response = input(f"\\n🚀 是否开始修复？(y/n): ")
    if response.lower() != 'y':
        print("❌ 操作已取消")
        return
    
    # 开始修复
    print(f"\\n🔧 开始批量修复 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("-" * 60)
    
    crawler = PracticalCrawler()
    success_count = 0
    fail_count = 0
    consecutive_fails = 0
    
    for i, article in enumerate(problematic_articles, 1):
        print(f"\\n[{i}/{total_articles}] 修复文章:")
        print(f"📅 日期: {article['date']}")
        print(f"📰 标题: {article['title']}")
        
        try:
            success = crawler.fix_single_article(
                article['date'],
                article['page_no'],
                article['metadata']
            )
            
            if success:
                success_count += 1
                consecutive_fails = 0
                print(f"✅ 修复成功 (成功率: {success_count}/{i} = {success_count/i*100:.1f}%)")
            else:
                fail_count += 1
                consecutive_fails += 1
                print(f"❌ 修复失败 (连续失败: {consecutive_fails})")
                
                # 连续失败保护
                if consecutive_fails >= 3:
                    print("\\n⚠️ 连续3次失败，可能遇到更严格的反爬虫机制")
                    print("建议：")
                    print("1. 暂停30-60分钟后再次尝试")
                    print("2. 或者增加延迟时间")
                    
                    choice = input("是否继续？(y/n): ")
                    if choice.lower() != 'y':
                        break
                    consecutive_fails = 0
                    
        except Exception as e:
            fail_count += 1
            consecutive_fails += 1
            print(f"❌ 修复出错: {e}")
            logger.error(f"修复文章出错: {e}")
        
        # 进度报告
        if i % batch_size == 0 and i < total_articles:
            print(f"\\n📊 批次完成: {i}/{total_articles}")
            print(f"📈 当前成功率: {success_count}/{i} = {success_count/i*100:.1f}%")
            
            # 批次间更长延迟
            batch_delay = random.uniform(60, 120)
            print(f"⏳ 批次间休息 {batch_delay:.0f}s...")
            time.sleep(batch_delay)
    
    # 最终报告
    print("\\n" + "="*60)
    print("🏁 批量修复完成")
    print("="*60)
    print(f"📊 总体统计:")
    print(f"   - 处理文章: {i}")
    print(f"   - 修复成功: {success_count}")
    print(f"   - 修复失败: {fail_count}")
    print(f"   - 成功率: {success_count/i*100:.1f}%")
    
    if success_count > 0:
        print(f"\\n✅ 建议下一步:")
        print(f"   1. 运行 python check_status.py 检查最新状态")
        print(f"   2. 如还有文章需要修复，等待1-2小时后再次运行")
        print(f"   3. 检查修复后的文章内容质量")
    
    print(f"\\n📝 详细日志已保存到: production_fix.log")
    print(f"🕐 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    production_batch_fix()
