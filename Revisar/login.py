from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

URI = os.getenv("URI")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD)) # type: ignore[arg-type]

# Customer: 
#  - Name: Text
#  - Phone: Text
#  - Email: Text
#  - Credit_Score: Int
#  - Age: Int
#  - Password: String


def login(driver, email: str, password: str):
    query = """
    MATCH (c:Customer {Email: $email, Password: $password})
    RETURN c {
        .customerId,
        .Name,
        .Phone,
        .Email,
        .Credit_Score,
        .Age
    } AS customer
    """

    # with driver.session(database=DATABASE) as session:
    #     result = session.run(query, customer_id=customer_id)
    #     return [record.data() for record in result]

    with driver.session(database=DATABASE) as session:
        result = session.run(query, email=email, password=password).single()
        return result["customer"] if result else None
    


# Dealership: 
#  - Name: Text
#  - Brand: Text
#  - City: Text
#  - Capacity: Int
#  - Certified: Bool
#  - Address: Text
#  - Password: Text

def dealership_login(driver, name: str, password: str):
    query = """
    MATCH (d:Dealership {Name: $name, Password: $password})
    RETURN d {
        .dealershipId,
        .Name,
        .Brand,
        .City,
        .Capacity,
        .Certified,
        .Address
    } AS dealership
    """

    with driver.session(database=DATABASE) as session:
        result = session.run(query, name=name, password=password).single()
        return result["dealership"] if result else None