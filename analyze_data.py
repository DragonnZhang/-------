#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析和验证脚本
分析已下载的人民邮电报数据
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import pandas as pd

def analyze_downloaded_data():
    """分析已下载的数据"""
    data_dir = Path("data")
    
    print("=== 人民邮电报数据分析报告 ===\n")
    
    # 统计文件信息
    json_files = list(data_dir.glob("*.json"))
    print(f"📁 总共下载文件数: {len(json_files)}")
    
    total_articles = 0
    date_stats = {}
    column_stats = defaultdict(int)
    author_stats = defaultdict(int)
    word_count_stats = []
    
    # 分析每个文件
    for json_file in sorted(json_files):
        date_str = json_file.stem.replace("_data", "")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                # 提取文章信息
                articles = []
                for item in data:
                    if 'onePageArticleList' in item:
                        articles.extend(item['onePageArticleList'])
                
                article_count = len(articles)
                date_stats[date_str] = article_count
                total_articles += article_count
                
                # 统计栏目和作者
                for article in articles:
                    if article.get('articleColumn'):
                        column_stats[article['articleColumn']] += 1
                    if article.get('articleAuthor'):
                        author_stats[article['articleAuthor']] += 1
                    if article.get('wordNumber'):
                        word_count_stats.append(article['wordNumber'])
                
                print(f"📅 {date_str}: {article_count} 篇文章")
            else:
                print(f"⚠️  {date_str}: 数据格式异常")
                
        except Exception as e:
            print(f"❌ {json_file.name}: 文件读取失败 - {e}")
    
    print(f"\n📊 **总体统计**")
    print(f"   总文章数: {total_articles}")
    print(f"   平均每日文章数: {total_articles/len(date_stats):.1f}")
    
    # 字数统计
    if word_count_stats:
        print(f"   平均字数: {sum(word_count_stats)/len(word_count_stats):.0f}")
        print(f"   最长文章: {max(word_count_stats)} 字")
        print(f"   最短文章: {min(word_count_stats)} 字")
    
    # 热门栏目
    print(f"\n📰 **热门栏目 (Top 10)**")
    for column, count in sorted(column_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        if column.strip():  # 排除空栏目
            print(f"   {column}: {count} 篇")
    
    # 活跃作者
    print(f"\n✍️  **活跃作者 (Top 10)**")
    for author, count in sorted(author_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        if author.strip() and not author.startswith("记者"):  # 排除空作者和通用记者
            print(f"   {author}: {count} 篇")
    
    # 缺失日期分析
    print(f"\n📅 **数据覆盖情况**")
    all_may_dates = [f"202505{i:02d}" for i in range(1, 32)]
    downloaded_dates = set(date_stats.keys())
    missing_dates = set(all_may_dates) - downloaded_dates
    
    print(f"   已下载日期: {len(downloaded_dates)} 天")
    print(f"   缺失日期: {len(missing_dates)} 天")
    
    if missing_dates:
        missing_sorted = sorted(missing_dates)
        print(f"   缺失的具体日期: {', '.join(missing_sorted)}")
        
        # 分析缺失日期是否为周末
        from datetime import datetime
        weekend_missing = []
        weekday_missing = []
        
        for date_str in missing_sorted:
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                if date_obj.weekday() >= 5:  # 周六=5, 周日=6
                    weekend_missing.append(date_str)
                else:
                    weekday_missing.append(date_str)
            except:
                pass
        
        if weekend_missing:
            print(f"   其中周末: {len(weekend_missing)} 天 ({', '.join(weekend_missing)})")
        if weekday_missing:
            print(f"   其中工作日: {len(weekday_missing)} 天 ({', '.join(weekday_missing)})")
    
    return date_stats, total_articles

def export_article_list():
    """导出文章清单到CSV"""
    data_dir = Path("data")
    json_files = list(data_dir.glob("*.json"))
    
    all_articles = []
    
    for json_file in sorted(json_files):
        date_str = json_file.stem.replace("_data", "")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    if 'onePageArticleList' in item:
                        for article in item['onePageArticleList']:
                            article_info = {
                                'date': date_str,
                                'title': article.get('mainTitle', ''),
                                'author': article.get('articleAuthor', ''),
                                'column': article.get('articleColumn', ''),
                                'word_count': article.get('wordNumber', 0),
                                'issue_number': article.get('issueNumber', ''),
                                'href': article.get('articleHref', '')
                            }
                            all_articles.append(article_info)
        except Exception as e:
            print(f"处理文件 {json_file.name} 时出错: {e}")
    
    if all_articles:
        df = pd.DataFrame(all_articles)
        csv_file = "article_list.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 已导出文章清单到: {csv_file}")
        print(f"   总共 {len(all_articles)} 篇文章")
        return csv_file
    else:
        print("❌ 没有找到文章数据")
        return None

def validate_data_integrity():
    """验证数据完整性"""
    print("\n🔍 **数据完整性检查**")
    
    data_dir = Path("data")
    json_files = list(data_dir.glob("*.json"))
    
    valid_files = 0
    invalid_files = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查数据结构
            if isinstance(data, list):
                has_articles = False
                for item in data:
                    if isinstance(item, dict) and 'onePageArticleList' in item:
                        articles = item['onePageArticleList']
                        if isinstance(articles, list) and len(articles) > 0:
                            # 检查文章字段完整性
                            for article in articles:
                                required_fields = ['mainTitle', 'articleIssueDate', 'articleHref']
                                if all(field in article for field in required_fields):
                                    has_articles = True
                                    break
                        if has_articles:
                            break
                
                if has_articles:
                    print(f"✅ {json_file.name}: 数据结构正确")
                    valid_files += 1
                else:
                    print(f"⚠️  {json_file.name}: 数据结构异常（无有效文章）")
                    invalid_files += 1
            else:
                print(f"❌ {json_file.name}: 根数据类型错误")
                invalid_files += 1
                
        except json.JSONDecodeError:
            print(f"❌ {json_file.name}: JSON格式错误")
            invalid_files += 1
        except Exception as e:
            print(f"❌ {json_file.name}: {e}")
            invalid_files += 1
    
    print(f"\n📈 **完整性统计**")
    print(f"   有效文件: {valid_files}")
    print(f"   无效文件: {invalid_files}")
    print(f"   数据质量: {valid_files/(valid_files+invalid_files)*100:.1f}%")

def main():
    """主函数"""
    try:
        # 分析数据
        analyze_downloaded_data()
        
        # 验证数据完整性
        validate_data_integrity()
        
        # 导出文章清单
        try:
            export_article_list()
        except ImportError:
            print("\n⚠️  pandas未安装，跳过CSV导出功能")
            print("   如需导出CSV，请运行: pip install pandas")
        
        print("\n🎉 数据分析完成！")
        
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
