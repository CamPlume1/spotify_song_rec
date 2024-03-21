# Installing Libraries 
from neo4j import GraphDatabase
import pandas as pd
import math
from sklearn.preprocessing import StandardScaler

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

# Function to load df and process the data before being transformed into a graphical database 
# Ensures to add the songs of interest
def load_data(file_path, size, songs_of_interest=False):

    # Load CSV file into a DataFrame
    spotify_df = pd.read_csv(file_path) 

    # Remove duplicates
    spotify_df.drop_duplicates(inplace=True)

    # Takes a sample of the spotify_df
    df = spotify_df.sample(size)

    # Adds songs_of_interest to the cleaned spotify df 
    if songs_of_interest:
        songs_of_interest_df = spotify_df[spotify_df['track_id'].isin(songs_of_interest)]

        # Get the distinct list of artists based on track_ids
        artists_list = spotify_df[spotify_df['track_id'].isin(songs_of_interest)]['artists'].unique()

        # Get the distinct list of track genres based on track_ids
        genres_list = spotify_df[spotify_df['track_id'].isin(songs_of_interest)]['track_genre'].unique()

        # Filter the DataFrame to keep only the rows where an artist wasn't apart of the recommended songs 
        df = spotify_df[~spotify_df['artists'].isin(artists_list)]

        # Filter the DataFrame to keep only the rows where the track genre is the same as one of the recommended songs 
        df = df[df['track_genre'].isin(genres_list)]

        # Takes a sample of the spotify_df
        df = df.sample(size)

        # Concats the list and removes duplicates 
        df = pd.concat([df, songs_of_interest_df])
        df = df.drop_duplicates(subset='track_id')

    # List of features used for when standardizing 
    feats = ['popularity', 'duration_ms', 'explicit', 'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness','acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']

    # Standardize the features
    scaler = StandardScaler()
    df[feats] = scaler.fit_transform(df[feats])

    return df

# Given the spotify CSV file, loads the data into Neo4j
def to_neo4j(df, driver, recommended_songs_track_ids):

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
                time_signature: toInteger($time_signature)
            })
            """

            # Execute the Cypher query for each row
            session.run(query, parameters=dict(row))

             # List of features used for when calcualating Euclidian distance 
            feats = ['popularity', 'duration_ms', 'explicit', 'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness','acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']

            # Calculate Euclidean distance between current node and all other nodes
            for inner_index, inner_row in df.iterrows():

                # Doesn't calculate distance with itself 
                if inner_index != index:  

                    # Doesn't draw a connection between two recommended songs 
                    if inner_row['track_id'] in recommended_songs_track_ids:
                        continue
                     
                    distance = math.sqrt(sum((row[feat] - inner_row[feat]) ** 2 for feat in feats))

                    # Assures the two song have a decent similarity by making sure they have a close distance 
                    if 0 < distance < 3:
                        # Create relationship with distance as a property
                        create_relationship_query = """
                        MATCH (a:Song {track_id: $current_track_id}), (b:Song {track_id: $other_track_id})
                        CREATE (a)-[:IS_SIMILAR_TO {value: $distance}]->(b)
                        """
                        session.run(create_relationship_query, parameters={
                            'current_track_id': row['track_id'],
                            'other_track_id': inner_row['track_id'],
                            'distance': distance
                    })

# Gets the recommended track names and relationship values given the track_id                  
def get_recommended_track_names(driver, track_ids):

    all_related_tracks = []

    with driver.session() as session:
        for track_id in track_ids:

            # Cypher query to find related track names and relationship values where the specific node is pointing to other nodes
            query_outgoing = """
            MATCH (:Song {track_id: $track_id})-[rel:IS_SIMILAR_TO]->(other:Song)
            RETURN other.track_name AS related_track_name, rel.value AS relationship_value
            """
        
            # Cypher query to find related track names and relationship values where other nodes are pointing to the specific node
            query_incoming = """
            MATCH (other:Song)-[rel:IS_SIMILAR_TO]->(:Song {track_id: $track_id})
            RETURN other.track_name AS related_track_name, rel.value AS relationship_value
            """
        
            # Execute the Cypher queries
            result_outgoing = session.run(query_outgoing, track_id=track_id)
            result_incoming = session.run(query_incoming, track_id=track_id)
        
            # Extract related track names and relationship values from the result
            outgoing_related_tracks = [(record["related_track_name"], record["relationship_value"]) for record in result_outgoing]
            incoming_related_tracks = [(record["related_track_name"], record["relationship_value"]) for record in result_incoming]

            # Adds the track recommendations for the current liked track to the list of all recommended tracks
            current_related_tracks = outgoing_related_tracks + incoming_related_tracks
            all_related_tracks.extend(current_related_tracks)

        # Sort by most similar
        all_related_tracks.sort(key=lambda x: x[1])

        # Drops the relationship value in each tuple so its just track names and drops duplicates 
        recommended_tracks = [track_name for track_name, value in all_related_tracks]
        recommended_tracks = list(set(recommended_tracks))

        # Returns the 5 most similar songs 
        final_recommendations = recommended_tracks[:5]

        return final_recommendations