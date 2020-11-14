FROM python:3.6
COPY . /telegram_bot
WORKDIR ./telegram_bot
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python bot.py
