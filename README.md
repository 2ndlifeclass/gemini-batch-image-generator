# Gemini 배치 이미지 생성기

90분 대본용 이미지를 자동으로 생성하는 도구

## 버전

### 🌐 웹 버전 (Streamlit)
- 브라우저에서 바로 사용
- URL만 공유하면 끝
- 설치 불필요

### 💻 로컬 프로그램 (GUI)
- Windows/macOS 지원
- 인터넷만 있으면 사용 가능
- 다운로드해서 실행

## 기능

- 프롬프트 여러 개 입력 (1~90개)
- Gemini 3 Pro Image로 16:9 이미지 생성
- 1분 간격 자동 생성
- 진행률 실시간 표시
- 완료 시 ZIP 다운로드

## 웹 버전 사용법

### 로컬 실행

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Streamlit Cloud 배포

1. GitHub에 푸시
2. https://share.streamlit.io 접속
3. 레포지토리 연결
4. `streamlit_app.py` 지정
5. Deploy 클릭

## GUI 버전 사용법

### 다운로드

[Releases](https://github.com/2ndlifeclass/gemini-batch-image-generator/releases)에서 다운로드:
- Windows: `GeminiImageGenerator.exe`
- macOS: `GeminiImageGenerator.app`

### 빌드 (개발자용)

**Windows:**
```bash
build-windows.bat
```

**macOS:**
```bash
./build-macos.sh
```

빌드된 파일은 `dist/` 폴더에 생성됩니다.

### 로컬 개발 실행

```bash
pip install -r requirements-gui.txt
python app.py
```

## API 키 발급

https://aistudio.google.com/apikey

## 시니어 사용 가이드

### 웹 버전
1. URL 접속
2. API 키 입력 (최초 1회)
3. 프롬프트 붙여넣기 (한 줄에 하나씩)
4. 생성 시작 버튼 클릭
5. ZIP 다운로드

### GUI 버전
1. 프로그램 실행 (더블클릭)
2. API 키 입력
3. 프롬프트 붙여넣기
4. 생성 시작 버튼 클릭
5. ZIP 다운로드 (저장 위치 선택)

---

Made with ❤️ for 인생2막
