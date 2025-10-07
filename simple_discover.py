#!/usr/bin/env python3
"""
简单的OI Wiki页面发现脚本
"""

import requests
import urllib3
from bs4 import BeautifulSoup
import json
import time
import random

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_page_with_retries(url, max_retries=3):
    """带重试的页面获取"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session = requests.Session()
    
    for attempt in range(max_retries):
        try:
            print(f"尝试访问 {url} (第{attempt+1}次)")
            response = session.get(url, headers=headers, verify=False, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                print("访问被拒绝，等待后重试...")
                time.sleep(random.uniform(5, 10))
            else:
                print(f"HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"请求失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
    
    return None

def test_topic_urls():
    """测试已知的topic URL"""
    test_urls = [
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
        
        # 可能存在的其他topic
        "topic/dsu/",
        "topic/segment-tree/",
        "topic/fenwick/",
        "topic/trie/",
        "topic/kmp/",
        "topic/hash/",
        "topic/convex-hull/",
        "topic/centroid-decomposition/",
        "topic/link-cut-tree/",
        "topic/persistent/",
    ]
    
    base_url = "https://oi-wiki.org/"
    existing_urls = []
    non_existing_urls = []
    
    print("🔍 测试topic URL...")
    for url_path in test_urls:
        full_url = f"{base_url}{url_path}"
        response = get_page_with_retries(full_url, max_retries=2)
        
        if response and response.status_code == 200:
            # 检查页面内容确认不是404页面
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            h1 = soup.find('h1')
            
            # 如果有正常的标题且不包含"404"等错误信息
            if title and not any(x in title.get_text().lower() for x in ['404', 'not found', 'error']):
                existing_urls.append({
                    'url': url_path,
                    'title': title.get_text().strip() if title else '',
                    'h1': h1.get_text().strip() if h1 else ''
                })
                print(f"✅ {url_path} - {title.get_text().strip() if title else ''}")
            else:
                non_existing_urls.append(url_path)
                print(f"❌ {url_path} - 页面无效")
        else:
            non_existing_urls.append(url_path)
            print(f"❌ {url_path} - 访问失败")
        
        # 随机延时避免被限制
        time.sleep(random.uniform(1, 3))
    
    return existing_urls, non_existing_urls

if __name__ == "__main__":
    print("🚀 简单的OI Wiki页面发现")
    print("=" * 50)
    
    existing, non_existing = test_topic_urls()
    
    print(f"\n📊 结果统计:")
    print(f"✅ 存在的URL ({len(existing)}):")
    topic_mapping = {}
    for item in existing:
        # 从标题中提取中文名称
        title = item['title']
        h1 = item['h1']
        
        # 优先使用h1，然后是title
        chinese_name = h1 if h1 and h1 != 'OI Wiki' else title
        if 'OI Wiki' in chinese_name:
            chinese_name = chinese_name.replace('OI Wiki', '').strip(' -|')
        
        topic_mapping[item['url']] = chinese_name
        print(f"  \"{item['url']}\": \"{chinese_name}\",")
    
    print(f"\n❌ 不存在的URL ({len(non_existing)}):")
    for url in non_existing:
        print(f"  {url}")
    
    # 保存结果
    with open('topic_mapping_corrected.json', 'w', encoding='utf-8') as f:
        json.dump(topic_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 修正后的映射已保存到 topic_mapping_corrected.json")


