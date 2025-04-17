import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps, ExifTags
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
import sys

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
            text="支持JPG、PNG等格式图片，自动处理方向，保持原始比例",
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
            
    def analyze_image(self, image_path):
        """分析图片并返回正确的尺寸和方向信息"""
        with Image.open(image_path) as img:
            # 获取原始EXIF方向信息
            try:
                exif = img.getexif()
                orientation = exif.get(0x0112) if exif else None
            except:
                orientation = None
            
            # 使用 exif_transpose 自动处理图片方向
            img = ImageOps.exif_transpose(img)
            
            # 获取处理后的尺寸
            width, height = img.size
            
            # 判断是否为竖屏图片
            is_portrait = height > width
            
            # 确定旋转方向
            # 如果是竖屏图片，根据EXIF方向决定旋转方向
            if is_portrait:
                # EXIF方向值：
                # 1: 0度
                # 3: 180度
                # 6: 顺时针90度
                # 8: 逆时针90度
                if orientation in [3, 6]:
                    rotate_angle = -90  # 逆时针旋转
                else:
                    rotate_angle = 90  # 顺时针旋转
            else:
                rotate_angle = 0
            
            return {
                'width': width,
                'height': height,
                'is_portrait': is_portrait,
                'rotate_angle': rotate_angle
            }
    
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
            # 创建PDF
            c = canvas.Canvas(output_path)
            margin = 0.5 * inch
            total_files = len(self.image_files)
            
            # 转换进度
            for i, image_path in enumerate(self.image_files):
                # 更新进度条
                progress = (i / total_files) * 100
                self.progress_var.set(progress)
                self.status_label.config(text=f"正在处理: {os.path.basename(image_path)}")
                self.window.update()
                
                # 分析图片
                img_info = self.analyze_image(image_path)
                
                # 设置页面方向
                if img_info['is_portrait']:
                    # 竖屏图片使用竖向页面
                    page_width, page_height = A4
                else:
                    # 横屏图片使用横向页面
                    page_width, page_height = landscape(A4)
                
                c.setPageSize((page_width, page_height))
                
                # 计算可用空间
                available_width = page_width - (2 * margin)
                available_height = page_height - (2 * margin) - 20  # 为文件名留出空间
                
                # 计算缩放比例
                width_ratio = available_width / img_info['width']
                height_ratio = available_height / img_info['height']
                scale = min(width_ratio, height_ratio)
                
                # 计算最终尺寸（保持原始比例）
                new_width = img_info['width'] * scale
                new_height = img_info['height'] * scale
                
                # 计算居中位置
                x = (page_width - new_width) / 2
                y = (page_height - new_height) / 2
                
                # 添加图片，对于竖屏图片进行旋转
                if img_info['is_portrait']:
                    # 根据分析结果进行旋转
                    c.saveState()
                    # 移动原点到页面中心
                    c.translate(page_width/2, page_height/2)
                    # 根据分析的角度旋转
                    c.rotate(img_info['rotate_angle'])
                    # 绘制图片（需要交换宽度和高度）
                    c.drawImage(
                        image_path,
                        -new_height/2, -new_width/2,
                        width=new_height,
                        height=new_width,
                        preserveAspectRatio=True,
                        mask='auto',  # 保持透明度
                        preserveColorSpace=True  # 保持颜色空间
                    )
                    c.restoreState()
                else:
                    # 横屏图片正常绘制
                    c.drawImage(
                        image_path,
                        x, y,
                        width=new_width,
                        height=new_height,
                        preserveAspectRatio=True,
                        mask='auto',  # 保持透明度
                        preserveColorSpace=True  # 保持颜色空间
                    )
                
                # 添加文件名
                filename = os.path.basename(image_path)
                c.setFont("Helvetica", 12)
                text_width = c.stringWidth(filename, "Helvetica", 12)
                c.drawString((page_width - text_width) / 2, y - 20, filename)
                
                # 添加新页面
                c.showPage()
            
            # 保存PDF
            c.save()
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