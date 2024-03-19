# Installing Libraries 
from neo4j import GraphDatabase
import pandas as pd

# Function to connect to Neo4j
def connect_to_neo4j(uri, username, password):

    # Establish connection to Neo4j database
    driver = GraphDatabase.driver(uri, auth=(username, password))

    # Start a session
    with driver.session() as session:

        # Cypher query to delete all nodes and relationships
        query = "MATCH (n) DETACH DELETE n"

        # Execute the Cypher query
        session.run(query)

    return driver

# Given the spotify CSV file, loads the data into Neo4j
def load_to_neo4j(file_path, size, driver):

    # Load CSV file into a DataFrame
    spotify_df = pd.read_csv(file_path) 

    df = spotify_df[0:size]

    # Iterate over the dataframe's rows and create nodes in Neo4j
    with driver.session() as session:
        for index, row in df.iterrows():
            # Construct Cypher query for creating node
            query = """
            CREATE (:Song {
                track_id: $track_id,
                artists: $artists,
                album_name: $album_name,
                track_name: $track_name,
                popularity: toInteger($popularity),
                duration_ms: toInteger($duration_ms),
                explicit: $explicit,
                danceability: toFloat($danceability),
                energy: toFloat($energy),
                key: toInteger($key),
                loudness: toFloat($loudness),
                mode: toInteger($mode),
                speechiness: toFloat($speechiness),
                acousticness: toFloat($acousticness),
                instrumentalness: toFloat($instrumentalness),
                liveness: toFloat($liveness),
                valence: toFloat($valence),
                tempo: toFloat($tempo),
                time_signature: toInteger($time_signature),
                track_genre: $track_genre
            })
            """

            # Execute the Cypher query for each row
            session.run(query, parameters=dict(row))


# Main script
def main():

    # Neo4j connection details
    neo4j_uri = "neo4j://localhost:7687"    
    neo4j_username = "neo4j"    
    neo4j_password = "password"

    # Connect to Neo4j
    driver = connect_to_neo4j(neo4j_uri, neo4j_username, neo4j_password)   

    # PFile Path to Spotify CSV File
    file_path = "spotify/spotify.csv"

    # Testing 
    load_to_neo4j(file_path, 15, driver)
    
    # Close the Neo4j driver
    driver.close()

if __name__ == '__main__':
    main()
