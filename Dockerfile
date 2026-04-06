FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV JOB_SPY_DATA_DIR=/app/data
ENV PORT=8501

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY app.py /app/app.py
COPY docs /app/docs
COPY .streamlit /app/.streamlit
COPY scripts /app/scripts

RUN chmod +x /app/scripts/*.sh
RUN pip install --upgrade pip && pip install .

EXPOSE 8501

CMD ["/app/scripts/start_streamlit.sh"]
