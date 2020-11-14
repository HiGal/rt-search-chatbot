FROM python:3.6
COPY . /indexer
WORKDIR ./indexer
RUN pip install -r requirements.txt
RUN pip install -U bert-serving-server[http]
EXPOSE 8125
CMD bert-serving-start -model_dir=./rubert_cased_L-12_H-768_A-12_v1 -http_port 8125 -max_seq_len 100