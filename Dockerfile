FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/wdrax

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY wdra_extender wdra_extender/
COPY migrations migrations/
COPY settings.ini settings.ini

EXPOSE 8000

LABEL maintainer="j.graham@software.ac.uk, p.j.grylls@southampton.ac.uk"

ENV FLASK_APP="wdra_extender/app.py"
CMD [ "gunicorn", "wdra_extender.app:app", "--worker-tmp-dir", "/dev/shm", "--bind", "0.0.0.0:8000", "--workers", "4"]
