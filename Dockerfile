FROM python:3.11

WORKDIR /usr/src/bot

COPY . .

VOLUME ["/usr/src/bot/database"]

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]