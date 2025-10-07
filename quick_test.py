#!/usr/bin/env python3
"""
快速测试关键的topic URL
"""

import requests
import urllib3
from bs4 import BeautifulSoup
import json

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def quick_test_url(url):
    """快速测试URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(f"https://oi-wiki.org/{url}", 
                              headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            if title and '404' not in title.get_text():
                return True, title.get_text().replace(' - OI Wiki', '').strip()
        return False, None
    except:
        return False, None

# 关键的topic URL测试
key_topics = [
    "topic/rmq/",
    "topic/dsu-app/", 
    "topic/lca/",
    "topic/offline-lca/",
    "topic/tree-centroid/",
    "topic/palindrome/",
    "topic/binary-lifting/",
    "topic/heavy-light/",
    "topic/sqrt-decomposition/",
    "topic/mo-algorithm/",
    "topic/dsu/",
    "topic/segment-tree/",
    "topic/fenwick/",
]

print("快速测试关键topic URL...")
existing = {}
non_existing = []

for url in key_topics:
    exists, title = quick_test_url(url)
    if exists:
        existing[url] = title
        print(f"✅ {url} -> {title}")
    else:
        non_existing.append(url)
        print(f"❌ {url}")

print(f"\n存在的映射 ({len(existing)}):")
for url, title in existing.items():
    print(f'    "{url}": "{title}",')

print(f"\n不存在的URL ({len(non_existing)}):")
for url in non_existing:
    print(f"    {url}")

# 保存结果
with open('quick_results.json', 'w', encoding='utf-8') as f:
    json.dump({'existing': existing, 'non_existing': non_existing}, 
              f, ensure_ascii=False, indent=2)


