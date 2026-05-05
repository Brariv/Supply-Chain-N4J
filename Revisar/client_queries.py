from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv(override=True)

URI = os.getenv("URI")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD)) # type: ignore[arg-type]


## Obtener información de carros de un cliente
def get_customer_cars(driver, customer_id: int):
    query = """
    MATCH (cst:Customer {customerId: $customer_id})-[r:OWNS]->(car:Car)
    RETURN 
        car.carId AS car_id,
        car.Model AS model,
        car.Brand AS brand,
        car.Year AS year,
        car.Plate AS plate,
        r.Since AS since
    """

    with driver.session(database=DATABASE) as session:
        result = session.run(query, customer_id=customer_id)
        return [record.data() for record in result]


## Obtener campos vacios de un perfil
def get_customer_profile(driver, customer_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id})
    RETURN c {
        .Name,
        .Phone,
        .Email,
        .Credit_Score,
        .Age
    } AS profile
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(query, customer_id=customer_id).single()

        if not record:
            raise ValueError("Cliente no encontrado")

        profile = record["profile"]

        missing = [k for k, v in profile.items() if v is None]

        return {
            "customer_id": customer_id,
            "profile": profile,
            "missing_fields": missing
        }


## Actualizar campos de un perfil
def update_customer_profile(driver, base_data: dict, updates: dict):
    """
    base_data: output de get_customer_profile o dict con customer_id
    updates: campos a actualizar
    """

    customer_id = base_data.get("customer_id")

    if not customer_id:
        raise ValueError("customer_id requerido")

    if not updates:
        return {"status": "no_updates"}

    set_clause = ", ".join([f"c.{k} = ${k}" for k in updates.keys()])

    query = f"""
    MATCH (c:Customer {{customerId: $customer_id}})
    SET {set_clause}
    RETURN c
    """

    params = {"customer_id": customer_id, **updates}

    with driver.session(database=DATABASE) as session:
        result = session.run(query, params).single()

        return {
            "status": "updated",
            "updated_fields": list(updates.keys()),
            "node": result["c"] if result else None
        }
        
## Eliminar propiedades de un perfil
def remove_customer_fields(driver, base_data: dict, fields: list):
    """
    base_data: puede ser output de funciones previas o {"customer_id": ...}
    fields: lista de propiedades a eliminar
    """

    customer_id = base_data.get("customer_id")

    if not customer_id:
        raise ValueError("customer_id requerido")

    if not fields:
        return {"status": "no_fields"}

    remove_clause = ", ".join([f"c.{field}" for field in fields])

    query = f"""
    MATCH (c:Customer {{customerId: $customer_id}})
    REMOVE {remove_clause}
    RETURN c
    """

    with driver.session(database=DATABASE) as session:
        result = session.run(query, {"customer_id": customer_id}).single()

        return {
            "status": "removed",
            "removed_fields": fields,
            "node": result["c"] if result else None
        }

## Obtener información de visitas de un cliente
def get_customer_visits(driver, customer_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id})-[r:VISITS]->(d:Dealership)
    RETURN d.Name, r.Date
    ORDER BY r.Date DESC
    """

    with driver.session(database=DATABASE) as session:
        result = session.run(query, customer_id=customer_id)
        return [record.data() for record in result]

## Añadir puntaje a una visita
def add_visit_rating(driver, customer_id: int, dealership_id: int, rating: int):
    # Validación discreta 0–5
    if not isinstance(rating, int) or rating < 0 or rating > 5:
        raise ValueError("rating debe ser un entero entre 0 y 5")

    query = """
    MATCH (c:Customer {customerId: $customer_id})-[r:VISITS]->(d:Dealership {dealershipId: $dealership_id})
    SET r.rating = $rating
    RETURN r
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(
            query,
            customer_id=customer_id,
            dealership_id=dealership_id,
            rating=rating
        ).single()

        if not record:
            raise ValueError("Visita no encontrada")

        return record["r"]


# Obtener información sobre visitas puntuadas en un perfil
def get_rated_visits(driver, customer_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id})-[r:VISITS]->(d:Dealership)
    WHERE r.rating IS NOT NULL
    RETURN 
        d.dealershipId AS dealership_id,
        d.Name AS dealership,
        r.Date AS date,
        r.rating AS rating
    """

    with driver.session(database=DATABASE) as session:
        result = session.run(query, customer_id=customer_id)
        visits = [record.data() for record in result]

        return {
            "customer_id": customer_id,
            "rated_visits": visits
        }
        
# Borrar un rating de una visita
def remove_rating_from_visit(driver, visit_data: dict):
    """
    visit_data: uno de los elementos de rated_visits
    requiere: customer_id, dealership, date
    """

    customer_id = visit_data.get("customer_id")
    dealership = visit_data.get("dealership")
    date = visit_data.get("date")

    if not all([customer_id, dealership, date]):
        raise ValueError("Datos incompletos para identificar la visita")

    query = """
    MATCH (c:Customer {customerId: $customer_id})-[r:VISITS {Date: $date}]->(d:Dealership {Name: $dealership})
    WHERE r.rating IS NOT NULL
    REMOVE r.rating
    RETURN r
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(
            query,
            customer_id=customer_id,
            dealership=dealership,
            date=date
        ).single()

        if not record:
            raise ValueError("No existe rating en esta visita")

        return {"status": "removed"}
    
# Borrar información de fecha de compra en carros de un cliente
def remove_since_from_all_cars(driver, customer_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id})-[r:OWNS]->(:Car)
    WHERE r.Since IS NOT NULL
    REMOVE r.Since
    RETURN count(r) AS updated
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(query, customer_id=customer_id).single()

        updated = record["updated"] if record else 0

        if updated == 0:
            return {
                "status": "no_changes",
                "message": "No había campos 'Since' para eliminar"
            }

        return {
            "status": "success",
            "relationships_updated": updated
        }

# Eliminar a un cliente y sus carros de la base de datos
def delete_customer_and_cars(driver, customer_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id})
    OPTIONAL MATCH (c)-[:OWNS]->(car:Car)
    WITH c, collect(car) AS cars
    DETACH DELETE c, cars
    RETURN size(cars) AS deleted_cars
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(query, customer_id=customer_id).single()

        if not record:
            raise ValueError("Cliente no encontrado")

        return {
            "status": "deleted",
            "deleted_cars": record["deleted_cars"]
        }

# Eliminar carro de cliente
def remove_car_from_customer(driver, customer_id: int, car_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id})-[r:OWNS]->(car:Car {carId: $car_id})
    DELETE r
    RETURN car
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(
            query,
            customer_id=customer_id,
            car_id=car_id
        ).single()

        if not record:
            raise ValueError("Relación Owns no encontrada")

        return {
            "status": "removed",
            "car": record["car"]
        }

# Cliente borra todos sus carros
def remove_all_cars_from_customer(driver, customer_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id})-[r:OWNS]->(:Car)
    DELETE r
    RETURN count(r) AS removed
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(query, customer_id=customer_id).single()

        removed = record["removed"] if record else 0

        if removed == 0:
            return {
                "status": "no_changes",
                "message": "El cliente no tenía carros"
            }

        return {
            "status": "success",
            "relationships_removed": removed
        }

def create_visit(driver, customer_id: int, dealership_id: int):
    query = """
    MATCH (c:Customer {customerId: $customer_id}), (d:Dealership {dealershipId: $dealership_id})
    CREATE (c)-[r:VISITS {Has_Reservation: false, Test_Drive: false, Date: date()}]->(d)
    RETURN r
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(
            query,
            customer_id=customer_id,
            dealership_id=dealership_id
        ).single()

        if not record:
            raise ValueError("No se pudo crear la visita")

        return record["r"]