import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps, ExifTags
import subprocess
import tempfile
import shutil
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
import PyPDF2
import io

class ImageToPDFConverter:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("图片转PDF工具")
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
        
    def create_widgets(self):
        # 标题
        header = ttk.Label(
            self.main_frame,
            text="图片转PDF工具",
            style='Header.TLabel'
        )
        header.pack(pady=20)
        
        # 说明文字
        description = ttk.Label(
            self.main_frame,
            text="支持JPG、PNG等格式图片，自动处理方向，保持原始比例和颜色",
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
            command=self.convert_to_pdf,
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
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"),
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
            
    def add_filename_to_pdf(self, input_pdf, output_pdf, filename):
        # 读取原始PDF
        reader = PyPDF2.PdfReader(input_pdf)
        writer = PyPDF2.PdfWriter()
        
        # 获取第一页
        page = reader.pages[0]
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        # 创建新的PDF页面来添加文件名
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))
        
        # 设置更大的字体大小
        c.setFont("Helvetica-Bold", 14)
        text_width = c.stringWidth(filename, "Helvetica-Bold", 14)
        
        # 在底部添加白色背景
        c.setFillColorRGB(1, 1, 1)  # 白色
        c.rect(0, 0, page_width, 50, fill=True)
        
        # 添加文件名
        c.setFillColorRGB(0, 0, 0)  # 黑色
        c.drawString((page_width - text_width) / 2, 20, filename)
        c.save()
        
        # 将文件名页面与原始页面合并
        packet.seek(0)
        watermark = PyPDF2.PdfReader(packet)
        watermark_page = watermark.pages[0]
        page.merge_page(watermark_page)
        
        # 添加处理后的页面
        writer.add_page(page)
        
        # 保存结果
        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
            
    def convert_to_pdf(self):
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
            
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                total_files = len(self.image_files)
                pdf_files = []
                
                # 转换进度
                for i, image_path in enumerate(self.image_files):
                    # 更新进度条
                    progress = (i / total_files) * 100
                    self.progress_var.set(progress)
                    self.status_label.config(text=f"正在处理: {os.path.basename(image_path)}")
                    self.window.update()
                    
                    # 使用 sips 命令转换单个图片为 PDF
                    temp_pdf = os.path.join(temp_dir, f"temp_{i}.pdf")
                    final_pdf = os.path.join(temp_dir, f"final_{i}.pdf")
                    
                    # 转换图片为PDF
                    subprocess.run([
                        'sips',
                        '-s', 'format', 'pdf',
                        '-s', 'formatOptions', 'best,quality=0.8',
                        image_path,
                        '--out', temp_pdf
                    ], check=True)
                    
                    # 添加文件名
                    self.add_filename_to_pdf(
                        temp_pdf,
                        final_pdf,
                        os.path.basename(image_path)
                    )
                    
                    pdf_files.append(final_pdf)
                
                # 如果只有一个文件，直接移动到目标位置
                if total_files == 1:
                    shutil.move(pdf_files[0], output_path)
                else:
                    # 使用 PyPDF2 合并所有 PDF
                    merger = PyPDF2.PdfMerger()
                    for pdf_file in pdf_files:
                        merger.append(pdf_file)
                    
                    # 保存合并后的 PDF
                    with open(output_path, 'wb') as output_file:
                        merger.write(output_file)
            
            self.progress_var.set(100)
            messagebox.showinfo("成功", "PDF转换完成！")
            self.status_label.config(text="转换完成！")
            
        except Exception as e:
            messagebox.showerror("错误", f"转换过程中出现错误：{str(e)}")
            self.status_label.config(text="转换失败！")
        finally:
            # 重置进度条
            self.progress_var.set(0)
    
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
    app = ImageToPDFConverter()
    app.run() 