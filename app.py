import streamlit as st
from src.rag import MigrationAssistant
from src.monitoring import init_monitoring_db, save_feedback

init_monitoring_db()

st.set_page_config(
	page_title="Python Migration Assistant",
	layout="centered"
)

@st.cache_resource
def load_assistant():
	return MigrationAssistant()

def clear_inputs():
	st.session_state.question = ""
	st.session_state.user_code = ""
	st.session_state.conversation_id = None
	st.session_state.last_result = None
	st.session_state.feedback_given = False

with st.spinner("Loading AI Models..."):
	assistant = load_assistant()

if "question" not in st.session_state:
	st.session_state.question = ""

if "user_code" not in st.session_state:
    	st.session_state.user_code = ""

if "conversation_id" not in st.session_state:
    	st.session_state.conversation_id = None

if "last_result" not in st.session_state:
    	st.session_state.last_result = None

if "feedback_given" not in st.session_state:
    	st.session_state.feedback_given = False

st.title("Python Migration Assistant")
st.markdown("Upgrade your code for **FastAPI**, **Pydantic**, and **SQLAlchemy**")

st.sidebar.header("Filters")

selected_library = st.sidebar.radio(
	"Target Library:",
	["All", "fastapi", "pydantic", "sqlalchemy"]
)
library_filter = None if selected_library == "All" else selected_library

question = st.text_area(
	"What do you need help with?",
	key="question",
	height=100,
	placeholder="e.g., I'm migrating my data models from Pydantic v1 to v2. How do I rewrite my old @validator methods to the new Pydantic v2 syntax?"
)

user_code = st.text_area(
	"Paste your old code here (Optional):",
	key="user_code",
	height=150,
	placeholder="""from pydantic import BaseModel, validator

class User(BaseModel):
    age: int

    @validator("age")
    def check_age(cls, v):
        if v < 0:
            raise ValueError("Age must be non-negative")
        return v
"""
)

col1, col2 = st.columns([1, 1])
with col1:
	generate = st.button("Generate Guide", type="primary")
with col2:
	st.button("Clear", on_click=clear_inputs)

if generate:
	if not question.strip():
		st.warning("Please enter a question first!")
	else:
		with st.spinner("Searching official docs and generating response..."):
			try:
				result = assistant.answer_question(
					question=question,
					user_code=user_code,
					library=library_filter
				)
				st.session_state.last_result = result
				st.session_state.conversation_id = result.get("conversation_id")
				st.session_state.feedback_given = False
			except Exception as e:
				st.error(f"An error occurred while connecting to the OpenAI API: {str(e)}")
if st.session_state.last_result:
	result = st.session_state.last_result
	st.divider()

	if result.get("retrieved", 0) == 0:
		st.warning("No relevant migration guide was found.")
		st.markdown("Try:\n* Selecting another library\n* Using different keywords\n* Removing version numbers")
	else:
		st.markdown("### Answer")
		st.markdown(result["answer"])
		tokens_val = result['usage'].total_tokens if result.get('usage') else 0
		st.caption(f"⏱️ Time: {result['response_time']:.2f}s | 💰 Cost: ${result['cost']:.6f} | 🔤 Tokens: {tokens_val}")

		with st.expander(f"Retrived {result['retrieved']} documentation chunks"):
			for idx, source in enumerate(result["sources"], start=1):
				lib_name = source['library'].title()
				st.markdown(f"**{idx}. {lib_name} {source['version']}** — *{source['heading']}*  \n`{source['filename']}`")

		if st.session_state.conversation_id:
			st.write("---")
			st.write("Was this migration guide helpful?")
			f_col1, f_col2, _ = st.columns([1, 1, 8])

			with f_col1:
				if st.button("👍 +1"):
					save_feedback(st.session_state.conversation_id, score=1)
					st.session_state.feedback_given = True
					st.rerun()
			with f_col2:
				if st.button("👎 -1"):
					save_feedback(st.session_state.conversation_id, score=-1)
					st.session_state.feedback_given = True
					st.rerun()