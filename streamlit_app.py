import streamlit as st
import time
import zipfile
import io
from pathlib import Path
import tempfile
import shutil
from PIL import Image as PILImage

# Page config
st.set_page_config(
    page_title="Gemini 배치 이미지 생성기",
    page_icon="🎨",
    layout="centered"
)

st.title("🎨 Gemini 배치 이미지 생성기")
st.markdown("**90분 대본용 이미지를 자동으로 생성합니다**")

# API Key input
api_key = st.text_input(
    "Gemini API 키",
    type="password",
    help="https://aistudio.google.com/apikey 에서 발급받으세요",
    key="api_key_input"
)

# Prompt input
prompts_text = st.text_area(
    "프롬프트 입력 (한 줄에 하나씩)",
    height=200,
    placeholder="예시:\n따뜻한 봄날의 공원\n가을 단풍이 물든 산\n겨울 눈 내리는 마을",
    help="각 줄이 하나의 이미지로 생성됩니다"
)

# Style input
style = st.text_input(
    "이미지 스타일 (선택사항)",
    placeholder="예: 따뜻한 일러스트, 파스텔톤",
    help="모든 이미지에 공통으로 적용될 스타일"
)

# Resolution
resolution = st.selectbox(
    "해상도",
    options=["1K", "2K", "4K"],
    index=0,
    help="1K: 1024x1024, 2K: 2048x2048, 4K: 4096x4096"
)

# Generate button
if st.button("🚀 생성 시작", type="primary"):
    if not api_key:
        st.error("❌ API 키를 입력해주세요")
    elif not prompts_text.strip():
        st.error("❌ 프롬프트를 입력해주세요")
    else:
        # Parse prompts
        prompts = [p.strip() for p in prompts_text.strip().split('\n') if p.strip()]
        total = len(prompts)
        
        if total == 0:
            st.error("❌ 유효한 프롬프트가 없습니다")
        else:
            st.info(f"📝 총 {total}개 이미지를 생성합니다 (예상 시간: {total}분)")
            
            # Import Gemini
            try:
                from google import genai
                from google.genai import types
            except ImportError:
                st.error("❌ google-genai 패키지가 설치되지 않았습니다")
                st.stop()
            
            # Initialize client
            try:
                client = genai.Client(api_key=api_key)
            except Exception as e:
                st.error(f"❌ API 키 오류: {e}")
                st.stop()
            
            # Create temp directory for images
            temp_dir = tempfile.mkdtemp()
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Generate images
            success_count = 0
            failed_prompts = []
            
            for idx, prompt in enumerate(prompts, 1):
                # Add style if provided
                full_prompt = f"{prompt}, {style}" if style else prompt
                
                status_text.text(f"🎨 생성 중: {idx}/{total} - {prompt[:50]}...")
                
                try:
                    # Generate image
                    response = client.models.generate_content(
                        model="gemini-3-pro-image-preview",
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["TEXT", "IMAGE"],
                            image_config=types.ImageConfig(
                                image_size=resolution
                            )
                        )
                    )
                    
                    # Save image
                    image_saved = False
                    for part in response.parts:
                        if part.inline_data is not None:
                            from io import BytesIO
                            
                            # Get image data
                            image_data = part.inline_data.data
                            if isinstance(image_data, str):
                                import base64
                                image_data = base64.b64decode(image_data)
                            
                            # Load and save as PNG
                            image = PILImage.open(BytesIO(image_data))
                            
                            # Convert to RGB if needed
                            if image.mode == 'RGBA':
                                rgb_image = PILImage.new('RGB', image.size, (255, 255, 255))
                                rgb_image.paste(image, mask=image.split()[3])
                                rgb_image.save(f"{temp_dir}/{idx:03d}.png", 'PNG')
                            elif image.mode == 'RGB':
                                image.save(f"{temp_dir}/{idx:03d}.png", 'PNG')
                            else:
                                image.convert('RGB').save(f"{temp_dir}/{idx:03d}.png", 'PNG')
                            
                            image_saved = True
                            success_count += 1
                            break
                    
                    if not image_saved:
                        failed_prompts.append((idx, prompt, "응답에 이미지가 없음"))
                
                except Exception as e:
                    failed_prompts.append((idx, prompt, str(e)))
                
                # Update progress
                progress_bar.progress(idx / total)
                
                # Wait 1 minute (except for last one)
                if idx < total:
                    status_text.text(f"⏳ 대기 중... (다음: {idx+1}/{total})")
                    time.sleep(60)
            
            # Complete
            progress_bar.progress(1.0)
            status_text.text("✅ 생성 완료!")
            
            # Show results
            st.success(f"🎉 {success_count}/{total}개 이미지 생성 성공!")
            
            if failed_prompts:
                st.warning(f"⚠️ {len(failed_prompts)}개 실패")
                with st.expander("실패 목록 보기"):
                    for idx, prompt, error in failed_prompts:
                        st.text(f"{idx}. {prompt[:50]}... - {error}")
            
            # Create ZIP
            if success_count > 0:
                status_text.text("📦 ZIP 파일 생성 중...")
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for img_file in sorted(Path(temp_dir).glob("*.png")):
                        zip_file.write(img_file, img_file.name)
                
                zip_buffer.seek(0)
                
                # Download button
                st.download_button(
                    label=f"📥 ZIP 다운로드 ({success_count}개 이미지)",
                    data=zip_buffer,
                    file_name=f"images_{1:03d}-{total:03d}.zip",
                    mime="application/zip"
                )
            
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

# Instructions
with st.expander("ℹ️ 사용 방법"):
    st.markdown("""
    1. **API 키 입력**: [Google AI Studio](https://aistudio.google.com/apikey)에서 발급
    2. **프롬프트 입력**: 한 줄에 하나씩 (90개면 90줄)
    3. **스타일 입력** (선택): 모든 이미지에 적용할 공통 스타일
    4. **생성 시작** 클릭
    5. 완료 후 **ZIP 다운로드**
    
    ⚠️ **주의**: 이미지 1개당 1분씩 대기합니다 (API 제한)
    """)

st.markdown("---")
st.markdown("Made with ❤️ for 인생2막")
