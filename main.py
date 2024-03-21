# Importing neo4j file
import neo4j_api

# Main script
def main():

    # Neo4j connection details
    neo4j_uri = "neo4j://localhost:7687"    
    neo4j_username = input("Enter the Neo4j username: ")
    neo4j_password = input("Enter the Neo4j password: ")

    # Connect to Neo4j
    driver = neo4j_api.connect_to_neo4j(neo4j_uri, neo4j_username, neo4j_password)   

    # File Path to Spotify CSV File
    file_path = "spotify/spotify.csv"

    # Extracts Professor Rachlin's songs of intrest
    # Songs from the Is This It Album
    df = neo4j_api.load_data(file_path, 114000)
    songs_of_interest = df[df['album_name'] == 'Is This It']
    rachlin_songs_track_ids = list(set(songs_of_interest['track_id'].tolist()))

    # Loading and cleaning the data to a dataframe that will be eventually converted into neo4j
    # Note: The function allows for any song (to use for recommending) as input, 
    # just need to pass in valid track_ids as a list for the third parameter
    song_df = neo4j_api.load_data(file_path, 1000, rachlin_songs_track_ids)

    # Given the dataframe, converts it into a graphical database and adds relationships if two nodes (songs) are similar
    neo4j_api.to_neo4j(song_df, driver, rachlin_songs_track_ids)

    # Returns the 5 song recommendations for Professor Rachlin based that he likes the Is This It album by The Strokes 
    # Note: The function allows for any song as input, just need to pass in valid track_ids as a list for the second parameter
    rachlin_recs = neo4j_api.get_recommended_track_names(driver, rachlin_songs_track_ids)
    print(rachlin_recs)

    # Close the Neo4j driver
    driver.close()

if __name__ == '__main__':
    main()