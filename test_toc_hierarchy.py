import fitz  # PyMuPDF
import os

# 测试修复后的TOC层级逻辑
pdf_dir = "./pdf/"
output_file = "test_hierarchy.pdf"

def is_404_pdf(pdf_path):
    """检测PDF是否为404错误页面"""
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        title = metadata.get('title', '').lower() if metadata else ''
        is_404 = '404 not found' in title
        doc.close()
        return is_404
    except Exception as e:
        print(f"   ⚠️ 无法检测PDF {pdf_path}: {e}")
        return False

def collect_pdf_files_hierarchical(root):
    """收集PDF文件并构建分层结构，过滤404错误"""
    items = []
    categories_added = set()
    skipped_404_files = []
    
    for dirpath, _, filenames in os.walk(root):
        rel_dirpath = os.path.relpath(dirpath, root)
        if rel_dirpath == ".":
            continue
        
        category_name = os.path.basename(dirpath)
        pdf_files = [f for f in sorted(filenames) if f.lower().endswith(".pdf")]
        valid_pdf_files = []
        
        # 检测并过滤404 PDF文件
        for file in pdf_files:
            full_path = os.path.join(dirpath, file)
            if is_404_pdf(full_path):
                skipped_404_files.append(full_path)
                print(f"   ℹ️ INFO: 跳过404错误PDF - {file}")
            else:
                valid_pdf_files.append(file)
        
        if valid_pdf_files and category_name not in categories_added:
            items.append((None, category_name, 1, True))
            categories_added.add(category_name)
            
            for file in valid_pdf_files:
                full_path = os.path.join(dirpath, file)
                if "_" in file:
                    title = file.split("_", 1)[1].replace(".pdf", "")
                else:
                    title = file.replace(".pdf", "")
                items.append((full_path, title, 2, False))
    
    # 打印404文件统计信息
    if skipped_404_files:
        print(f"\n📊 404错误PDF统计:")
        print(f"   跳过的文件数: {len(skipped_404_files)}")
        for file_path in skipped_404_files:
            rel_path = os.path.relpath(file_path, root)
            print(f"     - {rel_path}")
        print()
    
    return items

print("🧪 测试TOC层级修复")
print("=" * 50)

# 收集文件
items_list = collect_pdf_files_hierarchical(pdf_dir)

if not items_list:
    print("❌ 没有找到有效的PDF文件")
    exit(1)

# 分离分类和PDF文件
pdf_files = [(path, title, level, is_cat) for path, title, level, is_cat in items_list if not is_cat]
categories = [(path, title, level, is_cat) for path, title, level, is_cat in items_list if is_cat]

print(f"✅ 发现 {len(categories)} 个分类和 {len(pdf_files)} 个有效PDF文件")

# 合并PDF（使用修复后的逻辑）
print(f"\n📚 合并PDF文件（限制前15个用于测试）...")
merged = fitz.open()
toc = []
toc_entries = []
content_page_number = 1
current_category = None
category_start_page = None
processed_files = 0

for idx, (path, title, level, is_category) in enumerate(items_list):
    if is_category:
        # 记录分类信息，但不立即添加到TOC
        current_category = title
        category_start_page = content_page_number
        print(f"   📁 分类: {title}")
    else:
        if processed_files >= 15:  # 限制测试文件数量
            break
        try:
            doc = fitz.open(path)
            if doc.page_count > 0:
                # 如果这是分类下的第一个PDF，先添加分类标题到TOC
                if current_category and category_start_page == content_page_number:
                    toc.append([1, current_category, content_page_number])
                    toc_entries.append((1, current_category, content_page_number))
                    print(f"     ➕ 添加分类到TOC: {current_category} -> 页码 {content_page_number}")
                    current_category = None
                
                # 添加PDF文件到TOC
                toc.append([2, title, content_page_number])
                toc_entries.append((2, title, content_page_number))
                merged.insert_pdf(doc)
                print(f"   ➕ 合并: {title} (Level 2, 页码 {content_page_number}, {doc.page_count} 页)")
                content_page_number += doc.page_count
                processed_files += 1
            doc.close()
        except Exception as e:
            print(f"   ❌ 跳过 {title}: {e}")

print(f"\n📊 合并完成，共 {len(toc_entries)} 个TOC条目")

# 验证TOC层级结构
print(f"\n🔍 验证TOC层级结构:")
for i, (level, title, page) in enumerate(toc_entries, 1):
    print(f"  {i:2d}. Level {level}: {title} -> 页码 {page}")

# 检查第一个条目是否为level 1
if toc_entries and toc_entries[0][0] == 1:
    print("✅ TOC层级结构正确：第一个条目是level 1")
else:
    print("❌ TOC层级结构错误：第一个条目不是level 1")

# 生成TOC内容
print(f"\n📝 生成TOC内容...")
lines_per_page = 50
header_lines = 3
toc_lines = ["目录 (Table of Contents)", "", ""]

# 计算TOC页数
temp_lines = 3
for level, title, pg in toc_entries:
    temp_lines += 1
    if level == 1:  # 分类标题会多占2行（标题+下划线）
        temp_lines += 2
toc_pages_needed = ((temp_lines - header_lines) // lines_per_page) + 1

print(f"📊 TOC统计: {len(toc_entries)} 个条目, {temp_lines} 行, 需要 {toc_pages_needed} 页")

# 生成TOC显示内容
for level, title, pg in toc_entries:
    indent = "  " * (level - 1)
    display_title = title[:50] + "..." if len(title) > 50 else title
    actual_pdf_page = pg + toc_pages_needed
    
    if level == 1:
        # 分类标题
        toc_lines.append(f"\n{display_title}")
        toc_lines.append("-" * len(display_title))
        dot_count = max(3, 50 - len(str(actual_pdf_page)))
        toc_lines.append(f"{'.' * dot_count} {actual_pdf_page}")
    else:
        # PDF文件
        dot_count = max(3, 45 - len(indent) - len(display_title) - len(str(actual_pdf_page)))
        toc_lines.append(f"{indent}{display_title} {'.' * dot_count} {actual_pdf_page}")

# 创建TOC页面
print(f"\n📄 创建 {toc_pages_needed} 页TOC...")
total_lines = len(toc_lines)

for page_idx in range(toc_pages_needed):
    toc_page = merged.new_page(pno=page_idx)
    
    # 修复后的分页逻辑
    if page_idx == 0:
        start_line = 0
        end_line = min(header_lines + lines_per_page, total_lines)
    else:
        start_line = header_lines + lines_per_page + (page_idx - 1) * lines_per_page
        end_line = min(start_line + lines_per_page, total_lines)
    
    page_content = "\n".join(toc_lines[start_line:end_line])
    print(f"  第{page_idx+1}页: 行{start_line+1}-{end_line} ({len(page_content.split())} 个词)")
    
    # 渲染内容
    try:
        font_paths = [
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\msyh.ttc",
        ]
        
        success = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    toc_page.insert_textbox(
                        fitz.Rect(72, 50, 520, 780),
                        page_content,
                        fontsize=10,
                        fontname="SimSun",
                        fontfile=font_path,
                        align=0
                    )
                    print(f"    ✅ 中文字体渲染成功")
                    success = True
                    break
                except:
                    continue
        
        if not success:
            toc_page.insert_textbox(
                fitz.Rect(72, 50, 520, 780),
                page_content,
                fontsize=10,
                fontname="Helvetica",
                align=0
            )
            print(f"    ⚠️ 使用默认字体")
    except Exception as e:
        print(f"    ❌ 渲染失败: {e}")

# 更新TOC书签（所有条目都有页码）
print("\n🔖 设置TOC书签...")
updated_toc = []
for level, title, page in toc:
    actual_page = page + toc_pages_needed
    updated_toc.append([level, title, actual_page])

print(f"书签条目数: {len(updated_toc)}")
print("前5个书签:")
for i, (level, title, page) in enumerate(updated_toc[:5], 1):
    print(f"  {i}. Level {level}: {title} -> PDF页 {page}")

# 设置TOC
if updated_toc:
    try:
        merged.set_toc(updated_toc)
        print("✅ TOC书签设置成功")
    except Exception as e:
        print(f"❌ TOC书签设置失败: {e}")

# 保存
print("\n💾 保存PDF...")
try:
    merged.save(output_file)
    file_size = os.path.getsize(output_file)
    print(f"🎉 成功! 文件: {output_file}")
    print(f"📄 总页数: {merged.page_count}")
    print(f"📦 文件大小: {file_size:,} 字节")
except Exception as e:
    print(f"❌ 保存失败: {e}")
finally:
    merged.close()

print("\n" + "=" * 50)
print("🎯 层级修复测试完成!")
print("检查要点:")
print("1. TOC第一个条目是否为level 1")
print("2. 分类标题是否正确指向第一个PDF页面")
print("3. PDF文件页码是否正确对应")
print("4. 404文件是否被正确过滤")
