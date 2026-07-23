import streamlit as st
import pandas as pd
from src.monitoring import get_stats, init_monitoring_db, get_recent_conversations, get_db_connection

init_monitoring_db() 

st.set_page_config(layout="wide", page_title="Telemetry Dashboard")
st.title("📊 Migration Assistant Telemetry")

if st.button("🔄 Refresh Telemetry"):
    st.rerun()

stats = get_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Conversations", stats.total)
col2.metric("Avg Response Time", f"{stats.avg_response_time:.2f}s")
col3.metric("Total Cost", f"${stats.total_cost:.4f}")
col4.metric("Avg Tokens", f"{stats.avg_tokens:.0f}")

st.write("---")

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
        
	st.write("---")
	
	col_chart3, col_chart4, col_chart5 = st.columns(3)
	
	with col_chart3:
		st.subheader("3. Per-Library Volume")
		if "library" in df.columns:
			lib_counts = df["library"].value_counts()
			st.bar_chart(lib_counts)
	
	with col_chart4:
		st.subheader("4. Token Usage Distribution")
		if "total_tokens" in df.columns:
			st.scatter_chart(df, x="response_time", y="total_tokens")
			    
	with col_chart5:
		st.subheader("5. Feedback Score Distribution")
		conn = get_db_connection()
		feedback_df = pd.read_sql("SELECT score, COUNT(*) as count FROM feedback GROUP BY score", conn)
		conn.close()
		if not feedback_df.empty:
			score_map = {1: "Positive (+1)", -1: "Negative (-1)"}
			feedback_df["Feedback"] = feedback_df["score"].map(score_map).fillna(feedback_df["score"].astype(str))
			st.bar_chart(feedback_df, x="Feedback", y="count")
		else:
			st.info("No feedback recorded yet.")
	
	st.subheader("Recent Conversations")
	for record in records[:10]:
		st.markdown(f"**Q:** {record['question'][:100]}...")
		st.caption(f"Time: {record['response_time']:.2f}s | Cost: ${record['cost']:.6f} | Library: {record['library']}")
		st.divider()
else:
	st.info("No conversations logged yet. Ask the assistant a question to see data!")