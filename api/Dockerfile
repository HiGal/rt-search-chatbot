FROM python:3.6
COPY . /python-app
WORKDIR ./python-app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python main.py
