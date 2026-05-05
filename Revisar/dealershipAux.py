from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import uuid
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

load_dotenv(override=True)

URI = os.getenv("URI")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))  # type: ignore[arg-type]

# List Dealerships
def get_all_dealerships(driver):
    query = """
    MATCH (d:Dealership)
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
        result = session.run(query)
        return [record["dealership"] for record in result]

# List 
# Warehouse: 
#  - Brand: Text
#  - Group: Text
#  - Country: Text
#  - Capacity: Int
#  - Shiping_Type: Text

def get_all_warehouses(driver):
    query = """
    MATCH (w:Warehouse)
    RETURN w {
        .warehouseId,
        .Brand,
        .Group,
        .Country,
        .Capacity,
        .Shipping_Type
    } AS warehouse
    """
    with driver.session(database=DATABASE) as session:        
        result = session.run(query)
        return [record["warehouse"] for record in result]

# List
# Manufacturer: 
#  - Brand: Text
#  - Group: Text
#  - Country: Text
#  - year_manufacturing: Int
#  - Custom_orders: Bool

def get_all_manufacturers(driver):
    query = """
    MATCH (m:Manufacturer)
    RETURN m {
        .manufacturerId,
        .Brand,
        .Group,
        .Country,
        .Year_Manufacturing,
        .Custom_Orders
    } AS manufacturer
    """
    with driver.session(database=DATABASE) as session:
        result = session.run(query)
        return [record["manufacturer"] for record in result]