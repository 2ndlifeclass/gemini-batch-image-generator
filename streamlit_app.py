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
    layout="wide"
)

# Initialize session state
if 'generating' not in st.session_state:
    st.session_state.generating = False
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []

st.title("🎨 Gemini 배치 이미지 생성기")
st.markdown("**90분 대본용 이미지를 자동으로 생성합니다**")

# Left column: inputs, right column: preview
col1, col2 = st.columns([1, 1])

with col1:
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
        help="각 줄이 하나의 이미지로 생성됩니다",
        disabled=st.session_state.generating
    )

    # Style input
    style = st.text_input(
        "이미지 스타일 (선택사항)",
        placeholder="예: 따뜻한 일러스트, 파스텔톤",
        help="모든 이미지에 공통으로 적용될 스타일",
        disabled=st.session_state.generating
    )

    # Resolution
    resolution = st.selectbox(
        "해상도",
        options=["1K", "2K", "4K"],
        index=0,
        help="1K: 1024x1024, 2K: 2048x2048, 4K: 4096x4096",
        disabled=st.session_state.generating
    )

    # Control buttons
    button_col1, button_col2 = st.columns(2)
    
    with button_col1:
        if not st.session_state.generating:
            if st.button("🚀 생성 시작", type="primary", use_container_width=True):
                if not api_key:
                    st.error("❌ API 키를 입력해주세요")
                elif not prompts_text.strip():
                    st.error("❌ 프롬프트를 입력해주세요")
                else:
                    prompts = [p.strip() for p in prompts_text.strip().split('\n') if p.strip()]
                    if len(prompts) == 0:
                        st.error("❌ 유효한 프롬프트가 없습니다")
                    else:
                        st.session_state.generating = True
                        st.session_state.stop_requested = False
                        st.session_state.generated_images = []
                        st.session_state.temp_dir = tempfile.mkdtemp()
                        st.rerun()
    
    with button_col2:
        if st.session_state.generating:
            if st.button("⏹️ 중지", type="secondary", use_container_width=True):
                st.session_state.stop_requested = True
                st.warning("⏸️ 중지 요청됨... 현재 이미지 완료 후 중단됩니다")

with col2:
    st.subheader("📸 생성된 이미지 미리보기")
    preview_container = st.container()
    
    with preview_container:
        if st.session_state.generated_images:
            # Show latest images first
            for img_info in reversed(st.session_state.generated_images[-5:]):
                st.image(img_info['path'], caption=f"{img_info['idx']:03d}. {img_info['prompt'][:50]}...", use_container_width=True)
            
            if len(st.session_state.generated_images) > 5:
                st.info(f"📝 총 {len(st.session_state.generated_images)}개 생성됨 (최근 5개만 표시)")
        else:
            st.info("생성된 이미지가 여기에 표시됩니다")

# Main generation logic
if st.session_state.generating:
    # Parse prompts
    prompts = [p.strip() for p in prompts_text.strip().split('\n') if p.strip()]
    total = len(prompts)
    
    st.info(f"📝 총 {total}개 이미지를 생성합니다 (예상 시간: {total}분)")
    
    # Import Gemini
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        st.error("❌ google-genai 패키지가 설치되지 않았습니다")
        st.session_state.generating = False
        st.stop()
    
    # Initialize client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"❌ API 키 오류: {e}")
        st.session_state.generating = False
        st.stop()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Generate images
    success_count = len(st.session_state.generated_images)
    start_idx = success_count + 1
    failed_prompts = []
    
    for idx in range(start_idx, total + 1):
        # Check stop flag
        if st.session_state.stop_requested:
            status_text.warning(f"⏹️ 사용자가 중지했습니다 ({success_count}/{total}개 완료)")
            break
        
        prompt = prompts[idx - 1]
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
                    import base64
                    
                    # Get image data
                    image_data = part.inline_data.data
                    if isinstance(image_data, str):
                        image_data = base64.b64decode(image_data)
                    
                    # Load and save as PNG
                    image = PILImage.open(BytesIO(image_data))
                    
                    # Convert to RGB if needed
                    img_path = f"{st.session_state.temp_dir}/{idx:03d}.png"
                    if image.mode == 'RGBA':
                        rgb_image = PILImage.new('RGB', image.size, (255, 255, 255))
                        rgb_image.paste(image, mask=image.split()[3])
                        rgb_image.save(img_path, 'PNG')
                    elif image.mode == 'RGB':
                        image.save(img_path, 'PNG')
                    else:
                        image.convert('RGB').save(img_path, 'PNG')
                    
                    # Add to generated images list
                    st.session_state.generated_images.append({
                        'idx': idx,
                        'prompt': prompt,
                        'path': img_path
                    })
                    
                    image_saved = True
                    success_count += 1
                    
                    # Update preview immediately
                    st.rerun()
                    break
            
            if not image_saved:
                failed_prompts.append((idx, prompt, "응답에 이미지가 없음"))
        
        except Exception as e:
            failed_prompts.append((idx, prompt, str(e)))
        
        # Update progress
        progress_bar.progress(idx / total)
        
        # Wait 1 minute (except for last one or if stopped)
        if idx < total and not st.session_state.stop_requested:
            for remaining in range(60, 0, -1):
                status_text.text(f"⏳ 대기 중... {remaining}초 (다음: {idx+1}/{total})")
                time.sleep(1)
                if st.session_state.stop_requested:
                    break
    
    # Complete
    progress_bar.progress(1.0)
    st.session_state.generating = False
    
    if st.session_state.stop_requested:
        status_text.success(f"⏹️ 중지 완료! {success_count}/{total}개 생성됨")
    else:
        status_text.success("✅ 생성 완료!")
    
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
            for img_info in st.session_state.generated_images:
                zip_file.write(img_info['path'], f"{img_info['idx']:03d}.png")
        
        zip_buffer.seek(0)
        
        # Download button
        st.download_button(
            label=f"📥 ZIP 다운로드 ({success_count}개 이미지)",
            data=zip_buffer,
            file_name=f"images_{1:03d}-{total:03d}.zip",
            mime="application/zip"
        )
    
    # Reset for next generation
    if st.button("🔄 새로 시작"):
        st.session_state.generating = False
        st.session_state.stop_requested = False
        st.session_state.generated_images = []
        if st.session_state.temp_dir:
            shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
        st.session_state.temp_dir = None
        st.rerun()

# Instructions
with st.expander("ℹ️ 사용 방법"):
    st.markdown("""
    1. **API 키 입력**: [Google AI Studio](https://aistudio.google.com/apikey)에서 발급
    2. **프롬프트 입력**: 한 줄에 하나씩 (90개면 90줄)
    3. **스타일 입력** (선택): 모든 이미지에 적용할 공통 스타일
    4. **생성 시작** 클릭
    5. 오른쪽에서 **실시간 미리보기** 확인
    6. 중간에 멈추려면 **중지** 버튼 클릭
    7. 완료 후 **ZIP 다운로드**
    
    ⚠️ **주의**: 이미지 1개당 1분씩 대기합니다 (API 제한)
    """)

st.markdown("---")
st.markdown("Made with ❤️ for 인생2막")
