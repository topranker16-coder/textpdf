import streamlit as st
import re
from fpdf import FPDF

# 페이지 기본 설정
st.set_page_config(
    page_title="📄 대화&노트 텍스트 -> PDF 깔끔 변환기",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS 스타일링
st.markdown('''
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    .main .block-container {
        max-width: 540px !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    div.stButton > button {
        width: 100% !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        padding: 12px 0px !important;
    }
</style>
''', unsafe_allow_html=True)

# 한국어 PDF 생성 클래스
class KoreanPDF(FPDF):
    def __init__(self, title="소방시설관리사 공부노트"):
        super().__init__()
        self.doc_title = title
        self.add_page()
        # 한글 폰트 등록 (NotoSansKR / 나눔고딕)
        self.add_font("NotoSansKR", "", "/usr/share/fonts/truetype/noto-cjk/NotoSansKR-Regular.ttf")

    def header(self):
        self.set_font("NotoSansKR", size=9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, f"🔥 소방시설관리사 핵심 대화&공부노트 | {self.doc_title}", border=0, align="L")
        self.ln(4)
        self.set_draw_color(226, 232, 240)
        self.line(10, 15, 200, 15)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("NotoSansKR", size=9)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"- {self.page_no()} -", border=0, align="C")

# 대화/텍스트 파싱 함수
def parse_chat_text(raw_text):
    text = re.sub(r'\*{2,}', '', raw_text)  # 마크다운 볼드 제거
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
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

# PDF 바이너리 생성 함수
def build_pdf_bytes(title, sections):
    pdf = KoreanPDF(title=title)
    
    pdf.set_font("NotoSansKR", size=15)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 10, title, align="C")
    pdf.ln(4)
    
    pdf.set_draw_color(37, 99, 235)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    for idx, sec in enumerate(sections, 1):
        q_text = sec["q"]
        a_text = sec["a"]
        
        # 질문 상자
        pdf.set_font("NotoSansKR", size=11)
        pdf.set_text_color(30, 58, 138)
        pdf.set_fill_color(239, 246, 255)
        pdf.multi_cell(0, 8, f"Q{idx}. {q_text}", fill=True, border=1)
        pdf.ln(2)
        
        # 답변 내용
        if a_text:
            pdf.set_font("NotoSansKR", size=10)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 6, a_text)
            
        pdf.ln(6)
        
    return bytes(pdf.output())

# Streamlit UI
st.title("📝 대화&노트 텍스트 ➔ PDF 깔끔 변환기")
st.caption("마우스로 긁어서 붙여넣은 대화 내용이나 요약 노트를 소방시설관리사 공부용 PDF로 정돈해 드립니다!")

doc_title = st.text_input("📄 PDF 문서 제목:", "소방시설관리사 2차 실기 핵심 대화 노트")

raw_input = st.text_area(
    "📋 대화/노트 텍스트 복사-붙여넣기:",
    height=250,
    placeholder="마우스로 긁은 채팅 대화나 질문/답변 텍스트를 여기에 붙여넣으세요..."
)

if raw_input.strip():
    parsed_sections = parse_chat_text(raw_input)
    
    st.subheader(f"🔍 자동 정돈 미리보기 (총 {len(parsed_sections)}개 항목)")
    
    for i, sec in enumerate(parsed_sections, 1):
        with st.expander(f"📌 [{i}] {sec['q'][:35]}...", expanded=True):
            st.markdown(f"**질문/주제:** {sec['q']}")
            st.markdown(f"**내용/답변:**\n{sec['a']}")
            
    try:
        pdf_data = build_pdf_bytes(doc_title, parsed_sections)
        st.download_button(
            label="📥 깔끔하게 정리된 PDF 파일 다운로드",
            data=pdf_data,
            file_name=f"{doc_title.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary"
        )
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")
