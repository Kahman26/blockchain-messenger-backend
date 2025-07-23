FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y gcc build-essential libffi-dev libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main"]
