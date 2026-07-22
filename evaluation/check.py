import pandas as pd
df = pd.read_csv("data/evaluation/version_blending_evaluations.csv")

# Filter where RAG failed but Baseline passed
failures = df[(df['rag_has_legacy_syntax'] == True) & (df['baseline_has_legacy_syntax'] == False)]

print(f"Found {len(failures)} cases where RAG failed but Baseline succeeded.\n")
for idx, row in failures.head(5).iterrows():
    print(f"Question: {row['question']}")
    print(f"Judge Reasoning: {row['rag_reasoning']}")
    print("-" * 50)