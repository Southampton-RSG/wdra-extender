FROM python:3

WORKDIR /var/www/wdrax

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY wdra_extender wdra_extender/
COPY migrations migrations/

# TODO get settings from docker-compose
COPY settings.ini ./

EXPOSE 5000

ENV FLASK_APP="wdra_extender/app.py"
# TODO database in another container
RUN [ "python", "-m", "flask", "db", "upgrade" ]
CMD [ "python", "-m", "flask", "run" ]
