"""
OI Wiki 改进版爬虫 - 全面爬取侧边栏所有内容，使用中文标题
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from pathlib import Path
import time
import re
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== Configuration ====
BASE_URL = "https://oi.wiki/"
OUTPUT_DIR = Path("pdf")

# 完整的OI Wiki主题映射（URL -> 中文名称）
TOPIC_MAPPING = {
    # 数学 - 数论
    "math/number-theory/basic/": "数论基础",
    "math/number-theory/prime/": "素数",
    "math/number-theory/gcd/": "最大公约数",
    "math/number-theory/inverse/": "乘法逆元",
    "math/number-theory/crt/": "中国剩余定理",
    "math/number-theory/euler/": "欧拉函数",
    "math/number-theory/sieve/": "筛法",
    "math/number-theory/mobius/": "莫比乌斯反演",
    "math/number-theory/lucas/": "卢卡斯定理",
    "math/number-theory/quadratic-residue/": "二次剩余",
    "math/number-theory/primitive-root/": "原根",
    "math/number-theory/discrete-log/": "离散对数",
    "math/number-theory/du/": "杜教筛",
    "math/number-theory/min-25/": "Min_25筛",
    "math/number-theory/powerful-number/": "Powerful Number筛",
    "math/number-theory/stern-brocot/": "Stern–Brocot树与Farey序列",
    "math/number-theory/continued-fraction/": "连分数",
    "math/number-theory/pell-equation/": "Pell方程",
    "math/number-theory/quadratic-field/": "二次域",
    "math/number-theory/lift-the-exponent/": "升幂引理",
    "math/number-theory/wilson/": "威尔逊定理",
    "math/number-theory/fermat/": "费马小定理",
    "math/number-theory/euler-theorem/": "欧拉定理",
    "math/number-theory/linear-equation/": "线性同余方程",
    "math/number-theory/pollard-rho/": "Pollard Rho算法",
    "math/number-theory/baby-step-giant-step/": "大步小步算法",
    
    # 数学 - 组合数学
    "math/combinatorics/combination/": "组合数",
    "math/combinatorics/permutation/": "排列",
    "math/combinatorics/catalan/": "卡特兰数",
    "math/combinatorics/stirling/": "斯特林数",
    "math/combinatorics/burnside/": "Burnside引理",
    "math/combinatorics/polya/": "Polya定理",
    "math/combinatorics/inclusion-exclusion/": "容斥原理",
    
    # 数学 - 线性代数
    "math/linear-algebra/matrix/": "矩阵",
    "math/linear-algebra/gauss/": "高斯消元",
    "math/linear-algebra/determinant/": "行列式",
    "math/linear-algebra/linear-basis/": "线性基",
    
    # 数学 - 多项式
    "math/poly/fft/": "快速傅里叶变换",
    "math/poly/ntt/": "快速数论变换",
    "math/poly/lagrange/": "拉格朗日插值",
    
    # 数学 - 博弈论
    "math/game-theory/nim/": "Nim游戏",
    "math/game-theory/sg/": "SG函数",
    "math/game-theory/bash/": "巴什博弈",
    "math/game-theory/wythoff/": "威佐夫博弈",
    
    # 数据结构 - 基础
    "ds/stack/": "栈",
    "ds/queue/": "队列",
    "ds/linked-list/": "链表",
    "ds/hash/": "哈希表",
    "ds/heap/": "堆简介",
    "ds/disjoint-set/": "并查集",
    "ds/monotonous-stack/": "单调栈",
    "ds/monotonous-queue/": "单调队列",
    "ds/sparse-table/": "ST 表",
    
    # 数据结构 - 树形结构
    "ds/fenwick/": "树状数组",
    "ds/seg/": "线段树基础",
    "ds/cartesian-tree/": "笛卡尔树",
    "ds/splay/": "Splay 树",
    "ds/treap/": "Treap",
    "ds/fhq-treap/": "FHQ Treap",
    "ds/scapegoat/": "替罪羊树",
    "ds/avl/": "AVL 树",
    "ds/red-black-tree/": "红黑树",
    "ds/k-d-tree/": "K-D树",
    "ds/trie/": "字典树",
    "ds/persistent-trie/": "可持久化字典树",
    "ds/chtholly-tree/": "珂朵莉树",
    
    # 数据结构 - 可持久化
    "ds/persistent-seg/": "可持久化线段树",
    "ds/persistent-array/": "可持久化数组",
    
    # 数据结构 - 分块
    "ds/sqrt-decomposition/": "分块",
    "ds/mo-algorithm/": "莫队算法",
    
    # 图论 - 基础
    "graph/concept/": "图论相关概念",
    "graph/store/": "图的存储",
    "graph/traverse/": "图的遍历",
    "graph/tree-basic/": "树基础",
    "graph/tree-centroid/": "树的重心",
    "graph/tree-diameter/": "树的直径",
    "graph/lca/": "最近公共祖先",
    
    # 图论 - 最短路
    "graph/shortest-path/": "最短路",
    "graph/floyd/": "Floyd算法",
    "graph/dijkstra/": "Dijkstra算法",
    "graph/bellman-ford/": "Bellman-Ford算法",
    "graph/spfa/": "SPFA算法",
    "graph/johnson/": "Johnson算法",
    
    # 图论 - 生成树
    "graph/mst/": "最小生成树",
    "graph/kruskal/": "Kruskal算法",
    "graph/prim/": "Prim算法",
    "graph/boruvka/": "Borůvka算法",
    
    # 图论 - 连通性
    "graph/strongly-connected-components/": "强连通分量",
    "graph/bridge/": "桥",
    "graph/cut/": "割点和桥",
    "graph/block-cut-tree/": "圆方树",
    "graph/2-edge-connected-components/": "边双连通分量",
    "graph/2-sat/": "2-SAT",
    
    # 图论 - 匹配
    "graph/bipartite/": "二分图",
    "graph/matching/": "二分图匹配",
    "graph/kuhn-munkres/": "KM算法",
    "graph/general-matching/": "一般图匹配",
    
    # 图论 - 网络流
    "graph/flow/": "网络流简介",
    "graph/max-flow/": "最大流",
    "graph/min-cost-flow/": "最小费用最大流",
    "graph/dinic/": "Dinic算法",
    "graph/isap/": "ISAP算法",
    "graph/hlpp/": "HLPP算法",
    
    # 图论 - 其他
    "graph/topological/": "拓扑排序",
    "graph/euler/": "欧拉图",
    "graph/hamilton/": "哈密顿图",
    "graph/tree-decomposition/": "树分解",
    "graph/tree-dp/": "树形动态规划",
    "graph/rerooting/": "换根动态规划",
    "graph/centroid-decomposition/": "点分治",
    "graph/heavy-light-decomposition/": "重链剖分",
    "graph/link-cut-tree/": "Link Cut Tree",
    
    # 字符串
    "string/basic/": "字符串基础",
    "string/hash/": "字符串哈希",
    "string/kmp/": "前缀函数与 KMP 算法",
    "string/z-func/": "Z 函数（扩展 KMP）",
    "string/manacher/": "Manacher",
    "string/trie/": "字典树 (Trie)",
    "string/ac-automaton/": "AC 自动机",
    "string/suffix-array/": "后缀数组",
    "string/suffix-tree/": "后缀树",
    "string/suffix-automaton/": "后缀自动机",
    "string/palindromic-tree/": "回文树",
    "string/minimal-string/": "最小表示法",
    "string/lyndon/": "Lyndon 分解",
    "string/sequence-automaton/": "序列自动机",
    
    # 动态规划
    "dp/basic/": "动态规划基础",
    "dp/knapsack/": "背包 DP",
    "dp/interval/": "区间 DP",
    "dp/tree/": "树形 DP",
    "dp/state/": "状压 DP",
    "dp/digit/": "数位动态规划",
    "dp/probability/": "概率 DP",
    "dp/linear/": "线性动态规划",
    "dp/sequence/": "序列动态规划",
    "dp/lis/": "最长递增子序列",
    "dp/lcs/": "最长公共子序列",
    "dp/monotonous-queue-optimized/": "单调队列优化DP",
    "dp/convex-hull-optimized/": "凸包优化DP",
    "dp/divide-and-conquer-optimized/": "分治优化DP",
    "dp/quadrangle-optimized/": "四边形不等式优化DP",
    "dp/matrix-optimized/": "矩阵快速幂优化DP",
    
    # 搜索
    "search/dfs/": "DFS（搜索）",
    "search/bfs/": "BFS（搜索）",
    "search/bidirectional/": "双向搜索",
    "search/astar/": "A*",
    "search/iterative/": "迭代加深搜索",
    "search/ida-star/": "IDA*算法",
    "search/alpha-beta/": "Alpha–Beta 剪枝",
    "search/meet-in-middle/": "折半搜索",
    "search/dancing-links/": "舞蹈链",
    
    # 基础算法
    "basic/sort/": "排序算法",
    "basic/binary/": "二分",
    "basic/ternary/": "三分查找",
    "basic/divide-and-conquer/": "递归 & 分治",
    "basic/greedy/": "贪心",
    "basic/quick-power/": "快速幂",
    "basic/constructive/": "构造算法",
    
    # 计算几何
    "geometry/2d/": "二维计算几何基础",
    "geometry/3d/": "三维计算几何基础",
    "geometry/convex-hull/": "凸包",
    "geometry/rotating-calipers/": "旋转卡壳",
    "geometry/half-plane/": "半平面交",
    "geometry/closest-pair/": "最近点对",
    "geometry/delaunay/": "Delaunay三角剖分",
    
    # 其他算法
    "misc/binary-search/": "二分答案",
    "misc/frac-programming/": "分数规划",
    "misc/parallel-binsearch/": "整体二分",
    "misc/ternary-search/": "三分法",
    "misc/simulated-annealing/": "模拟退火",
    "misc/random/": "随机函数",
    "misc/bitwise/": "位运算",
    "misc/expression/": "表达式求值",
    "misc/coordinate-compression/": "离散化",
    "misc/offline/": "离线算法简介",
    "misc/cdq-divide/": "CDQ 分治",
    
    # 专题算法
    "topic/rmq/": "RMQ",
    "topic/dsu-app/": "并查集应用",
    "topic/bracket/": "括号序列",
    "topic/segment-tree-offline/": "线段树与离线询问",
    
    # 高级数据结构
    "advanced-ds/persistent/": "可持久化数据结构",
    "advanced-ds/functional/": "函数式数据结构",
    "advanced-ds/link-cut-tree/": "Link Cut Tree",
    "advanced-ds/top-tree/": "Top Tree",
    "advanced-ds/euler-tour-tree/": "欧拉游览树",
    
    # 数学 - 概率期望
    "math/expectation/": "概率期望",
    "math/generating-function/": "生成函数",
    
    # 数学 - 数值分析
    "math/numerical/": "数值分析",
    "math/simpson/": "辛普森积分",
    
    # 工具与技巧
    "tools/editor/": "编辑器配置",
    "tools/debug/": "调试技巧",
    "tools/complexity/": "复杂度分析",
    "tools/special-judge/": "Special Judge",
    
    # 比赛相关
    "contest/problems/": "题型概述",
    "contest/tricks/": "比赛技巧",
    "contest/template/": "代码模板",
}

# 分类映射
CATEGORY_MAPPING = {
    "math": "数学",
    "ds": "数据结构", 
    "graph": "图论",
    "string": "字符串",
    "dp": "动态规划",
    "search": "搜索",
    "basic": "基础算法",
    "misc": "其他算法",
    "geometry": "计算几何",
    "contest": "比赛相关",
    "tools": "工具软件",
    "topic": "专题算法",
    "advanced-ds": "高级数据结构"
}

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
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Chrome driver setup failed: {e}")
        return None

def get_chinese_title_and_category(url, soup):
    """获取中文标题和分类"""
    # 从URL获取路径
    path = urlparse(url).path.strip('/')
    
    # 查找预定义的中文标题
    chinese_title = None
    for url_pattern, title in TOPIC_MAPPING.items():
        if path == url_pattern.rstrip('/') or path.startswith(url_pattern):
            chinese_title = title
            break
    
    # 如果没有预定义，尝试从页面提取
    if not chinese_title:
        h1 = soup.find('h1')
        if h1:
            chinese_title = h1.get_text().strip()
        else:
            # 最后备用方案：从URL路径推断
            chinese_title = path.split('/')[-1].replace('-', ' ').title()
    
    # 获取中文分类
    path_parts = path.split('/')
    if path_parts:
        category_key = path_parts[0]
        chinese_category = CATEGORY_MAPPING.get(category_key, "其他")
    else:
        chinese_category = "其他"
    
    return chinese_title, chinese_category

def discover_all_articles():
    """发现OI Wiki的所有文章页面"""
    print("🔍 发现OI Wiki所有文章...")
    
    # 基于已知的URL模式生成完整的文章列表
    all_articles = []
    
    # 从预定义的映射中获取所有URL
    for url_path, chinese_title in TOPIC_MAPPING.items():
        full_url = urljoin(BASE_URL, url_path)
        path_parts = url_path.split('/')
        category_key = path_parts[0] if path_parts else "misc"
        chinese_category = CATEGORY_MAPPING.get(category_key, "其他")
        
        all_articles.append({
            'url': full_url,
            'title': chinese_title,
            'category': chinese_category,
            'path': url_path
        })
    
    print(f"✅ 发现 {len(all_articles)} 个预定义文章")
    
    # 按分类分组显示
    by_category = {}
    for article in all_articles:
        category = article['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(article)
    
    print("\n📚 按分类统计:")
    for category, articles in by_category.items():
        print(f"  {category}: {len(articles)} 篇")
    
    return all_articles

def save_page_as_pdf(driver, url, output_path: Path, title: str):
    """将网页保存为PDF"""
    try:
        print(f"  正在访问: {url}")
        driver.get(url)
        
        # 等待页面加载完成
        WebDriverWait(driver, 15).until(
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
            'paperWidth': 8.27,
            'paperHeight': 11.7,
            'marginTop': 0.4,
            'marginBottom': 0.4,
            'marginLeft': 0.4,
            'marginRight': 0.4,
        }
        
        result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
        
        # 保存PDF文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            import base64
            f.write(base64.b64decode(result['data']))
        
        print(f"  ✅ 保存成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ 保存失败: {e}")
        return False

def crawl_oi_wiki_complete():
    """完整爬取OI Wiki"""
    
    # 发现所有文章
    all_articles = discover_all_articles()
    
    # 设置浏览器驱动
    driver = setup_driver()
    if not driver:
        print("❌ 无法设置浏览器驱动")
        return
    
    try:
        print(f"\n🚀 开始爬取 {len(all_articles)} 篇文章...")
        success_count = 0
        
        for i, article in enumerate(all_articles, 1):
            url = article['url']
            chinese_title = article['title']
            category = article['category']
            
            print(f"\n[{i}/{len(all_articles)}] {category} - {chinese_title}")
            
            # 生成安全的文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', chinese_title)
            pdf_filename = f"{safe_title}.pdf"
            output_path = OUTPUT_DIR / category / pdf_filename
            
            # 跳过已存在的文件
            if output_path.exists():
                print(f"  ⏭️ 文件已存在，跳过")
                continue
            
            # 生成PDF
            if save_page_as_pdf(driver, url, output_path, chinese_title):
                success_count += 1
            
            # 适当延时
            time.sleep(2)
        
        print(f"\n🎉 完成！成功生成 {success_count} 个PDF文件")
        print(f"📁 文件保存在: {OUTPUT_DIR}")
        
        # 生成统计报告
        print("\n📊 生成统计:")
        by_category = {}
        for article in all_articles:
            category = article['category']
            by_category[category] = by_category.get(category, 0) + 1
        
        for category, count in by_category.items():
            print(f"  {category}: {count} 篇")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断了程序")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🚀 OI Wiki 完整爬虫 - 中文标题版本")
    print("=" * 60)
    
    # 检查输出目录
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
        print(f"✅ 创建输出目录: {OUTPUT_DIR}")
    
    try:
        crawl_oi_wiki_complete()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        print("\n💡 可能的解决方案:")
        print("1. 确保已安装ChromeDriver并添加到PATH")
        print("2. 检查网络连接")
        print("3. 尝试关闭防火墙或代理设置")
