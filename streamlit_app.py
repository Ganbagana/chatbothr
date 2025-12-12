import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Recruiting Assistant", layout="wide")

# ---- Secrets ----
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---- Job catalog (жишээ) ----
JOBS = {
    "Давхар даатгалын менежер": {
        "description": "Давхар даатгалын гэрээ, нөхцөл, түншлэл, тайлан...",
        "screening_questions": [
            "Өмнө нь давхар даатгал/даатгалын чиглэлээр ажилласан туршлагаасаа товч ярьж өгнө үү.",
            "Гэрээ хэлэлцээр хийхэд ямар арга барил ашигладаг вэ?",
            "Excel/тайлан боловсруулах ур чадварын түвшингээ жишээгээр тайлбарлана уу."
        ],
    },
    "Хүний нөөцийн менежер": {
        "description": "Сонгон шалгаруулалт, сургалт хөгжүүлэлт, бодлого журам...",
        "screening_questions": [
            "Сонгон шалгаруулалтыг хэрхэн хэмжиж сайжруулж байсан туршлага байна уу?",
            "Хөдөлмөрийн харилцааны маргаан/асуудлыг хэрхэн шийдэж байсан бэ?",
            "HR analytics (KPI, retention, time-to-hire) ашиглаж байсан уу?"
        ],
    },
}

# ---- Session state ----
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Сайн байна уу! Би сонгон шалгаруулалтын туслах. Та ямар ажлын байранд горилж байна вэ?"}
    ]
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = []

# ---- Sidebar ----
with st.sidebar:
    st.header("Нээлттэй ажлын байр")
    job_name = st.selectbox("Ажлын байр сонгох", list(JOBS.keys()))
    st.caption(JOBS[job_name]["description"])
    if st.button("Энэ ажлыг сонгох"):
        st.session_state.selected_job = job_name
        st.session_state.q_index = 0
        st.session_state.answers = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Ок! **{job_name}** дээр эхний асуултаа асууя:\n\n{JOBS[job_name]['screening_questions'][0]}"
        })

# ---- Render chat ----
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Энд хариултаа бичнэ үү...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.selected_job:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Зүүн талын жагсаалтаас ажлын байраа сонгоод **'Энэ ажлыг сонгох'** дээр дарна уу."
        })
    else:
        # хадгалах
        st.session_state.answers.append({
            "question": JOBS[st.session_state.selected_job]["screening_questions"][st.session_state.q_index],
            "answer": prompt
        })
        st.session_state.q_index += 1

        questions = JOBS[st.session_state.selected_job]["screening_questions"]
        if st.session_state.q_index < len(questions):
            st.session_state.messages.append({
                "role": "assistant",
                "content": questions[st.session_state.q_index]
            })
        else:
            # Эцсийн summary-г AI-аар гаргуулж болно
            if not client:
                st.session_state.messages.append({"role": "assistant", "content": "API key байхгүй байна."})
            else:
                summary_prompt = f"""
Та HR туслах. Доорх Q/A дээр үндэслээд 5-7 өгүүлбэртэй товч дүгнэлт гарга.
Ажлын байр: {st.session_state.selected_job}

Асуулт/Хариултууд:
{st.session_state.answers}
"""
                resp = client.responses.create(
                    model="gpt-4.1-mini",
                    input=[
                        {"role": "system", "content": "Та бодитой, шударга HR screening assistant."},
                        {"role": "user", "content": summary_prompt},
                    ],
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Баярлалаа! Таны мэдээллийг хүлээн авлаа.\n\n**Товч дүгнэлт:**\n\n" + resp.output_text
                })

    # rerun to show assistant message immediately
    st.rerun()
