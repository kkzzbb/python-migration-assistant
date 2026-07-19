import time
import streamlit as st
from src.rag import MigrationAssistant

st.set_page_config(
	page_title="Python Migration Assistant",
	layout="centered"
)

@st.cache_resource
def load_assistant():
	return MigrationAssistant()

with st.spinner("Loading AI Models..."):
	assistant = load_assistant()

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
	height=100,
	placeholder="e.g., I'm migrating a FastAPI project from 0.95 to 0.115. Why is Depends() no longer working inside my Annotated types?"
)

user_code = st.text_area(
	"Paste your old code here (Optional):",
	height=150,
	placeholder="class User(BaseModel:)\n	@validator('age')\n	def check_age(cls, v):\n	return v"
)

col1, col2 = st.columns([1, 5])
with col1:
	generate = st.button("Generate Guide", type="primary")
with col2:
	if st.button("Clear"):
		st.rerun()

if generate:
	if not question.strip():
		st.warning("Please enter a question first!")
	else:
		start_time = time.time()
		with st.spinner("Searching official docs and generating response..."):
			try:
				result = assistant.answer_question(
					question=question,
					user_code=user_code,
					library=library_filter
				)
				elapsed = time.time() - start_time
				st.divider()
				if result["retrieved"] == 0:
					st.warning("No relevant migration guide was found.")
					st.markdown("Try:\n* Selecting another library\n* Using different keywords\n* Removing version numbers")
				else:
					st.markdown("### Answer")
					st.markdown(result["answer"])
					st.caption(f"Completed in {elapsed:.2f} seconds")
					with st.expander(f"Retrived {result['retrieved']} documentation chunks"):
						for idx, source in enumerate(result["sources"], start=1):
							lib_name = source['library'].title()
							st.markdown(f"**{idx}. {lib_name} {source['version']}** — *{source['heading']}*  \n`{source['filename']}`")
			except Exception as e:
					st.error(f"An error occurred while connecting to the OpenAI API: {str(e)}")