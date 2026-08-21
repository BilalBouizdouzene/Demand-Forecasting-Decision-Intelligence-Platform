FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY src ./src
COPY frontend ./frontend
COPY configs ./configs
COPY results ./results

RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "demand_intelligence.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
