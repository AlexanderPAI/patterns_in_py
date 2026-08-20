FROM python:3.9-slim-buster

WORKDIR /code

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /code/

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=src.allocation.entrypoints.flask_app:app \
    FLASK_DEBUG=1

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5005"]