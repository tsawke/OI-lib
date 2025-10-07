import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from pathlib import Path
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== Configuration ====
BASE_URL = "https://oi.wiki/"
OUTPUT_DIR = Path("pdf")

# ==== Helper Functions ====

def setup_driver():
    """设置Chrome浏览器驱动，支持PDF打印"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # 设置打印选项
    chrome_options.add_argument('--enable-print-browser')
    chrome_options.add_argument('--run-all-compositor-stages-before-draw')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Chrome driver setup failed: {e}")
        print("请确保已安装ChromeDriver并添加到PATH中")
        return None

def get_page_title_and_category(soup, url):
    """从页面中提取标题和分类信息"""
    # 获取页面标题
    title_elem = soup.find('h1')
    if title_elem:
        title = title_elem.get_text().strip()
    else:
        # 从URL路径推断标题
        path = urlparse(url).path.strip('/')
        title = path.split('/')[-1] if path else "index"
    
    # 从URL路径获取分类
    path_parts = urlparse(url).path.strip('/').split('/')
    if len(path_parts) > 1:
        category = path_parts[0]  # 使用第一级路径作为分类
    else:
        category = "其他"
    
    return title, category

def fetch_html(url):
    """获取指定URL的HTML内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # 使用Session来保持连接
        session = requests.Session()
        session.headers.update(headers)
        
        # 添加重试机制和SSL配置
        resp = session.get(
            url, 
            timeout=(10, 30),  # (连接超时, 读取超时)
            verify=False,      # 禁用SSL验证以避免证书问题
            allow_redirects=True,
            stream=False
        )
        resp.raise_for_status()
        
        # 检查内容类型
        content_type = resp.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            print(f"⚠️ Skipping non-HTML content: {url} (Content-Type: {content_type})")
            return None
            
        return resp.text
        
    except requests.exceptions.SSLError as e:
        print(f"⚠️ SSL error for {url}: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"⚠️ Timeout error for {url}: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"⚠️ Connection error for {url}: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else 'Unknown'
        print(f"⚠️ HTTP error {code} for {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request error for {url}: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error for {url}: {e}")
        return None

def save_page_as_pdf(driver, url, output_path: Path):
    """将网页保存为PDF"""
    try:
        driver.get(url)
        
        # 等待页面加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 额外等待确保内容完全加载
        time.sleep(3)
        
        # 使用Chrome的打印功能保存为PDF
        print_options = {
            'landscape': False,
            'displayHeaderFooter': False,
            'printBackground': True,
            'preferCSSPageSize': True,
        }
        
        result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
        
        # 保存PDF文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            import base64
            f.write(base64.b64decode(result['data']))
        
        print(f"✅ Saved PDF: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save PDF for {url}: {e}")
        return False

def is_article_page(url, soup):
    """判断是否为文章页面（而非导航页面）"""
    # 排除主页
    if url == BASE_URL or url == BASE_URL.rstrip('/'):
        return False
    
    # 排除明显的非文章页面
    excluded_patterns = [
        '/edit', '/history', '/search', '/special:', 
        '.css', '.js', '.png', '.jpg', '.gif', '.svg',
        '/user:', '/talk:', '/file:', '/category:'
    ]
    
    url_lower = url.lower()
    if any(pattern in url_lower for pattern in excluded_patterns):
        return False
    
    # OI Wiki的文章页面通常有以下特征之一：
    # 1. 有h1标题标签
    h1 = soup.find('h1')
    if not h1:
        return False
    
    # 2. 检查页面是否有足够的文本内容
    # 使用多种选择器查找主要内容
    content_selectors = [
        '.md-content',      # OI Wiki 可能使用的类
        '.content',         # 通用内容类
        'main',            # HTML5 main 标签
        'article',         # HTML5 article 标签
        '#content',        # ID为content的元素
        '.wiki-content',   # Wiki内容类
        '.page-content'    # 页面内容类
    ]
    
    main_content = None
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    # 如果没找到特定的内容容器，使用整个body
    if not main_content:
        main_content = soup.find('body')
    
    if main_content:
        text_content = main_content.get_text().strip()
        # 降低文本长度要求，因为有些文章可能比较短
        if len(text_content) < 200:  # 至少200字符
            return False
    else:
        return False
    
    # 3. 检查URL结构 - OI Wiki的文章通常有层级结构
    path = urlparse(url).path.strip('/')
    if path and '/' in path:  # 有路径且有层级结构
        return True
    
    # 4. 如果URL路径不为空且不是特殊页面，可能是文章
    if path and not any(special in path.lower() for special in ['index', 'main', 'home']):
        return True
    
    return False

# ==== 主要流程 ====

def crawl_oi_wiki():
    """爬取OI Wiki并生成PDF"""
    
    # 设置浏览器驱动
    driver = setup_driver()
    if not driver:
        return
    
    try:
        # 1. 发现所有文章页面
        print("🔍 正在发现OI Wiki文章页面...")
        visited = set()
        
        # 从一些已知的文章页面开始，而不仅仅是首页
        initial_urls = {
            BASE_URL,
            "https://oi.wiki/math/number-theory/basic/",
            "https://oi.wiki/ds/stack/",
            "https://oi.wiki/graph/shortest-path/",
            "https://oi.wiki/string/hash/",
            "https://oi.wiki/dp/basic/",
            "https://oi.wiki/search/dfs/",
            "https://oi.wiki/basic/sort/",
            "https://oi.wiki/misc/binary-search/"
        }
        
        to_visit = initial_urls.copy()
        article_pages = []
        
        while to_visit and len(visited) < 200:  # 减少爬取数量，提高成功率
            url = to_visit.pop()
            if url in visited:
                continue
            visited.add(url)
            
            print(f"正在检查: {url}")
            
            html = fetch_html(url)
            if html is None:
                print(f"  ❌ 无法获取页面内容")
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 判断是否为文章页面
            if is_article_page(url, soup):
                article_pages.append(url)
                print(f"  ✅ 发现文章页面")
            else:
                print(f"  ⏭️ 跳过非文章页面")
            
            # 收集更多链接（限制在同域名下）
            links_added = 0
            for a in soup.find_all('a', href=True):
                if links_added >= 10:  # 每页最多添加10个新链接
                    break
                    
                href = urljoin(BASE_URL, a['href'])
                parsed = urlparse(href)
                
                # 只处理同域名且未访问的链接
                if (parsed.netloc == urlparse(BASE_URL).netloc and 
                    href not in visited and 
                    len(to_visit) < 100 and  # 减少待访问队列大小
                    not any(skip in href.lower() for skip in ['.css', '.js', '.png', '.jpg', 'edit', 'history'])):
                    to_visit.add(href)
                    links_added += 1
            
            # 添加延时避免过快请求
            time.sleep(1)
        
        print(f"✅ 发现 {len(article_pages)} 个文章页面")
        
        # 2. 为每个文章页面生成PDF
        print("📄 正在生成PDF文件...")
        success_count = 0
        
        for i, page_url in enumerate(article_pages, 1):
            print(f"处理进度: {i}/{len(article_pages)} - {page_url}")
            
            # 获取页面信息
            html = fetch_html(page_url)
            if html is None:
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            title, category = get_page_title_and_category(soup, page_url)
            
            # 清理标题中的非法字符
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            pdf_filename = f"{safe_title} - OI Wiki.pdf"
            output_path = OUTPUT_DIR / category / pdf_filename
            
            # 跳过已存在的文件
            if output_path.exists():
                print(f"⏭️ 文件已存在，跳过: {output_path}")
                continue
            
            # 生成PDF
            if save_page_as_pdf(driver, page_url, output_path):
                success_count += 1
            
            # 适当延时避免过于频繁的请求
            time.sleep(1)
        
        print(f"🎉 完成！成功生成 {success_count} 个PDF文件，保存在: {OUTPUT_DIR}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    crawl_oi_wiki()
