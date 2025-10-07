#!/usr/bin/env python3
"""
测试OI Wiki的URL结构，确定哪些页面实际存在
"""

import requests
import urllib3
from urllib.parse import urljoin

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://oi-wiki.org/"

# 测试用户提到的URL
test_urls = [
    # 用户说不存在的
    "topic/lca/",
    
    # 用户说存在的  
    "topic/dsu-app/",
    
    # 其他一些可能的topic URL
    "topic/rmq/",
    "topic/offline-lca/",
    "topic/tree-centroid/",
    "topic/palindrome/",
    
    # 一些可能存在的topic URL（根据常见算法主题推测）
    "topic/dsu/",
    "topic/binary-lifting/",
    "topic/heavy-light/",
    "topic/centroid-decomposition/",
    "topic/mo-algorithm/",
    "topic/sqrt-decomposition/",
]

def test_url(url_path):
    """测试URL是否可访问"""
    full_url = urljoin(BASE_URL, url_path)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(full_url, verify=False, headers=headers, timeout=10)
        return response.status_code, response.url
    except Exception as e:
        return f"Error: {e}", full_url

print("🔍 测试OI Wiki URL结构...")
print("=" * 60)

existing_urls = []
non_existing_urls = []

for url_path in test_urls:
    status, final_url = test_url(url_path)
    print(f"Testing: {url_path:<25} -> Status: {status}")
    
    if isinstance(status, int):
        if status == 200:
            existing_urls.append(url_path)
            print(f"  ✅ 存在: {final_url}")
        elif status == 404:
            non_existing_urls.append(url_path)
            print(f"  ❌ 不存在")
        elif status == 403:
            print(f"  ⚠️  访问被拒绝")
        else:
            print(f"  ❓ 状态码: {status}")
    else:
        print(f"  ❌ 错误: {status}")
    print()

print("\n📊 总结:")
print(f"✅ 存在的URL ({len(existing_urls)}):")
for url in existing_urls:
    print(f"  - {url}")

print(f"\n❌ 不存在的URL ({len(non_existing_urls)}):")
for url in non_existing_urls:
    print(f"  - {url}")
