#!/usr/bin/env python3
"""
获取OI Wiki的mkdocs.yml配置文件
"""

import requests
import urllib3
import re

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_mkdocs_config():
    """获取mkdocs.yml配置"""
    url = "https://raw.githubusercontent.com/OI-wiki/OI-wiki/master/mkdocs.yml"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"正在获取: {url}")
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"文件大小: {len(content)} 字符")
            
            # 查找topic相关的配置
            lines = content.split('\n')
            topic_lines = []
            in_topic_section = False
            
            for i, line in enumerate(lines):
                if 'topic' in line.lower() and ':' in line:
                    in_topic_section = True
                    topic_lines.append(f"{i+1}: {line}")
                elif in_topic_section and line.strip() and not line.startswith(' '):
                    # 离开了topic节
                    in_topic_section = False
                elif in_topic_section and line.strip():
                    topic_lines.append(f"{i+1}: {line}")
                
                # 也收集所有包含topic/的行
                if 'topic/' in line:
                    topic_lines.append(f"{i+1}: {line}")
            
            print(f"\n找到 {len(topic_lines)} 行包含topic的配置:")
            for line in topic_lines[:50]:  # 限制输出行数
                print(line)
            
            # 保存完整文件
            with open('mkdocs.yml', 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n完整文件已保存为 mkdocs.yml")
            
            return content
        else:
            print(f"获取失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"错误: {e}")
        return None

def extract_topic_mappings(content):
    """从mkdocs内容中提取topic映射"""
    if not content:
        return {}
    
    # 使用正则表达式查找topic相关的映射
    topic_pattern = r'topic/([^:]+)\.md'
    matches = re.findall(topic_pattern, content)
    
    print(f"\n找到的topic页面:")
    topic_mapping = {}
    for match in matches:
        path = f"topic/{match}/"
        # 尝试从上下文中提取标题
        # 这里需要更复杂的解析，先简单处理
        title = match.replace('-', ' ').title()
        topic_mapping[path] = title
        print(f"  {path} -> {title}")
    
    return topic_mapping

if __name__ == "__main__":
    print("🚀 获取OI Wiki的mkdocs.yml配置")
    print("=" * 50)
    
    content = get_mkdocs_config()
    if content:
        mappings = extract_topic_mappings(content)
        
        if mappings:
            print(f"\n生成的topic映射:")
            for path, title in mappings.items():
                print(f'    "{path}": "{title}",')
        else:
            print("未找到topic映射，请手动检查mkdocs.yml文件")
    else:
        print("获取配置文件失败")


