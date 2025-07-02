import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps
import tempfile
import shutil
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
import pypdf
import io
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
from typing import List, Tuple

class OptimizedImageToPDFConverter:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("图片转PDF工具 (优化版)")
        self.window.geometry("800x600")
        
        # 设置窗口样式
        self.style = ttk.Style()
        self.style.configure('TButton', padding=10, font=('微软雅黑', 12))
        self.style.configure('TLabel', font=('微软雅黑', 12))
        self.style.configure('Header.TLabel', font=('微软雅黑', 16, 'bold'))
        self.style.configure('TProgressbar', thickness=20)
        
        # 设置窗口背景色
        self.window.configure(bg='#f0f0f0')
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.window, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建界面元素
        self.create_widgets()
        
        # 存储选择的图片文件
        self.image_files = []
        
        # 优化设置
        self.max_image_size = (2048, 2048)  # 最大图片尺寸
        self.jpeg_quality = 85  # JPEG质量
        self.max_workers = min(4, os.cpu_count() or 1)  # 最大线程数
        
    def create_widgets(self):
        # 标题
        header = ttk.Label(
            self.main_frame,
            text="图片转PDF工具 (优化版)",
            style='Header.TLabel'
        )
        header.pack(pady=20)
        
        # 说明文字
        description = ttk.Label(
            self.main_frame,
            text="优化版本：更快的转换速度，更低的内存占用，支持跨平台",
            wraplength=600
        )
        description.pack(pady=10)
        
        # 创建按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=20)
        
        # 选择文件按钮
        self.select_button = ttk.Button(
            button_frame,
            text="选择图片文件",
            command=self.select_files,
            style='TButton'
        )
        self.select_button.pack(side=tk.LEFT, padx=10)
        
        # 转换按钮
        self.convert_button = ttk.Button(
            button_frame,
            text="转换为PDF",
            command=self.start_conversion,
            state=tk.DISABLED,
            style='TButton'
        )
        self.convert_button.pack(side=tk.LEFT, padx=10)
        
        # 文件信息框架
        info_frame = ttk.LabelFrame(self.main_frame, text="文件信息", padding="10")
        info_frame.pack(fill=tk.X, pady=20)
        
        # 显示选择的文件数量
        self.file_label = ttk.Label(
            info_frame,
            text="未选择文件",
            style='TLabel'
        )
        self.file_label.pack(pady=10)
        
        # 进度条框架
        progress_frame = ttk.LabelFrame(self.main_frame, text="转换进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=20)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=600,
            mode='determinate',
            style='TProgressbar'
        )
        self.progress_bar.pack(pady=10)
        
        # 状态标签
        self.status_label = ttk.Label(
            progress_frame,
            text="准备就绪",
            style='TLabel'
        )
        self.status_label.pack(pady=5)
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            self.image_files = list(files)
            self.file_label.config(
                text=f"已选择 {len(self.image_files)} 个文件"
            )
            self.convert_button.config(state=tk.NORMAL)
            self.status_label.config(text="已选择文件，可以开始转换")
            self.progress_var.set(0)
    
    def optimize_image(self, image_path: str) -> Tuple[Image.Image, str]:
        """优化图片：自动旋转、调整大小、优化质量"""
        try:
            # 打开图片并自动处理EXIF旋转
            with Image.open(image_path) as img:
                # 自动处理图片旋转
                img = ImageOps.exif_transpose(img)
                
                # 转换为RGB模式（如果需要）
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整图片大小（如果太大）
                if img.size[0] > self.max_image_size[0] or img.size[1] > self.max_image_size[1]:
                    img.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                
                # 创建副本以避免引用原始文件
                optimized_img = img.copy()
                
            return optimized_img, os.path.basename(image_path)
        except Exception as e:
            raise Exception(f"处理图片 {os.path.basename(image_path)} 时出错: {str(e)}")
    
    def create_pdf_from_image(self, img: Image.Image, filename: str) -> bytes:
        """从图片创建PDF页面"""
        # 创建内存中的PDF
        buffer = io.BytesIO()
        
        # 根据图片方向选择页面大小
        img_width, img_height = img.size
        if img_width > img_height:
            page_size = landscape(A4)
        else:
            page_size = A4
        
        c = canvas.Canvas(buffer, pagesize=page_size)
        page_width, page_height = page_size
        
        # 计算图片在页面上的位置和大小
        # 留出底部空间显示文件名
        available_height = page_height - 60
        
        # 计算缩放比例
        scale_x = (page_width - 40) / img_width
        scale_y = available_height / img_height
        scale = min(scale_x, scale_y, 1)  # 不放大图片
        
        # 计算图片位置（居中）
        scaled_width = img_width * scale
        scaled_height = img_height * scale
        x = (page_width - scaled_width) / 2
        y = (available_height - scaled_height) / 2 + 30  # 底部留空间
        
        # 保存图片到临时字节流
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=self.jpeg_quality, optimize=True)
        img_buffer.seek(0)
        
        # 在PDF中绘制图片
        c.drawImage(img_buffer, x, y, width=scaled_width, height=scaled_height)
        
        # 添加文件名
        c.setFont("Helvetica-Bold", 12)
        text_width = c.stringWidth(filename, "Helvetica-Bold", 12)
        c.drawString((page_width - text_width) / 2, 15, filename)
        
        c.save()
        
        # 释放内存
        img_buffer.close()
        del img  # 显式删除图片对象
        gc.collect()  # 强制垃圾回收
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def process_single_image(self, image_path: str) -> bytes:
        """处理单个图片并返回PDF字节"""
        try:
            # 优化图片
            img, filename = self.optimize_image(image_path)
            
            # 创建PDF
            pdf_bytes = self.create_pdf_from_image(img, filename)
            
            return pdf_bytes
        except Exception as e:
            raise Exception(f"处理图片 {os.path.basename(image_path)} 失败: {str(e)}")
    
    def update_progress(self, completed: int, total: int, current_file: str = ""):
        """线程安全的进度更新"""
        def update_ui():
            progress = (completed / total) * 100
            self.progress_var.set(progress)
            if current_file:
                self.status_label.config(text=f"正在处理 ({completed}/{total}): {current_file}")
            else:
                self.status_label.config(text=f"处理进度: {completed}/{total}")
            self.window.update_idletasks()
        
        # 在主线程中更新UI
        self.window.after(0, update_ui)
    
    def convert_to_pdf_threaded(self, output_path: str):
        """在后台线程中执行转换"""
        try:
            total_files = len(self.image_files)
            pdf_parts = []
            
            # 使用线程池处理图片
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_index = {
                    executor.submit(self.process_single_image, img_path): (i, img_path)
                    for i, img_path in enumerate(self.image_files)
                }
                
                # 收集结果
                completed = 0
                for future in as_completed(future_to_index):
                    index, img_path = future_to_index[future]
                    try:
                        pdf_bytes = future.result()
                        pdf_parts.append((index, pdf_bytes))
                        completed += 1
                        
                        # 更新进度（减少更新频率）
                        if completed % max(1, total_files // 20) == 0 or completed == total_files:
                            self.update_progress(completed, total_files, os.path.basename(img_path))
                        
                    except Exception as e:
                        # 在主线程中显示错误
                        self.window.after(0, lambda: messagebox.showerror("错误", str(e)))
                        return
            
            # 按原始顺序排序PDF部分
            pdf_parts.sort(key=lambda x: x[0])
            
            self.window.after(0, lambda: self.status_label.config(text="正在合并PDF..."))
            
            # 合并PDF
            if len(pdf_parts) == 1:
                # 单个文件，直接保存
                with open(output_path, 'wb') as f:
                    f.write(pdf_parts[0][1])
            else:
                # 多个文件，使用pypdf合并
                merger = pypdf.PdfMerger()
                
                for _, pdf_bytes in pdf_parts:
                    pdf_buffer = io.BytesIO(pdf_bytes)
                    merger.append(pdf_buffer)
                
                # 保存合并后的PDF
                with open(output_path, 'wb') as output_file:
                    merger.write(output_file)
                
                merger.close()
            
            # 清理内存
            del pdf_parts
            gc.collect()
            
            # 成功完成
            self.window.after(0, lambda: [
                self.update_progress(total_files, total_files),
                messagebox.showinfo("成功", f"PDF转换完成！\n文件保存至: {output_path}"),
                self.status_label.config(text="转换完成！"),
                self.convert_button.config(state=tk.NORMAL),
                self.select_button.config(state=tk.NORMAL)
            ])
            
        except Exception as e:
            # 在主线程中显示错误
            self.window.after(0, lambda: [
                messagebox.showerror("错误", f"转换过程中出现错误：{str(e)}"),
                self.status_label.config(text="转换失败！"),
                self.convert_button.config(state=tk.NORMAL),
                self.select_button.config(state=tk.NORMAL)
            ])
        finally:
            # 重置进度条
            self.window.after(0, lambda: self.progress_var.set(0))
    
    def start_conversion(self):
        """开始转换过程"""
        if not self.image_files:
            messagebox.showerror("错误", "请先选择图片文件")
            return
        
        # 选择保存位置
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        
        if not output_path:
            return
        
        # 禁用按钮防止重复点击
        self.convert_button.config(state=tk.DISABLED)
        self.select_button.config(state=tk.DISABLED)
        
        # 在后台线程中启动转换
        conversion_thread = threading.Thread(
            target=self.convert_to_pdf_threaded,
            args=(output_path,),
            daemon=True
        )
        conversion_thread.start()
    
    def run(self):
        # 设置窗口在屏幕中央
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        self.window.mainloop()

if __name__ == "__main__":
    app = OptimizedImageToPDFConverter()
    app.run()