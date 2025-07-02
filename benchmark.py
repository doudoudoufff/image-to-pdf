#!/usr/bin/env python3
"""
Performance benchmark script for Image-to-PDF converter
Compares original vs optimized implementation
"""

import time
import os
import tempfile
import shutil
import psutil
import threading
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import gc

# Generate test images for benchmarking
def create_test_images(num_images: int = 10, sizes: Optional[List[Tuple[int, int]]] = None) -> List[str]:
    """Create test images of various sizes for benchmarking"""
    if sizes is None:
        sizes = [(800, 600), (1920, 1080), (3000, 2000), (4000, 3000)]
    
    from PIL import Image, ImageDraw
    import random
    
    test_dir = tempfile.mkdtemp(prefix="pdf_benchmark_")
    image_paths = []
    
    print(f"Creating {num_images} test images in {test_dir}")
    
    for i in range(num_images):
        # Cycle through different sizes
        width, height = sizes[i % len(sizes)]
        
        # Create image with random colors
        img = Image.new('RGB', (width, height), 
                       color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # Add some content
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"Test Image {i+1}\n{width}x{height}", fill=(255, 255, 255))
        
        # Add some shapes for complexity
        for _ in range(10):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.rectangle([x1, y1, x2, y2], 
                         fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # Save image
        img_path = os.path.join(test_dir, f"test_image_{i+1:03d}.jpg")
        img.save(img_path, 'JPEG', quality=90)
        image_paths.append(img_path)
    
    return image_paths

def monitor_memory_usage(process_pid: int, duration: float, interval: float = 0.1) -> Dict:
    """Monitor memory usage of a process"""
    memory_data = {
        'peak_memory_mb': 0,
        'avg_memory_mb': 0,
        'samples': []
    }
    
    try:
        process = psutil.Process(process_pid)
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                memory_data['samples'].append(memory_mb)
                memory_data['peak_memory_mb'] = max(memory_data['peak_memory_mb'], memory_mb)
                time.sleep(interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
    except Exception:
        pass
    
    if memory_data['samples']:
        memory_data['avg_memory_mb'] = sum(memory_data['samples']) / len(memory_data['samples'])
    
    return memory_data

def benchmark_conversion(converter_func, image_paths: List[str], output_path: str) -> Dict:
    """Benchmark a conversion function"""
    # Force garbage collection before test
    gc.collect()
    
    # Get current process for memory monitoring
    current_process = psutil.Process()
    
    # Start memory monitoring in background
    memory_data = {'peak_memory_mb': 0, 'avg_memory_mb': 0, 'samples': []}
    
    def memory_monitor():
        start_time = time.time()
        while time.time() - start_time < 300:  # Max 5 minutes
            try:
                memory_info = current_process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_data['samples'].append(memory_mb)
                memory_data['peak_memory_mb'] = max(memory_data['peak_memory_mb'], memory_mb)
                time.sleep(0.1)
            except:
                break
    
    monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
    monitor_thread.start()
    
    # Measure conversion time
    start_time = time.time()
    start_memory = current_process.memory_info().rss / 1024 / 1024
    
    try:
        # Run conversion
        converter_func(image_paths, output_path)
        success = True
    except Exception as e:
        print(f"Conversion failed: {e}")
        success = False
    
    end_time = time.time()
    end_memory = current_process.memory_info().rss / 1024 / 1024
    
    # Calculate average memory usage
    if memory_data['samples']:
        memory_data['avg_memory_mb'] = sum(memory_data['samples']) / len(memory_data['samples'])
    
    # Get file size
    file_size_mb = 0
    if success and os.path.exists(output_path):
        file_size_mb = os.path.getsize(output_path) / 1024 / 1024
    
    return {
        'success': success,
        'duration_seconds': end_time - start_time,
        'start_memory_mb': start_memory,
        'end_memory_mb': end_memory,
        'peak_memory_mb': memory_data['peak_memory_mb'],
        'avg_memory_mb': memory_data['avg_memory_mb'],
        'memory_increase_mb': end_memory - start_memory,
        'output_file_size_mb': file_size_mb
    }

def simulate_original_conversion(image_paths: List[str], output_path: str):
    """Simulate the original conversion method (slower, more memory usage)"""
    import subprocess
    import tempfile
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import PyPDF2
    import io
    
    # Simulate the original approach with subprocess calls
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_files = []
        
        for i, image_path in enumerate(image_paths):
            # Simulate sips command (load image and convert)
            from PIL import Image
            with Image.open(image_path) as img:
                # Convert to PDF using similar approach as original
                temp_pdf = os.path.join(temp_dir, f"temp_{i}.pdf")
                
                # Create PDF with image
                c = canvas.Canvas(temp_pdf, pagesize=A4)
                img_width, img_height = img.size
                page_width, page_height = A4
                
                # Scale image to fit page
                scale = min(page_width / img_width, (page_height - 50) / img_height)
                scaled_width = img_width * scale
                scaled_height = img_height * scale
                
                # Save image temporarily
                temp_img = os.path.join(temp_dir, f"temp_img_{i}.jpg")
                img.save(temp_img, 'JPEG')
                
                # Add to PDF
                x = (page_width - scaled_width) / 2
                y = (page_height - scaled_height) / 2
                c.drawImage(temp_img, x, y, width=scaled_width, height=scaled_height)
                
                # Add filename
                c.drawString(50, 20, os.path.basename(image_path))
                c.save()
                
                pdf_files.append(temp_pdf)
                
                # Simulate slower processing (original blocking behavior)
                time.sleep(0.01)  # Small delay to simulate subprocess overhead
        
        # Merge PDFs using PyPDF2 (original library)
        if len(pdf_files) == 1:
            shutil.copy(pdf_files[0], output_path)
        else:
            merger = PyPDF2.PdfMerger()
            for pdf_file in pdf_files:
                merger.append(pdf_file)
            
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)

def simulate_optimized_conversion(image_paths: List[str], output_path: str):
    """Simulate the optimized conversion method"""
    from concurrent.futures import ThreadPoolExecutor
    from PIL import Image, ImageOps
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    import pypdf
    import io
    import gc
    
    def process_image(image_path: str) -> bytes:
        # Optimized image processing
        with Image.open(image_path) as img:
            # Auto-rotate and optimize
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                else:
                    img = img.convert('RGB')
            
            # Resize if too large (memory optimization)
            max_size = (2048, 2048)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            optimized_img = img.copy()
        
        # Create PDF in memory
        buffer = io.BytesIO()
        img_width, img_height = optimized_img.size
        
        # Choose page orientation
        if img_width > img_height:
            page_size = landscape(A4)
        else:
            page_size = A4
        
        c = canvas.Canvas(buffer, pagesize=page_size)
        page_width, page_height = page_size
        
        # Calculate scaling and position
        available_height = page_height - 60
        scale_x = (page_width - 40) / img_width
        scale_y = available_height / img_height
        scale = min(scale_x, scale_y, 1)
        
        scaled_width = img_width * scale
        scaled_height = img_height * scale
        x = (page_width - scaled_width) / 2
        y = (available_height - scaled_height) / 2 + 30
        
        # Add image to PDF
        img_buffer = io.BytesIO()
        optimized_img.save(img_buffer, format='JPEG', quality=85, optimize=True)
        img_buffer.seek(0)
        
        c.drawImage(img_buffer, x, y, width=scaled_width, height=scaled_height)
        c.drawString((page_width - c.stringWidth(os.path.basename(image_path), "Helvetica", 12)) / 2, 15, 
                    os.path.basename(image_path))
        c.save()
        
        # Clean up
        img_buffer.close()
        del optimized_img
        gc.collect()
        
        buffer.seek(0)
        return buffer.getvalue()
    
    # Process images in parallel
    max_workers = min(4, os.cpu_count() or 1)
    pdf_parts = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, img_path) for img_path in image_paths]
        
        for i, future in enumerate(futures):
            pdf_bytes = future.result()
            pdf_parts.append((i, pdf_bytes))
    
    # Sort by original order
    pdf_parts.sort(key=lambda x: x[0])
    
    # Merge PDFs using pypdf (modern library)
    if len(pdf_parts) == 1:
        with open(output_path, 'wb') as f:
            f.write(pdf_parts[0][1])
    else:
        merger = pypdf.PdfMerger()
        
        for _, pdf_bytes in pdf_parts:
            pdf_buffer = io.BytesIO(pdf_bytes)
            merger.append(pdf_buffer)
        
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
        
        merger.close()

def run_benchmark():
    """Run the complete benchmark"""
    print("=== Image-to-PDF Converter Performance Benchmark ===\n")
    
    # Test configurations
    test_configs = [
        {'name': 'Small (5 images)', 'num_images': 5, 'sizes': [(800, 600), (1024, 768)]},
        {'name': 'Medium (10 images)', 'num_images': 10, 'sizes': [(1920, 1080), (2048, 1536)]},
        {'name': 'Large (20 images)', 'num_images': 20, 'sizes': [(3000, 2000), (4000, 3000)]}
    ]
    
    results = []
    
    for config in test_configs:
        print(f"Testing: {config['name']}")
        print("-" * 50)
        
        # Create test images
        image_paths = create_test_images(config['num_images'], config['sizes'])
        
        try:
            # Test original method
            print("Testing original method...")
            original_output = tempfile.mktemp(suffix='.pdf')
            original_results = benchmark_conversion(simulate_original_conversion, image_paths, original_output)
            
            # Test optimized method
            print("Testing optimized method...")
            optimized_output = tempfile.mktemp(suffix='.pdf')
            optimized_results = benchmark_conversion(simulate_optimized_conversion, image_paths, optimized_output)
            
            # Calculate improvements
            if original_results['success'] and optimized_results['success']:
                speed_improvement = ((original_results['duration_seconds'] - optimized_results['duration_seconds']) 
                                   / original_results['duration_seconds']) * 100
                memory_improvement = ((original_results['peak_memory_mb'] - optimized_results['peak_memory_mb']) 
                                    / original_results['peak_memory_mb']) * 100
                
                result = {
                    'config': config['name'],
                    'original': original_results,
                    'optimized': optimized_results,
                    'speed_improvement_percent': speed_improvement,
                    'memory_improvement_percent': memory_improvement
                }
                results.append(result)
                
                # Print results
                print(f"\nResults for {config['name']}:")
                print(f"Original: {original_results['duration_seconds']:.2f}s, "
                      f"Peak Memory: {original_results['peak_memory_mb']:.1f}MB")
                print(f"Optimized: {optimized_results['duration_seconds']:.2f}s, "
                      f"Peak Memory: {optimized_results['peak_memory_mb']:.1f}MB")
                print(f"Speed Improvement: {speed_improvement:.1f}%")
                print(f"Memory Improvement: {memory_improvement:.1f}%")
            
            # Cleanup
            for img_path in image_paths:
                if os.path.exists(img_path):
                    os.remove(img_path)
            for output_file in [original_output, optimized_output]:
                if os.path.exists(output_file):
                    os.remove(output_file)
                    
        except Exception as e:
            print(f"Error in test {config['name']}: {e}")
        
        print()
    
    # Summary
    if results:
        print("=== BENCHMARK SUMMARY ===")
        print("Configuration              | Speed Improvement | Memory Improvement")
        print("-" * 65)
        for result in results:
            print(f"{result['config']:<25} | {result['speed_improvement_percent']:.1f}%            | {result['memory_improvement_percent']:.1f}%")

if __name__ == "__main__":
    run_benchmark()