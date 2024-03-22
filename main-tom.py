from neo4j_api_tom import Neo4J_API
import pandas as pd

def main():

    # Neo4j connection details
    neo4j_uri = "neo4j://localhost:7687"    
    neo4j_username = "neo4j"    
    neo4j_password = input("Enter your password: ")

    # Instantiate API
    api = Neo4J_API(neo4j_uri, neo4j_username, neo4j_password)
    # PFile Path to Spotify CSV File
    file_path = "spotify/spotify.csv"
    # Sample dataset to contain 1000 random songs + all songs from "Is This It"
    samples,track_list = api.sample_dataset(file_path, 1000, "Soma", "The Strokes")
    # Create nodes and edges for each song
    api.load_data(samples)
    # Generate results and print out result dataframe
    results = api.get_recs(track_list)
    print(results)
    # Close the Neo4j driver
    #api.driver.close()

if __name__ == '__main__':
    main()