import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps, ExifTags
import tempfile
import shutil
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
import PyPDF2
import io
import platform

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
        
        # 检测操作系统
        self.is_windows = platform.system() == "Windows"
        
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
    
    def convert_image_to_pdf(self, image_path, output_pdf, filename):
        """将图片转换为PDF，支持Windows和macOS"""
        try:
            # 打开图片
            with Image.open(image_path) as img:
                # 处理EXIF方向信息
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    exif = dict(img._getexif())
                    
                    if exif[orientation] == 3:
                        img = img.rotate(180, expand=True)
                    elif exif[orientation] == 6:
                        img = img.rotate(270, expand=True)
                    elif exif[orientation] == 8:
                        img = img.rotate(90, expand=True)
                except (AttributeError, KeyError, IndexError):
                    # 没有EXIF信息，跳过
                    pass
                
                # 转换为RGB模式（如果需要）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 获取图片尺寸
                img_width, img_height = img.size
                
                # 计算PDF页面尺寸（A4）
                pdf_width, pdf_height = A4
                
                # 计算缩放比例，保持宽高比
                scale_x = pdf_width / img_width
                scale_y = pdf_height / img_height
                scale = min(scale_x, scale_y) * 0.9  # 留一些边距
                
                # 计算在PDF中的位置（居中）
                new_width = img_width * scale
                new_height = img_height * scale
                x = (pdf_width - new_width) / 2
                y = (pdf_height - new_height) / 2 + 50  # 为文件名留出空间
                
                # 创建PDF
                c = canvas.Canvas(output_pdf, pagesize=A4)
                
                # 添加文件名背景
                c.setFillColorRGB(1, 1, 1)  # 白色
                c.rect(0, 0, pdf_width, 50, fill=True)
                
                # 添加文件名
                c.setFillColorRGB(0, 0, 0)  # 黑色
                c.setFont("Helvetica-Bold", 14)
                text_width = c.stringWidth(filename, "Helvetica-Bold", 14)
                c.drawString((pdf_width - text_width) / 2, 20, filename)
                
                # 将图片保存到临时文件
                temp_img_path = output_pdf.replace('.pdf', '_temp.jpg')
                img.save(temp_img_path, 'JPEG', quality=95)
                
                # 在PDF中插入图片
                c.drawImage(temp_img_path, x, y, width=new_width, height=new_height)
                c.save()
                
                # 删除临时图片文件
                os.remove(temp_img_path)
                
        except Exception as e:
            raise Exception(f"处理图片 {filename} 时出错: {str(e)}")
            
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
                    
                    # 生成临时PDF文件路径
                    temp_pdf = os.path.join(temp_dir, f"temp_{i}.pdf")
                    filename = os.path.basename(image_path)
                    
                    # 转换图片为PDF
                    self.convert_image_to_pdf(image_path, temp_pdf, filename)
                    pdf_files.append(temp_pdf)
                
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