# Usar imagen oficial de Python con Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# Directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY main.py .

# Exponer puerto
EXPOSE 8080

# Variables de entorno para Cloud Run
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
