import requests

url = 'https://rmydb.cnii.com.cn/html/2025/20250501/data.json'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f'状态码: {response.status_code}')
    print(f'Content-Type: {response.headers.get("Content-Type", "Unknown")}')
    content = response.text[:300]
    print(f'响应内容(前300字符):\n{content}')
    
    # 检查是否是JSON
    try:
        data = response.json()
        print(f'JSON解析成功，类型: {type(data)}')
        if isinstance(data, list):
            print(f'列表长度: {len(data)}')
            if len(data) > 0:
                print(f'第一个元素类型: {type(data[0])}')
                if isinstance(data[0], dict):
                    print(f'第一个元素的键: {list(data[0].keys())}')
    except Exception as e:
        print(f'JSON解析失败: {e}')
        
except Exception as e:
    print(f'请求失败: {e}')
