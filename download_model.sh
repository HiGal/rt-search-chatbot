curl --progress-bar --request GET -L \
     --url 'files.deeppavlov.ai/deeppavlov_data/bert/rubert_cased_L-12_H-768_A-12_v1.tar.gz'\
     --output './data/rubert_cased_L-12_H-768_A-12_v1.tar.gz'
tar -C ./data -xzf ./data/rubert_cased_L-12_H-768_A-12_v1.tar.gz
rm ./data/rubert_cased_L-12_H-768_A-12_v1.tar.gz