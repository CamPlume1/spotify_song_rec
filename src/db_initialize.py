from neo4j import GraphDatabase
import pandas as pd

df = pd.read_csv("C:/Users\Cam\Desktop\SP_24_Classes\DS_4300\hw5\spotify_song_rec\spotify\spotify.csv")

print(df.columns)

driver = GraphDatabase.driver("uri", auth=("username", "password"))

with driver.session() as session:
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        query = (
            "CREATE (n:Node {"
        )

        for key in row_dict.keys():
            val = '"' + str(row_dict[key]) + '"'
            query += f'{key}:{val},'
        query = query[:-1]
        query += "})"
        session.run(query)





