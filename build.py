import fitz  # PyMuPDF
import os


# ==== Configuration ====
pdf_dir = "./pdf/"  # Root directory
output_file = "merged_with_toc.pdf"

# ==== Utility Function ====
def is_404_pdf(pdf_path):
    """
    检测PDF是否为404错误页面
    通过检查PDF的元数据标题是否包含"404 Not Found"
    """
    try:
        doc = fitz.open(pdf_path)
        
        # 检查PDF元数据中的标题
        metadata = doc.metadata
        title = metadata.get('title', '').lower() if metadata else ''
        
        # 检查标题是否包含404特征
        is_404 = '404 not found' in title
        
        doc.close()
        return is_404
        
    except Exception as e:
        print(f"   ⚠️ 无法检测PDF {pdf_path}: {e}")
        return False

def collect_pdf_files_hierarchical(root):
    """
    收集PDF文件并构建分层结构：文件夹作为主标题，PDF文件作为副标题
    同时过滤404错误的PDF文件
    Returns: List of tuples (full_path, title, level, is_category)
    """
    items = []
    categories_added = set()
    skipped_404_files = []
    
    for dirpath, _, filenames in os.walk(root):
        # 获取相对路径
        rel_dirpath = os.path.relpath(dirpath, root)
        if rel_dirpath == ".":
            continue  # 跳过根目录
        
        # 获取文件夹名作为分类
        category_name = os.path.basename(dirpath)
        
        # 收集该目录下的PDF文件
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
            # 添加分类标题（主标题）
            items.append((None, category_name, 1, True))  # None表示这是分类标题
            categories_added.add(category_name)
            
            # 添加该分类下的有效PDF文件（副标题）
            for file in valid_pdf_files:
                full_path = os.path.join(dirpath, file)
                # 清理文件名
                if "_" in file:
                    title = file.split("_", 1)[1].replace(".pdf", "")
                else:
                    title = file.replace(".pdf", "")
                items.append((full_path, title, 2, False))  # level 2 表示副标题
    
    # 打印404文件统计信息
    if skipped_404_files:
        print(f"\n📊 404错误PDF统计:")
        print(f"   跳过的文件数: {len(skipped_404_files)}")
        print(f"   跳过的文件列表:")
        for file_path in skipped_404_files:
            rel_path = os.path.relpath(file_path, root)
            print(f"     - {rel_path}")
        print()
    
    return items

# ==== Step 1: Collect PDFs ====
print("📁 Scanning all subdirectories for PDF files...")

# 检查目录是否存在
if not os.path.exists(pdf_dir):
    raise FileNotFoundError(f"Directory '{pdf_dir}' does not exist.")

items_list = collect_pdf_files_hierarchical(pdf_dir)

if not items_list:
    print(f"❌ No PDF files found in directory: {pdf_dir}")
    print("Please ensure there are PDF files in the following structure:")
    print("  pdf/")
    print("    数论/")
    print("      file1.pdf")
    print("      file2.pdf")
    print("    其他分类/")
    print("      file3.pdf")
    raise FileNotFoundError("No PDF files found under the specified directory.")

# 分离分类和PDF文件
pdf_files = [(path, title, level, is_cat) for path, title, level, is_cat in items_list if not is_cat]
categories = [(path, title, level, is_cat) for path, title, level, is_cat in items_list if is_cat]

print(f"✅ Found {len(categories)} categories and {len(pdf_files)} PDF files.")
print("Structure preview:")
current_category = None
for i, (path, title, level, is_category) in enumerate(items_list[:15], 1):
    if is_category:
        print(f"  📁 {title}")
        current_category = title
    else:
        print(f"    📄 {title}")
if len(items_list) > 15:
    print(f"  ... and {len(items_list) - 15} more items")

# ==== Step 2: Merge PDFs and build hierarchical TOC ====
merged = fitz.open()
toc = []
toc_entries = []
content_page_number = 1  # 内容页码从1开始（不包括TOC页面）

print("📚 Merging files and building hierarchical TOC...")

current_category = None
category_start_page = None

for idx, (path, title, level, is_category) in enumerate(items_list, start=1):
    if is_category:
        # 记录分类信息，但不立即添加到TOC
        current_category = title
        category_start_page = content_page_number  # 记录分类开始页码
        print(f"   📁 Category: {title}")
    else:
        # 这是PDF文件，需要合并
        try:
            doc = fitz.open(path)
            if doc.page_count > 0:
                # 如果这是分类下的第一个PDF，先添加分类标题到TOC
                if current_category and category_start_page == content_page_number:
                    toc.append([1, current_category, content_page_number])  # 分类标题指向第一个PDF
                    toc_entries.append((1, current_category, content_page_number))
                    current_category = None  # 避免重复添加
                
                # 添加PDF文件到TOC
                toc.append([2, title, content_page_number])  # PDF文件使用level 2
                toc_entries.append((2, title, content_page_number))
                merged.insert_pdf(doc)
                print(f"   ➕ Merged: {title} (Level 2, content page {content_page_number}, {doc.page_count} pages)")
                content_page_number += doc.page_count
            else:
                print(f"   ⚠️ Skipped empty PDF: {path}")
            doc.close()
        except Exception as e:
            print(f"   ❌ Failed to merge {path}: {e}")

print("✅ Merge complete.")

# 调试：检查TOC数据
print(f"📊 TOC数据检查: 共 {len(toc_entries)} 个条目")
if toc_entries:
    print("前5个条目:")
    for i, (level, title, page) in enumerate(toc_entries[:5], 1):
        print(f"  {i}. Level {level}: {title} -> Page {page}")

# ==== Step 3: Create and insert TOC pages ====
print("📄 Creating table of contents...")

# 计算需要多少页来显示TOC
lines_per_page = 50  # 增加每页显示行数，充分利用页面空间
header_lines = 3  # 标题占用的行数

# 生成TOC内容 - 注意：这里需要使用更新后的页码
print("📝 生成TOC显示内容...")

# 先生成TOC内容以计算实际需要的页数
toc_lines = ["目录 (Table of Contents)", "", ""]  # 标题和空行

for level, title, pg in toc_entries:
    indent = "  " * (level - 1)
    # 限制标题长度，避免过长
    display_title = title[:60] + "..." if len(title) > 60 else title
    
    if pg is None:
        # 这是分类标题（主标题），不显示页码
        if level == 1:
            toc_lines.append(f"\n{display_title}")  # 分类标题前加空行
            toc_lines.append("-" * len(display_title))  # 添加下划线
        else:
            toc_lines.append(f"{indent}{display_title}")
    else:
        # 这是PDF文件（副标题），先用占位符，稍后更新
        toc_lines.append(f"{indent}{display_title} ... PLACEHOLDER")

# 计算实际需要的TOC页数
total_lines = len(toc_lines)
toc_pages_needed = ((total_lines - header_lines) // lines_per_page) + 1

print(f"📊 TOC统计: {len(toc_entries)} 个条目, {total_lines} 行, 需要 {toc_pages_needed} 页")

# 现在重新生成TOC内容，使用正确的页码
toc_lines = ["目录 (Table of Contents)", "", ""]  # 重新开始

for level, title, pg in toc_entries:
    indent = "  " * (level - 1)
    display_title = title[:60] + "..." if len(title) > 60 else title
    
    # 现在所有条目都有页码，根据层级决定显示格式
    actual_pdf_page = pg + toc_pages_needed
    
    if level == 1:
        # 分类标题，添加空行和下划线，显示页码
        toc_lines.append(f"\n{display_title}")
        toc_lines.append("-" * len(display_title))
        dot_count = max(3, 50 - len(str(actual_pdf_page)))
        toc_lines.append(f"{'.' * dot_count} {actual_pdf_page}")
    else:
        # PDF文件，显示页码
        dot_count = max(3, 45 - len(indent) - len(display_title) - len(str(actual_pdf_page)))
        toc_lines.append(f"{indent}{display_title} {'.' * dot_count} {actual_pdf_page}")

print(f"📊 TOC页码已更新为实际PDF页码（内容页码 + {toc_pages_needed} TOC页数）")

# 创建TOC页面
for page_idx in range(toc_pages_needed):
    print(f"📄 创建TOC第 {page_idx + 1} 页...")
    
    toc_page = merged.new_page(pno=page_idx)
    
    # 确定这一页要显示的行
    if page_idx == 0:
        # 第一页包含标题
        start_line = 0
        end_line = min(header_lines + lines_per_page, total_lines)
    else:
        # 后续页面：从第一页结束的地方继续
        start_line = header_lines + lines_per_page + (page_idx - 1) * lines_per_page
        end_line = min(start_line + lines_per_page, total_lines)
    
    page_content = "\n".join(toc_lines[start_line:end_line])
    
    print(f"  页面内容: 行 {start_line+1}-{end_line}, {len(page_content)} 字符")
    
    # 渲染内容
    success = False
    
    # 方法1: 使用textbox with 中文字体
    try:
        # 尝试使用中文字体
        font_paths = [
            r"C:\Windows\Fonts\simsun.ttc",    # 宋体
            r"C:\Windows\Fonts\simhei.ttf",    # 黑体
            r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
        ]
        
        font_used = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    toc_page.insert_textbox(
                        fitz.Rect(72, 50, 520, 780),  # 扩大文本框：上边距50，下边距780
                        page_content,
                        fontsize=10,
                        fontname="SimSun",
                        fontfile=font_path,
                        align=0
                    )
                    font_used = font_path
                    success = True
                    break
                except Exception as e:
                    continue
        
        if success:
            print(f"  ✅ textbox方式渲染成功 (使用字体: {os.path.basename(font_used)})")
        else:
            print(f"  ⚠️ 中文字体渲染失败，尝试默认字体")
            # 备用：使用默认字体
            toc_page.insert_textbox(
                fitz.Rect(72, 50, 520, 780),  # 扩大文本框
                page_content,
                fontsize=10,
                fontname="Helvetica",
                align=0
            )
            success = True
            print(f"  ⚠️ 使用默认字体渲染（中文可能显示异常）")
            
    except Exception as e:
        print(f"  ⚠️ textbox渲染失败: {e}")
    
    # 方法2: 逐行渲染（备用方案）
    if not success:
        try:
            lines = page_content.split('\n')
            y_pos = 70  # 从更高的位置开始，充分利用页面空间
            
            # 尝试使用中文字体进行逐行渲染
            font_paths = [
                r"C:\Windows\Fonts\simsun.ttc",
                r"C:\Windows\Fonts\simhei.ttf",
                r"C:\Windows\Fonts\msyh.ttc",
            ]
            
            font_used = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_used = font_path
                    break
            
            for line in lines:
                if line.strip() and y_pos < 780:  # 扩大可用范围到780
                    if font_used:
                        try:
                            toc_page.insert_text(
                                fitz.Point(72, y_pos),
                                line,
                                fontsize=10,
                                fontname="SimSun",
                                fontfile=font_used
                            )
                        except:
                            # 如果中文字体失败，使用默认字体
                            toc_page.insert_text(
                                fitz.Point(72, y_pos),
                                line,
                                fontsize=10,
                                fontname="Helvetica"
                            )
                    else:
                        toc_page.insert_text(
                            fitz.Point(72, y_pos),
                            line,
                            fontsize=10,
                            fontname="Helvetica"
                        )
                    y_pos += 13  # 减小行间距，让内容更紧凑
            
            font_name = os.path.basename(font_used) if font_used else "Helvetica"
            print(f"  ✅ 逐行渲染成功 (使用字体: {font_name})")
            success = True
        except Exception as e:
            print(f"  ❌ 逐行渲染也失败: {e}")
    
    if not success:
        print(f"  ❌ 第 {page_idx + 1} 页渲染完全失败")

# 更新TOC页码引用（因为插入了TOC页面，内容页码需要偏移）
print("🔄 更新TOC页码引用...")
print(f"  TOC页面数: {toc_pages_needed}")
print(f"  原始TOC条目数: {len(toc)}")

updated_toc = []
for level, title, page in toc:
    # 实际页码 = 原内容页码 + TOC页面数
    actual_page = page + toc_pages_needed
    updated_toc.append([level, title, actual_page])
    print(f"  {title}: {page} -> {actual_page}")

toc = updated_toc
print(f"✅ TOC页码更新完成，共 {len(toc)} 个条目")

print("✅ TOC page inserted.")


# ==== Step 4: Add Page Numbers ====
print("🔢 Adding page numbers...")

total_pages = merged.page_count
content_pages = total_pages - toc_pages_needed

for i in range(merged.page_count):
    page = merged[i]
    
    if i < toc_pages_needed:
        # TOC页面：显示罗马数字或不显示页码
        if toc_pages_needed > 1:
            # 如果有多页TOC，显示罗马数字
            roman_nums = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
            if i < len(roman_nums):
                page_num_str = roman_nums[i]
            else:
                page_num_str = f"toc-{i+1}"
            
            page.insert_text(
                fitz.Point(500, 820),
                page_num_str,
                fontsize=9,
                fontname="Helvetica-Oblique",
                rotate=0
            )
    else:
        # 内容页面：从1开始编号
        content_page_num = i - toc_pages_needed + 1
        page_num_str = f"{content_page_num} / {content_pages}"
        page.insert_text(
            fitz.Point(500, 820),
            page_num_str,
            fontsize=9,
            fontname="Helvetica-Oblique",
            rotate=0
        )

print(f"✅ Page numbers added. TOC页: {toc_pages_needed}, 内容页: {content_pages}")

# ==== Step 5: Set TOC and Save Output ====
print("📖 Setting up table of contents...")

# 确保TOC格式正确
if toc:
    try:
        merged.set_toc(toc)
        print(f"✅ TOC设置成功，共 {len(toc)} 个条目")
    except Exception as e:
        print(f"⚠️ TOC设置失败: {e}")
        print("尝试修复TOC格式...")
        
        # 修复TOC格式
        fixed_toc = []
        for level, title, page in toc:
            # 确保level是整数，title是字符串，page是整数
            fixed_toc.append([int(level), str(title), int(page)])
        
        try:
            merged.set_toc(fixed_toc)
            print("✅ 修复后的TOC设置成功")
        except Exception as e2:
            print(f"❌ TOC修复失败: {e2}")
else:
    print("⚠️ 没有TOC条目可设置")

print("💾 Saving final merged PDF...")

try:
    merged.save(output_file)
    print(f"🎉 Done! Output saved to: {output_file}")
    print(f"📄 总页数: {merged.page_count}")
    print(f"📚 包含 {len(pdf_files)} 个PDF文件，分为 {len(categories)} 个分类")
except Exception as e:
    print(f"❌ 保存失败: {e}")
finally:
    merged.close()
