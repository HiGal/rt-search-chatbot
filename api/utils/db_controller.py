import psycopg2
import pandas as pd
from sqlalchemy import create_engine
db_name = "questions"
db_user = "farit_priglasil"
db_password = "f4r17_pr1gl451l"

connection = psycopg2.connect(
    database=db_name,
    user=db_user,
    password=db_password,
    host="127.0.0.1",
    port="5432"
)

cursor = connection.cursor()


def prep():
    prep_query = "DROP TABLE IF EXISTS knowledge_base, vectors, unknown_questions"
    cursor.execute(prep_query)
    connection.commit()
    return True


def init():
    connection1 = create_engine(f"postgresql://{db_user}:{db_password}@localhost:5432/{db_name}")
    df = pd.read_csv("../KB.csv")
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
                           "Вопрос TEXT)"
    cursor.execute(unknown_create_query)
    connection.commit()


cursor.execute('SELECT "Ответ" FROM knowledge_base WHERE index = %s', (171, ))
answer_text = cursor.fetchone()[0]
print(answer_text)