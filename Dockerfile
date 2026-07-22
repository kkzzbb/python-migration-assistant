FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./

RUN uv pip install --system --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cpu -r pyproject.toml

COPY . .

EXPOSE 8501 8502

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]