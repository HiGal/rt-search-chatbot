import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import os
from model.context import Question

db_name = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')

connection = psycopg2.connect(
    database=db_name,
    user=db_user,
    password=db_password,
    host="questions_postgres_db",
    port="5432"
)

cursor = connection.cursor()


def prep():
    prep_query = "DROP TABLE IF EXISTS knowledge_base, vectors, unknown_questions"
    cursor.execute(prep_query)
    connection.commit()
    return True


def init():
    connection1 = create_engine(f"postgresql://{db_user}:{db_password}@questions_postgres_db:5432/{db_name}")
    df = pd.read_csv("./KB.csv")
    df.to_sql("knowledge_base", con=connection1)
    unique_query = """drop index ix_knowledge_base_index;
                        create unique index ix_knowledge_base_index
                            on knowledge_base (index);    
                        alter table knowledge_base
                            add constraint knowledge_base_pk
                                primary key (index);"""
    cursor.execute(unique_query)
    vectors_create_query = "CREATE TABLE IF NOT EXISTS vectors(" \
                           "index INT PRIMARY KEY REFERENCES knowledge_base(index)," \
                           "Вектор FLOAT[])"
    cursor.execute(vectors_create_query)
    unknown_create_query = "CREATE TABLE IF NOT EXISTS unknown_questions(" \
                           "index SERIAL PRIMARY KEY," \
                           "Вопрос TEXT," \
                           "Тип TEXT," \
                           "Запрос TEXT," \
                           "Предположение TEXT)"
    cursor.execute(unknown_create_query)
    connection.commit()


def push_unknown(context):
    cursor.execute('INSERT INTO unknown_questions("Вопрос", "Тип", "Запрос", "Предположение") '
                   'VALUES(%s, %s, %s, %s)', (context["original_question"], context["type"],
                                                  context["request"], context["suggestion"]))
    connection.commit()


def get_question(id):
    cursor.execute(f'SELECT * FROM knowledge_base WHERE index = {id}')
    db_inst = cursor.fetchone()
    question = Question(
        question=db_inst[4],
        answer=db_inst[5],
        type=db_inst[3],
        request=db_inst[1],
        suggestion=db_inst[2],
        distanse=0)
    return question
