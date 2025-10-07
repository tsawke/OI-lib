#!/usr/bin/env python3
"""
验证TOPIC_MAPPING与mkdocs.yml的一致性
"""

import re

# 从crawler_improved.py中提取TOPIC_MAPPING
def extract_topic_mapping():
    """从crawler_improved.py中提取TOPIC_MAPPING"""
    mapping = {}
    with open('crawler_improved.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到TOPIC_MAPPING的定义
    pattern = r'TOPIC_MAPPING\s*=\s*\{(.*?)\}'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        mapping_content = match.group(1)
        # 提取每一行的映射
        lines = mapping_content.split('\n')
        for line in lines:
            if '": "' in line and not line.strip().startswith('#'):
                # 提取键值对
                parts = line.split('": "')
                if len(parts) == 2:
                    key = parts[0].strip().strip('"')
                    value = parts[1].strip().rstrip('",')
                    mapping[key] = value
    
    return mapping

def extract_mkdocs_mapping():
    """从mkdocs.yml中提取实际的页面映射"""
    mapping = {}
    try:
        with open('mkdocs.yml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有.md文件的映射
        pattern = r'- ([^:]+): ([^/]+/[^/]+\.md)'
        matches = re.findall(pattern, content)
        
        for title, path in matches:
            # 转换路径格式: xxx/yyy.md -> xxx/yyy/
            url_path = path.replace('.md', '/').strip()
            mapping[url_path] = title.strip()
    
    except Exception as e:
        print(f"解析mkdocs.yml失败: {e}")
    
    return mapping

def compare_mappings():
    """比较两个映射"""
    crawler_mapping = extract_topic_mapping()
    mkdocs_mapping = extract_mkdocs_mapping()
    
    print("🔍 映射对比分析")
    print("=" * 60)
    
    print(f"爬虫映射条目数: {len(crawler_mapping)}")
    print(f"mkdocs映射条目数: {len(mkdocs_mapping)}")
    
    # 找出爬虫中有但mkdocs中没有的（错误映射）
    crawler_only = set(crawler_mapping.keys()) - set(mkdocs_mapping.keys())
    print(f"\n❌ 爬虫中存在但实际不存在的映射 ({len(crawler_only)}):")
    for path in sorted(crawler_only):
        print(f"  {path} -> {crawler_mapping[path]}")
    
    # 找出mkdocs中有但爬虫中没有的（缺失映射）
    mkdocs_only = set(mkdocs_mapping.keys()) - set(crawler_mapping.keys())
    print(f"\n➕ 实际存在但爬虫中缺失的映射 ({len(mkdocs_only)}):")
    for path in sorted(mkdocs_only):
        print(f"  {path} -> {mkdocs_mapping[path]}")
    
    # 找出标题不一致的映射
    common_paths = set(crawler_mapping.keys()) & set(mkdocs_mapping.keys())
    title_mismatches = []
    for path in common_paths:
        if crawler_mapping[path] != mkdocs_mapping[path]:
            title_mismatches.append((path, crawler_mapping[path], mkdocs_mapping[path]))
    
    print(f"\n⚠️  路径相同但标题不一致的映射 ({len(title_mismatches)}):")
    for path, crawler_title, mkdocs_title in title_mismatches:
        print(f"  {path}:")
        print(f"    爬虫: {crawler_title}")
        print(f"    实际: {mkdocs_title}")
    
    print(f"\n✅ 完全匹配的映射: {len(common_paths) - len(title_mismatches)}")
    
    return {
        'crawler_only': crawler_only,
        'mkdocs_only': mkdocs_only, 
        'title_mismatches': title_mismatches
    }

if __name__ == "__main__":
    results = compare_mappings()
    
    # 生成修正建议
    if results['crawler_only'] or results['mkdocs_only'] or results['title_mismatches']:
        print("\n🔧 修正建议:")
        
        if results['crawler_only']:
            print("\n需要从TOPIC_MAPPING中移除的错误映射:")
            for path in sorted(results['crawler_only']):
                print(f'    # 移除: "{path}": "...",')
        
        if results['mkdocs_only']:
            print("\n需要添加到TOPIC_MAPPING的缺失映射:")
            mkdocs_mapping = extract_mkdocs_mapping()
            for path in sorted(results['mkdocs_only']):
                print(f'    "{path}": "{mkdocs_mapping[path]}",')
        
        if results['title_mismatches']:
            print("\n需要更新标题的映射:")
            mkdocs_mapping = extract_mkdocs_mapping()
            for path, _, _ in results['title_mismatches']:
                print(f'    "{path}": "{mkdocs_mapping[path]}",  # 原标题需要更新')
    else:
        print("\n🎉 所有映射都是正确的！")
