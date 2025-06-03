# 人民邮电报数据爬虫

这个爬虫用于爬取人民邮电报网站的data.json数据文件。

## 功能特点

- 自动生成指定月份的所有日期URL
- 支持批量下载data.json文件
- 自动处理网络错误和重试
- 详细的日志记录
- 数据保存到本地文件

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行爬虫

```bash
python crawler.py
```

默认会爬取2025年5月的所有data.json文件。

### 自定义参数

你可以修改`crawler.py`中的参数来爬取不同的年月：

```python
# 在main()函数中修改
crawler.crawl_month(2025, 5)  # 年份, 月份
```

## 输出结果

- 数据文件保存在`data/`目录下
- 文件命名格式：`YYYYMMDD_data.json`
- 日志文件：`crawler.log`

## 注意事项

1. 请合理控制爬取频率，避免对服务器造成压力
2. 如果遇到403或其他错误，可能需要调整请求头或使用代理
3. 某些日期可能没有数据，这是正常现象

## 故障排除

如果遇到JavaScript相关的错误，可能需要使用selenium：

```bash
pip install selenium
```

然后修改代码使用webdriver来处理JavaScript渲染的页面。
