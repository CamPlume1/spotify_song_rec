from neo4j import GraphDatabase
import pandas as pd

# Function to connect to Neo4j and delete all data
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

# Function to add a row for testing
def add_test_row(driver):
    with driver.session() as session:
        session.run("CREATE (:Test {name: 'Beans Node'})")

# Neo4j connection details
neo4j_uri = "neo4j://localhost:7687"    
neo4j_username = "neo4j"    
neo4j_password = "#####"

# Path to your CSV file
file_path = "spotify/spotify.csv"

# Load CSV file into a DataFrame
df = pd.read_csv(file_path)

# Main script
def main():

    # Connect to Neo4j
    driver = connect_to_neo4j(neo4j_uri, neo4j_username, neo4j_password)    

    # Add a row for testing
    add_test_row(driver)
    add_test_row(driver)

    # Close the Neo4j driver
    driver.close()

    print(df)

if __name__ == '__main__':
    main()
