#!/usr/bin/env python3
"""
发现OI Wiki实际的页面结构
"""

import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://oi-wiki.org/"

def setup_driver():
    """设置Chrome浏览器驱动"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"❌ Chrome driver setup failed: {e}")
        return None

def get_sidebar_links(driver, url):
    """获取页面侧边栏的所有链接"""
    try:
        print(f"正在访问: {url}")
        driver.get(url)
        
        # 等待页面加载完成
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 额外等待确保内容完全加载
        time.sleep(5)
        
        # 获取页面HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找侧边栏导航
        sidebar_selectors = [
            '.md-nav--secondary',  # MkDocs Material主题的侧边栏
            '.md-nav__list',       # 导航列表
            '.toc',                # 目录
            'nav',                 # 通用导航
            '.sidebar',            # 通用侧边栏
            '.navigation'          # 导航区域
        ]
        
        all_links = []
        
        for selector in sidebar_selectors:
            sidebar = soup.select(selector)
            if sidebar:
                print(f"找到侧边栏: {selector}")
                for nav in sidebar:
                    links = nav.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        text = link.get_text().strip()
                        if href.startswith('/') or href.startswith('http'):
                            all_links.append({
                                'href': href,
                                'text': text,
                                'selector': selector
                            })
        
        # 如果侧边栏方法失败，尝试获取所有内部链接
        if not all_links:
            print("侧边栏方法失败，尝试获取所有内部链接...")
            all_page_links = soup.find_all('a', href=True)
            for link in all_page_links:
                href = link['href']
                text = link.get_text().strip()
                if href.startswith('/') and not href.startswith('//'):
                    all_links.append({
                        'href': href,
                        'text': text,
                        'selector': 'all_links'
                    })
        
        return all_links
        
    except Exception as e:
        print(f"获取侧边栏失败: {e}")
        return []

def discover_topic_pages():
    """发现专题算法页面"""
    driver = setup_driver()
    if not driver:
        print("❌ 无法设置浏览器驱动")
        return []
    
    try:
        # 尝试访问专题算法主页
        topic_urls = [
            "https://oi-wiki.org/topic/",
            "https://oi-wiki.org/",  # 主页
        ]
        
        all_topic_links = []
        
        for url in topic_urls:
            print(f"\n🔍 正在分析: {url}")
            links = get_sidebar_links(driver, url)
            
            # 筛选topic相关的链接
            topic_links = []
            for link in links:
                href = link['href']
                if '/topic/' in href:
                    topic_links.append(link)
            
            print(f"找到 {len(topic_links)} 个topic相关链接:")
            for link in topic_links:
                print(f"  {link['href']} -> {link['text']}")
            
            all_topic_links.extend(topic_links)
        
        # 去重
        unique_links = {}
        for link in all_topic_links:
            href = link['href'].rstrip('/')
            if href not in unique_links:
                unique_links[href] = link
        
        return list(unique_links.values())
        
    except Exception as e:
        print(f"发现页面失败: {e}")
        return []
    finally:
        driver.quit()

def analyze_all_categories():
    """分析所有分类的页面"""
    driver = setup_driver()
    if not driver:
        return {}
    
    try:
        # 主要分类页面
        category_urls = {
            'math': 'https://oi-wiki.org/math/',
            'ds': 'https://oi-wiki.org/ds/',
            'graph': 'https://oi-wiki.org/graph/',
            'string': 'https://oi-wiki.org/string/',
            'dp': 'https://oi-wiki.org/dp/',
            'search': 'https://oi-wiki.org/search/',
            'basic': 'https://oi-wiki.org/basic/',
            'misc': 'https://oi-wiki.org/misc/',
            'geometry': 'https://oi-wiki.org/geometry/',
            'topic': 'https://oi-wiki.org/topic/',
        }
        
        all_results = {}
        
        for category, url in category_urls.items():
            print(f"\n🔍 分析分类: {category} - {url}")
            links = get_sidebar_links(driver, url)
            
            # 筛选该分类的链接
            category_links = []
            for link in links:
                href = link['href']
                if f'/{category}/' in href:
                    category_links.append(link)
            
            print(f"找到 {len(category_links)} 个 {category} 相关链接")
            all_results[category] = category_links
            
            # 适当延时
            time.sleep(3)
        
        return all_results
        
    except Exception as e:
        print(f"分析分类失败: {e}")
        return {}
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🚀 发现OI Wiki实际页面结构")
    print("=" * 60)
    
    # 首先专注于topic分类
    print("\n📚 专门分析topic分类...")
    topic_links = discover_topic_pages()
    
    print(f"\n✅ 发现 {len(topic_links)} 个topic页面:")
    topic_mapping = {}
    for link in topic_links:
        href = link['href'].strip('/')
        text = link['text']
        if href.startswith('/'):
            href = href[1:]  # 移除开头的/
        topic_mapping[href] = text
        print(f"  \"{href}\": \"{text}\",")
    
    # 保存结果
    with open('discovered_topics.json', 'w', encoding='utf-8') as f:
        json.dump(topic_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存到 discovered_topics.json")


