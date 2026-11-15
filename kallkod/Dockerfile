# CarDeps chattserver (och hela webbplatsen) i en container, t.ex. på Render, Fly.io eller Railway.
# Bygg webbplatsen och katalog.txt med python3 bygg.py innan du publicerar.
FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py katalog.txt ./
COPY app ./app
ENV HOST=0.0.0.0 PORT=8080 TRUST_PROXY=1 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
