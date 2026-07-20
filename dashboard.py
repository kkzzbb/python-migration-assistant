import streamlit as st
import pandas as pd
from src.monitoring import get_stats, get_recent_conversations

st.set_page_config(layout="wide", page_title="Telemetry Dashboard")
st.title("📊 Migration Assistant Telemetry")

stats = get_stats()

# Top Level Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Conversations", stats.total)
col2.metric("Avg Response Time", f"{stats.avg_response_time:.2f}s")
col3.metric("Total Cost", f"${stats.total_cost:.4f}")
col4.metric("Avg Tokens", f"{stats.avg_tokens:.0f}")

st.write("---")

# Charts and Data
records = get_recent_conversations(limit=100)

if records:
	df = pd.DataFrame(records)
    
	col_chart1, col_chart2 = st.columns(2)
	with col_chart1:
		st.subheader("Cost over time")
		st.line_chart(df, x="timestamp", y="cost")
		
	with col_chart2:
		st.subheader("Response time over time")
		st.line_chart(df, x="timestamp", y="response_time")
        
	st.subheader("Recent Conversations")
	for record in records[:10]:
		st.markdown(f"**Q:** {record['question'][:100]}...")
		st.caption(f"Time: {record['response_time']:.2f}s | Cost: ${record['cost']:.6f} | Library: {record['library']}")
		st.divider()
else:
	st.info("No conversations logged yet. Ask the assistant a question to see data!")