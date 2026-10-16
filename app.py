import os
import urllib.request
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def get_korean_font():
    """한글 폰트(나눔고딕)가 없을 경우 서버/로컬 환경에 맞춰 자동 세팅합니다."""
    font_name = "NanumGothic"
    font_path = "NanumGothic.ttf"
    
    if not os.path.exists(font_path):
        # 윈도우 로컬 환경인 경우 시스템 폰트 활용
        if os.path.exists("C:/Windows/Fonts/malgun.ttf"):
            font_path = "C:/Windows/Fonts/malgun.ttf"
            font_name = "MalgunGothic"
        else:
            # 깃허브 / Streamlit Cloud 등 서버 환경인 경우 구글 폰트 자동 다운로드
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            try:
                urllib.request.urlretrieve(url, font_path)
            except Exception as e:
                raise FileNotFoundError(f"폰트 자동 다운로드 실패: {e}")

    pdfmetrics.registerFont(TTFont(font_name, font_path))
    return font_name

def create_text_pdf(title, content, filename="study_note.pdf"):
    font_name = get_korean_font()
    
    # A4 기준 양쪽 여백 50pt 설정 및 자동 페이지 레이아웃 객체 생성
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    # 문서 제목 스타일
    title_style = ParagraphStyle(
        'DocTitleStyle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=24,
        spaceAfter=15,
        textColor='#1A237E'
    )
    
    # 본문 텍스트 스타일 (CJK 자동 줄바꿈 적용으로 텍스트 짤림 방지)
    body_style = ParagraphStyle(
        'DocBodyStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10.5,
        leading=16,
        spaceAfter=6,
        wordWrap='CJK' 
    )
    
    story = []
    
    # 1. 제목 추가
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))
    
    # 2. 본문 줄 단위 처리 및 Paragraph 변환 (줄바꿈 및 마크업 안전 처리)
    lines = content.split('\n')
    for line in lines:
        if line.strip() == "":
            story.append(Spacer(1, 8))  # 빈 줄 간격 유지
        else:
            safe_line = (
                line.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
            )
            story.append(Paragraph(safe_line, body_style))
            
    # PDF 문서 빌드 (자동 페이지 넘김 처리 포함)
    doc.build(story)
    return filename

# --- Streamlit UI 화면 구성 ---
st.set_page_config(page_title="소방 서브노트 PDF 변환기", page_icon="📝", layout="centered")

st.title("📝 소방 서브노트 PDF 변환기")
st.write("공부한 내용이나 법령 요약 텍스트를 붙여넣으면 깔끔한 A4 PDF 노트로 변환해 드립니다.")

doc_title = st.text_input("문서 제목을 입력하세요", "소방시설관리사 핵심 요약 노트")
doc_content = st.text_area("내용을 붙여넣으세요", height=380, placeholder="여기에 공부한 내용을 입력하세요...")

if st.button("📄 PDF 생성 및 다운로드 준비", key="generate_pdf_btn"):
    if not doc_content.strip():
        st.warning("변환할 내용을 입력해 주세요!")
    else:
    # 탭으로 오류 분기 처리 및 다운로드 버튼 제공
        try:
            pdf_file = create_text_pdf(doc_title, doc_content, "study_note.pdf")
            with open(pdf_file, "rb") as f:
                st.success("✨ 한글 깨짐 없는 깔끔한 PDF 문서 생성이 완료되었습니다!")
                st.download_button(
                    label="📥 PDF 파일 다운로드", 
                    data=f, 
                    file_name=f"{doc_title.replace(' ', '_')}.pdf", 
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")