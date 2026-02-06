#!/usr/bin/env python3
"""
Gemini 배치 이미지 생성기 - GUI 버전
Windows/macOS 크로스 플랫폼 지원
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import zipfile
import tempfile
import shutil
from pathlib import Path
from PIL import Image as PILImage
import os
import sys

class GeminiImageGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini 배치 이미지 생성기")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # Variables
        self.api_key = tk.StringVar()
        self.style = tk.StringVar()
        self.resolution = tk.StringVar(value="1K")
        self.is_generating = False
        self.temp_dir = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Label(
            self.root,
            text="🎨 Gemini 배치 이미지 생성기",
            font=("Arial", 16, "bold"),
            pady=10
        )
        header.pack()
        
        # API Key
        api_frame = tk.Frame(self.root, pady=5)
        api_frame.pack(fill=tk.X, padx=20)
        tk.Label(api_frame, text="API 키:", width=10, anchor="w").pack(side=tk.LEFT)
        api_entry = tk.Entry(api_frame, textvariable=self.api_key, show="*")
        api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Help link
        help_label = tk.Label(
            self.root,
            text="API 키 발급: https://aistudio.google.com/apikey",
            fg="blue",
            cursor="hand2",
            font=("Arial", 9)
        )
        help_label.pack(pady=2)
        help_label.bind("<Button-1>", lambda e: self.open_url("https://aistudio.google.com/apikey"))
        
        # Prompts
        prompt_label = tk.Label(self.root, text="프롬프트 (한 줄에 하나씩):", anchor="w")
        prompt_label.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        self.prompt_text = scrolledtext.ScrolledText(
            self.root,
            height=15,
            font=("Arial", 10)
        )
        self.prompt_text.pack(fill=tk.BOTH, padx=20, expand=True)
        
        # Style
        style_frame = tk.Frame(self.root, pady=5)
        style_frame.pack(fill=tk.X, padx=20)
        tk.Label(style_frame, text="스타일:", width=10, anchor="w").pack(side=tk.LEFT)
        style_entry = tk.Entry(style_frame, textvariable=self.style)
        style_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Resolution
        res_frame = tk.Frame(self.root, pady=5)
        res_frame.pack(fill=tk.X, padx=20)
        tk.Label(res_frame, text="해상도:", width=10, anchor="w").pack(side=tk.LEFT)
        res_combo = ttk.Combobox(
            res_frame,
            textvariable=self.resolution,
            values=["1K", "2K", "4K"],
            state="readonly",
            width=10
        )
        res_combo.pack(side=tk.LEFT)
        
        # Generate button
        self.generate_btn = tk.Button(
            self.root,
            text="🚀 생성 시작",
            command=self.start_generation,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            pady=10
        )
        self.generate_btn.pack(pady=15, padx=20, fill=tk.X)
        
        # Progress
        progress_frame = tk.Frame(self.root, pady=5)
        progress_frame.pack(fill=tk.X, padx=20)
        
        self.progress_label = tk.Label(progress_frame, text="대기 중...", anchor="w")
        self.progress_label.pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status
        self.status_text = scrolledtext.ScrolledText(
            self.root,
            height=8,
            font=("Courier", 9),
            state='disabled'
        )
        self.status_text.pack(fill=tk.BOTH, padx=20, pady=10, expand=True)
        
        # Download button (initially hidden)
        self.download_btn = tk.Button(
            self.root,
            text="📥 ZIP 다운로드",
            command=self.download_zip,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold"),
            state='disabled'
        )
        self.download_btn.pack(pady=5, padx=20, fill=tk.X)
        
    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)
    
    def log(self, message):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
    
    def start_generation(self):
        if self.is_generating:
            messagebox.showwarning("경고", "이미 생성 중입니다")
            return
        
        api_key = self.api_key.get().strip()
        prompts_text = self.prompt_text.get("1.0", tk.END).strip()
        
        if not api_key:
            messagebox.showerror("오류", "API 키를 입력해주세요")
            return
        
        if not prompts_text:
            messagebox.showerror("오류", "프롬프트를 입력해주세요")
            return
        
        # Parse prompts
        prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]
        
        if not prompts:
            messagebox.showerror("오류", "유효한 프롬프트가 없습니다")
            return
        
        # Disable button
        self.generate_btn.config(state='disabled')
        self.download_btn.config(state='disabled')
        self.is_generating = True
        
        # Clear previous status
        self.status_text.config(state='normal')
        self.status_text.delete("1.0", tk.END)
        self.status_text.config(state='disabled')
        
        # Start generation in thread
        thread = threading.Thread(
            target=self.generate_images,
            args=(api_key, prompts),
            daemon=True
        )
        thread.start()
    
    def generate_images(self, api_key, prompts):
        try:
            # Import here to avoid slow startup
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            
            total = len(prompts)
            self.log(f"📝 총 {total}개 이미지 생성 시작")
            self.log(f"⏱️ 예상 시간: {total}분")
            self.log("-" * 50)
            
            # Create temp directory
            self.temp_dir = tempfile.mkdtemp()
            
            success_count = 0
            failed = []
            
            for idx, prompt in enumerate(prompts, 1):
                # Update UI
                self.progress_label.config(text=f"생성 중: {idx}/{total}")
                self.progress_bar['value'] = (idx / total) * 100
                
                # Add style
                full_prompt = f"{prompt}, {self.style.get()}" if self.style.get() else prompt
                
                self.log(f"\n🎨 [{idx}/{total}] {prompt[:40]}...")
                
                try:
                    # Generate
                    response = client.models.generate_content(
                        model="gemini-3-pro-image-preview",
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["TEXT", "IMAGE"],
                            image_config=types.ImageConfig(
                                image_size=self.resolution.get()
                            )
                        )
                    )
                    
                    # Save
                    image_saved = False
                    for part in response.parts:
                        if part.inline_data is not None:
                            from io import BytesIO
                            import base64
                            
                            image_data = part.inline_data.data
                            if isinstance(image_data, str):
                                image_data = base64.b64decode(image_data)
                            
                            image = PILImage.open(BytesIO(image_data))
                            
                            # Convert to RGB
                            if image.mode == 'RGBA':
                                rgb_image = PILImage.new('RGB', image.size, (255, 255, 255))
                                rgb_image.paste(image, mask=image.split()[3])
                                rgb_image.save(f"{self.temp_dir}/{idx:03d}.png", 'PNG')
                            elif image.mode == 'RGB':
                                image.save(f"{self.temp_dir}/{idx:03d}.png", 'PNG')
                            else:
                                image.convert('RGB').save(f"{self.temp_dir}/{idx:03d}.png", 'PNG')
                            
                            image_saved = True
                            success_count += 1
                            self.log(f"✅ 저장 완료: {idx:03d}.png")
                            break
                    
                    if not image_saved:
                        failed.append((idx, prompt, "응답에 이미지 없음"))
                        self.log(f"❌ 실패: 응답에 이미지 없음")
                
                except Exception as e:
                    failed.append((idx, prompt, str(e)))
                    self.log(f"❌ 실패: {str(e)}")
                
                # Wait 1 minute (except for last one)
                if idx < total:
                    self.log(f"⏳ 1분 대기... (다음: {idx+1}/{total})")
                    time.sleep(60)
            
            # Complete
            self.log("\n" + "=" * 50)
            self.log(f"🎉 생성 완료! {success_count}/{total}개 성공")
            
            if failed:
                self.log(f"\n⚠️ {len(failed)}개 실패:")
                for idx, prompt, error in failed:
                    self.log(f"  {idx}. {prompt[:30]}... - {error}")
            
            if success_count > 0:
                self.download_btn.config(state='normal')
            
        except Exception as e:
            self.log(f"\n❌ 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"생성 중 오류 발생:\n{str(e)}")
        
        finally:
            self.is_generating = False
            self.generate_btn.config(state='normal')
            self.progress_label.config(text="완료!")
    
    def download_zip(self):
        if not self.temp_dir or not Path(self.temp_dir).exists():
            messagebox.showerror("오류", "생성된 이미지가 없습니다")
            return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile="gemini_images.zip"
        )
        
        if not file_path:
            return
        
        try:
            # Create ZIP
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for img_file in sorted(Path(self.temp_dir).glob("*.png")):
                    zip_file.write(img_file, img_file.name)
            
            self.log(f"\n💾 ZIP 저장 완료: {file_path}")
            messagebox.showinfo("완료", f"ZIP 파일 저장 완료:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("오류", f"ZIP 저장 실패:\n{str(e)}")

def main():
    root = tk.Tk()
    app = GeminiImageGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
