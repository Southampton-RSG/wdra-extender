FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/wdrax

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY wdra_extender wdra_extender/
COPY migrations migrations/

EXPOSE 8000

LABEL maintainer="j.graham@software.ac.uk"

CMD [ "gunicorn", "wdra_extender.app:app", "--worker-tmp-dir", "/dev/shm", "--bind", "0.0.0.0:8000" ]
