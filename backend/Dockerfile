# Lightweight Python with official Playwright Linux deps
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

# Copy requirements & install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chromium only (to keep image light)
RUN playwright install chromium

# Copy app source code
COPY . .

# Expose port (Render/Railway sets PORT dynamically)
ENV PORT=8000
EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]