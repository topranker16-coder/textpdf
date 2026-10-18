import streamlit as st
import re
import os
import urllib.request
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 페이지 설정
st.set_page_config(
    page_title="📄 대화&노트 ➔ 고품질 PDF 변환기",
    page_icon="📝",
    layout="centered"
)

# 한글 폰트(나눔고딕) 다운로드 및 등록
FONT_PATH = "NanumGothic.ttf"
def ensure_korean_font():
    if not os.path.exists(FONT_PATH):
        font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(font_url, FONT_PATH)
    pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))

# 마크다운 서식을 ReportLab HTML 태그로 변환
def md_to_rl_html(text):
    if not text:
        return ""
    # XML 특수문자 이스케이프
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # **볼드** -> <b>볼드</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # *이탈릭* -> <i>이탈릭</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # 줄바꿈 -> <br/>
    text = text.replace('\n', '<br/>')
    return text

# 대화/텍스트 파싱 함수
def parse_chat_text(raw_text):
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    sections = []
    current_q = ""
    current_a_lines = []
    
    for line in lines:
        if re.match(r'^(Q[\.:\d]|질문|문제|User|사용자|\\[문제\\]|Q\d+)', line, re.IGNORECASE) or any(line.startswith(p) for p in ["Q.", "Q:", "[질문]", "[문제]"]):
            if current_q or current_a_lines:
                sections.append({"q": current_q if current_q else "주요 노트 내용", "a": "\n".join(current_a_lines)})
                current_a_lines = []
            current_q = re.sub(r'^(Q[\.:\d]|질문|문제|User|사용자|\\[문제\\]|Q\d+)\s*', '', line, flags=re.IGNORECASE).strip()
        elif re.match(r'^(A[\.:\d]|답변|답|Gemini|AI|모범답안|\\[답변\\]|\\[모범답안\\])', line, re.IGNORECASE):
            if not current_q and current_a_lines:
                sections.append({"q": "주요 핵심 요약", "a": "\n".join(current_a_lines)})
                current_a_lines = []
            clean_a = re.sub(r'^(A[\.:\d]|답변|답|Gemini|AI|모범답안|\\[답변\\]|\\[모범답안\\])\s*', '', line, flags=re.IGNORECASE).strip()
            if clean_a:
                current_a_lines.append(clean_a)
        else:
            if not current_q:
                current_q = line
            else:
                current_a_lines.append(line)
                
    if current_q or current_a_lines:
        sections.append({"q": current_q if current_q else "공부노트 정리", "a": "\n".join(current_a_lines)})
        
    return sections

# ReportLab 고품질 PDF 생성 함수
def build_reportlab_pdf(title, sections):
    ensure_korean_font()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )
    
    usable_w = A4[0] - 30 * mm
    
    # 스타일 정의
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='NanumGothic',
        fontSize=18,
        leading=22,
        textColor=HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=12
    )
    
    q_style = ParagraphStyle(
        'QStyle',
        fontName='NanumGothic',
        fontSize=11,
        leading=16,
        textColor=HexColor('#1e3a8a')
    )
    
    a_style = ParagraphStyle(
        'AStyle',
        fontName='NanumGothic',
        fontSize=10,
        leading=16,
        textColor=HexColor('#334155'),
        spaceBefore=6,
        spaceAfter=10
    )
    
    story = []
    
    # 문서 제목
    story.append(Paragraph(f"<b>{md_to_rl_html(title)}</b>", title_style))
    story.append(Spacer(1, 10))
    
    # Q&A 세트 구성
    for idx, sec in enumerate(sections, 1):
        q_html = md_to_rl_html(f"Q{idx}. {sec['q']}")
        a_html = md_to_rl_html(sec['a'])
        
        # 질문 박스 (테이블 스타일)
        q_para = Paragraph(f"<b>{q_html}</b>", q_style)
        q_table = Table([[q_para]], colWidths=[usable_w])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#eff6ff')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINELEFT', (0, 0), (0, 0), 4, HexColor('#2563eb')),
        ]))
        
        # 답변 파라그래프
        a_para = Paragraph(a_html, a_style)
        
        # 질문과 답변을 묶어 한 페이지에서 어색하게 쪼개지지 않도록 설정
        item_group = KeepTogether([q_table, Spacer(1, 4), a_para, Spacer(1, 10)])
        story.append(item_group)
        
    # 헤더 및 푸터 콜백
    def add_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('NanumGothic', 8)
        canvas.setFillColor(HexColor('#94a3b8'))
        # 상단 헤더
        canvas.drawString(15 * mm, A4[1] - 12 * mm, "🔥 소방시설관리사 핵심 공부노트")
        canvas.setStrokeColor(HexColor('#e2e8f0'))
        canvas.setLineWidth(0.5)
        canvas.line(15 * mm, A4[1] - 14 * mm, A4[0] - 15 * mm, A4[1] - 14 * mm)
        # 하단 푸터 (페이지 번호)
        canvas.drawCentredString(A4[0] / 2, 10 * mm, f"- {doc.page} -")
        canvas.restoreState()
        
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    
    buffer.seek(0)
    return buffer.getvalue()

# Streamlit UI
st.title("📝 대화&노트 ➔ 고품질 PDF 변환기")
st.caption("강조(**볼드**)와 줄바꿈이 완벽히 유지되는 고품질 공부노트 PDF를 생성합니다.")

doc_title = st.text_input("📄 PDF 문서 제목:", "소방시설관리사 2차 실기 핵심 요약노트")

raw_input = st.text_area(
    "📋 대화/노트 텍스트 복사-붙여넣기:",
    height=250,
    placeholder="마우스로 긁은 채팅 대화나 **강조가 들어간 텍스트**를 여기에 붙여넣으세요..."
)

if raw_input.strip():
    parsed_sections = parse_chat_text(raw_input)
    
    st.subheader(f"🔍 자동 정돈 미리보기 (총 {len(parsed_sections)}개 항목)")
    for i, sec in enumerate(parsed_sections, 1):
        with st.expander(f"📌 [{i}] {sec['q'][:35]}...", expanded=True):
            st.markdown(f"**질문:** {sec['q']}")
            st.markdown(f"**답변:**\n{sec['a']}")
            
    try:
        pdf_bytes = build_reportlab_pdf(doc_title, parsed_sections)
        st.download_button(
            label="📥 고품질 PDF 공부노트 다운로드",
            data=pdf_bytes,
            file_name=f"{doc_title.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary"
        )
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")
