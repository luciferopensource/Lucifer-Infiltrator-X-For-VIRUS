FROM python:3.10-slim

WORKDIR /app

# Forces Python to print logs immediately
ENV PYTHONUNBUFFERED=1

# --- INSTALL SYSTEM DEPENDENCIES ---
# Added build-essential & python3-dev to compile C-extensions (tgcrypto/uvloop) on ARM64
# Replaced p7zip-full with 7zip (standard for modern Debian/Ubuntu)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    7zip \
    coreutils \
    build-essential \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "restrict_bot.py"]
