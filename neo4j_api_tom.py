from neo4j import GraphDatabase
import pandas as pd
from sklearn.preprocessing import StandardScaler

class Neo4J_API:    

    # Instantiate connection
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        # Cypher query to delete all nodes and relationships
        query = "MATCH (n) DETACH DELETE n"

            # Execute the Cypher query
        self.driver.session().run(query)

    # Create dataset that will be uploaded to Neo4j
    # Create dataset that will be uploaded to Neo4j
    def sample_dataset(self, filepath, size, song_name, artist):
        # Read CSV from specified filepath, and drop all duplicates
        df = pd.read_csv(filepath)
        df.drop_duplicates(inplace=True)

        # Retrieve Song
        song = df[df['track_name'] == song_name]
        song = df[(df['track_name'] == song_name) & (df['artists'] == artist)]
        # Retreive Album
        album = song['album_name'].values[0]

        # Create first dataframe that only contains the songs from the given songs album
        condition = df['album_name'] == album
        df_1 = df[condition]        

        # get a list of all genres on the album
        genres = df_1['track_genre'].tolist()
        genres = list(set(genres))
        # Retrieve a track_list to return for recommendations
        track_list = df_1['track_id'].tolist()

        # Filter dataframe so that it has all genres on the given songs album
        df_2 = df[~df['track_genre'].isin(genres)]
        # Randomly sample the dataframe
        df_2 = df.sample(size)

        # Concat the two dataframes together and drop duplicates
        spotify_df = pd.concat([df_1,df_2])
        spotify_df.drop_duplicates(inplace=True)

        # List of features used for when standardizing 
        feats = ['popularity', 'duration_ms', 'explicit', 'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness','acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']

        # Standardize the features
        scaler = StandardScaler()
        spotify_df[feats] = scaler.fit_transform(spotify_df[feats])

        return spotify_df, track_list  

    # Loads data to Neo4j, creating both Nodes and Edges
    def load_data(self, df):
        # Define features that will be used to compare song similarity
        feats = ['danceability', 'energy', 'key', 'loudness', 'mode', 
                 'speechiness','acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'popularity', 'time_signature']
        
        with self.driver.session() as session:
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

                # Calculate Manhattan distance between current node and all other nodes
                for inner_index, inner_row in df.iterrows():
                    if inner_index != index:  
                        # Formula for manhattan distance
                        manhattan_distance = sum(abs(row[feat] - inner_row[feat]) for feat in feats)
                        
                        # If the distance between the current nodes is greater than 0 but less than 6, Create an edge
                        if 0 < manhattan_distance < 6:
                            # Query for making an edge
                            create_relationship_query = """
                            MATCH (a:Song {track_id: $current_track_id}), (b:Song {track_id: $other_track_id})
                            MERGE (a)<-[:IS_SIMILAR_TO {value: $distance}]->(b)
                            """
                            session.run(create_relationship_query, parameters={
                                'current_track_id': row['track_id'],
                                'other_track_id': inner_row['track_id'],
                                'distance': manhattan_distance
                            })

    # Return a list of Professor Rachlins' favorite songs
    def get_track_list(self, df):
        # Filter for "This is It" by the Strokes
        condition = df['album_name'] == 'Is This It'
        df = df[condition]
        # Return track_id's as a list
        return df['track_id'].tolist()

    # Generate 5 recommendations 
    def get_recs(self, track_list):
        # Instantiate results dataframe
        results_df = pd.DataFrame()
        # For each track in the specified track list, get all nodes connected and concatenate it with the results dataframe
        for track in track_list:
            # Query for getting all connected nodes
            query = """
            MATCH (:Song {track_id: $track_id })-[rel:IS_SIMILAR_TO]-(other:Song)
            RETURN other.track_name AS related_track_name, rel.value AS relationship_value, other.album_name as album_name, other.artists as artist, other.track_id as track_id

            """

            # Get query results, convert to a pandas dataframe compatible data type, and concatenate with results dataframe
            result = self.driver.session().run(query,  track_id=track)
            result_list = [dict(record) for record in result]
            step_df = pd.DataFrame(result_list)
            results_df = pd.concat([step_df, results_df])

        # Retrieve album name from the given track list
        album_name = results_df[results_df['track_id'] == track_list[0]]
        album_name = album_name['album_name'].values[0]
        # Filter out all relationships that concern the retrieved Album
        results_df = results_df.loc[results_df['album_name'] != album_name]
        results_df.drop_duplicates(subset=['related_track_name'],inplace=True)
        # Sort values by Manhattan similarity scores (ascending)
        results_df = results_df.sort_values(by='relationship_value', ascending=True)
        
        # Get five songs most similar to the specified track_list 
        results_df = results_df.head(5)
        results_df = results_df.reset_index(drop=True)

        # Drop track_id column to make result cleaner
        results_df = results_df.drop(columns=['track_id'])
        
        return results_df
        
        


                        
    