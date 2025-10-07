#!/usr/bin/env python3
"""
基于mkdocs.yml生成正确的TOPIC_MAPPING
"""

import re

def generate_topic_mapping():
    """从mkdocs.yml生成正确的TOPIC_MAPPING"""
    with open('mkdocs.yml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有的页面映射
    pattern = r'- ([^:]+): ([^/\s]+/[^/\s]+\.md)'
    matches = re.findall(pattern, content)
    
    # 按分类组织
    categories = {
        'math': '数学',
        'ds': '数据结构',
        'graph': '图论', 
        'string': '字符串',
        'dp': '动态规划',
        'search': '搜索',
        'basic': '基础算法',
        'misc': '其他算法',
        'geometry': '计算几何',
        'contest': '比赛相关',
        'tools': '工具软件',
        'topic': '专题算法',
        'lang': '语言基础',
        'intro': '项目介绍'
    }
    
    mapping_by_category = {}
    for category in categories.keys():
        mapping_by_category[category] = []
    
    # 处理所有匹配项
    for title, path in matches:
        # 转换路径格式: xxx/yyy.md -> xxx/yyy/
        url_path = path.replace('.md', '/').strip()
        title = title.strip()
        
        # 确定分类
        category = url_path.split('/')[0]
        if category in categories:
            mapping_by_category[category].append((url_path, title))
        else:
            # 未知分类，放到其他算法中
            mapping_by_category['misc'].append((url_path, title))
    
    # 生成Python代码
    print('# 完整的OI Wiki主题映射（基于mkdocs.yml生成）')
    print('TOPIC_MAPPING = {')
    
    for category, chinese_category in categories.items():
        if mapping_by_category[category]:
            print(f'    # {chinese_category}')
            for url_path, title in sorted(mapping_by_category[category]):
                print(f'    "{url_path}": "{title}",')
            print()
    
    print('}')
    
    # 生成分类映射
    print('\n# 分类映射')
    print('CATEGORY_MAPPING = {')
    for category, chinese_category in categories.items():
        print(f'    "{category}": "{chinese_category}",')
    print('}')
    
    # 统计信息
    total_pages = sum(len(pages) for pages in mapping_by_category.values())
    print(f'\n# 统计信息')
    print(f'# 总页面数: {total_pages}')
    for category, chinese_category in categories.items():
        count = len(mapping_by_category[category])
        if count > 0:
            print(f'# {chinese_category}: {count} 页')

if __name__ == "__main__":
    print("🚀 基于mkdocs.yml生成正确的TOPIC_MAPPING")
    print("=" * 60)
    generate_topic_mapping()


