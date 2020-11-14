# Leaders_of_digital_Farit_priglasil

## Клонирование репозитория
```
git clone https://github.com/HiGal/rt-search-chatbot.git
cd rt-search-chatbot
```
## Скачивание ИИ-модели
*Так как модель весит ~700MB, внутри репозитория ее нет* 
1. Запустите готовый sh скрипт, чтобы скачать модель:
    ```
    chmod u+x download_model.sh
    sh download_model.sh 
    ```
2. **Или** скачайте файл вручную отсюда:  
http://files.deeppavlov.ai/deeppavlov_data/bert/rubert_cased_L-12_H-768_A-12_v1.tar.gz,
Затем распакуйте tar.gz архив и поместите содержимое в директорию `/data`.  

    В конечном итоге должна получиться структура  
`rt-search-chatbot/data/rubert_cased_L-12_H-768_A-12_v1/*`

## Запуск проекта
```
docker-compose up
```
Ожидайте, пока поднимутся все контейнеры (при запуске так же заполняется БД с базой знаний и векторным представлением вопросов, поэтому время запуска может быть относительно большим), маркером успешного старта и инициализации проекта является строчка "*all set, ready to serve request!*" в самом конце:  
![](https://i.imgur.com/5rCeR3j.png)


## Пример запроса в API
```
curl -X POST "http://127.0.0.1:8000/bot/v1/question/1" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{\"question\":\"В какое время в течение дня происходит подключение к интернету?\"}" 
```

## Пример ответа
* Готовый ответ
```json=
{
  "id": "1",
  "type": "final",
  "answer": "Подключение к Интернету происходит ежедневно, в том числе и в выходные дни с 09:00 до 21:00. Предварительно сотрудники Контакт - центра за один день до подключения согласуют с Вами день приезда монтажника.",
  "options": null
}
```

* Ответ требующий уточнения
```json=
{
  "id": "1",
  "type": "clarification",
  "answer": "Вас интересует:",
  "options": ["Диагностика и настройка оборудования/подключения", "Оплата услуг", "Другое"]
}
```

* Перевод на оператора
```json=
{
  "id": "1",
  "type": "operator",
  "answer": "Ответ не найден, переводим Вас на оператора",
  "options": null
}
```


## Краткое описание работы программы

Поиск по базе знаний идет так же как и поиск запросов в поисковике (Google, Яндекс и т.п.)

1. Языковая модель RuBERT индексирует базу знаний при запуске сервиса
2. Поисковой запрос пользователя так же переводится к векторному представлению при помощи той же модели (помогает избежать возможные орфографические ошибки, а так же понимать семантику запроса независимо от используемых синонимов)
3. Система удовлетворяет следующим Quality Attributes - Reliability, Scalability (вертикальная и горизонтальная).
4. Языковая модель может быть слегкостью заменена (для этого нужно будет изменить файлы в директории `rt-search-chatbot/data/rubert_cased_L-12_H-768_A-12_v1/` на данные типа tf_models (сохраненная модель Tensorflow)) или же наоборот дополнена моделью обученной для специфического задания (например классификация, ведение диалога, нахождения конкретной строчки ответа по данному запросу и т.д.)

## **Демо-видео работы API и бота:**  
https://drive.google.com/drive/folders/1wrsE2hhHC3qi5_3MhWaB1Qlh45whbIiP
