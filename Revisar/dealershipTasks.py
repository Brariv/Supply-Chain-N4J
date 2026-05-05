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

# TASK 1 — Crear una backorder de carro desde un concesionario
# CYPHER (para probar en Neo4j Browser):
#
# MATCH (m:Manufacturer {id: $manufacturer_id})
# CALL apoc.create.node(
#     ['Car', $body_type, $fuel_type],
#     {
#         carId:  $car_id,
#         Model:  $model,
#         Brand:  $brand,
#         Color:  $color,
#         Year:   $year,
#         Plate:  $plate,
#         Group:  $group
#     }
# ) YIELD node AS c
# CREATE (m)-[:ON_BACKORDER {
#     Date_start:           date(),
#     Special_order:        $special_order,
#     Destination_Country:  $destination_country
# }]->(c)
# RETURN c
#
# Nota: body_type  ∈ {SUV, Sedan, Pickup}
#       fuel_type  ∈ {Electric, Diesel, Gas}
#       APOC es necesario para labels dinámicos en tiempo de ejecución.


VALID_BODY_TYPES = {"SUV", "Sedan", "Pickup"}
VALID_FUEL_TYPES = {"Electric", "Diesel", "Gas"}


def create_backorder(
    driver,
    manufacturer_id: str,
    body_type: str,           # SUV | Sedan | Pickup
    fuel_type: str,           # Electric | Diesel | Gas
    model: str,
    brand: str,
    color: str,
    year: int,
    plate: str,
    group: str,
    special_order: bool,
    destination_country: str,
):
    """
    Crea un nodo Car con labels dinámicos (Car + body_type + fuel_type)
    y lo vincula a un Manufacturer con la relación ON_BACKORDER.
    Requiere APOC instalado en la instancia de Neo4j.
    """
    if body_type not in VALID_BODY_TYPES:
        raise ValueError(f"body_type debe ser uno de {VALID_BODY_TYPES}")
    if fuel_type not in VALID_FUEL_TYPES:
        raise ValueError(f"fuel_type debe ser uno de {VALID_FUEL_TYPES}")

    query = """
    MATCH (m:Manufacturer {id: $manufacturer_id})
    CALL apoc.create.node(
        ['Car', $body_type, $fuel_type],
        {
            carId:  $car_id,
            Model:  $model,
            Brand:  $brand,
            Color:  $color,
            Year:   $year,
            Plate:  $plate,
            Group:  $group
        }
    ) YIELD node AS c
    CREATE (m)-[:`ON_BACKORDER` {
        Date_start:          date(),
        Special_order:       $special_order,
        Destination_Country: $destination_country
    }]->(c)
    RETURN c
    """

    params = {
        "manufacturer_id":    manufacturer_id,
        "car_id":             str(uuid.uuid4()),
        "body_type":          body_type,
        "fuel_type":          fuel_type,
        "model":              model,
        "brand":              brand,
        "color":              color,
        "year":               year,
        "plate":              plate,
        "group":              group,
        "special_order":      special_order,
        "destination_country": destination_country,
    }

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, params).single()
        if not rec:
            raise ValueError("Manufacturer no encontrado o APOC no disponible")
        return rec["c"]


# TASK 4 — Ver últimas visitas de un concesionario (rango dinámico de 1 mes)
# CYPHER (para probar en Neo4j Browser):
#
# MATCH (d:Dealership {dealershipId: $dealership_id})<-[v:Visits]-(cst:Customer)
# WHERE v.Date >= date($date_from) AND v.Date <= date($date_to)
# RETURN
#     cst.id          AS customer_id,
#     cst.Name        AS customer_name,
#     cst.Phone       AS phone,
#     v.Date          AS visit_date,
#     v.Has_Reservation AS has_reservation,
#     v.Test_Drive    AS test_drive
# ORDER BY v.Date DESC


def get_dealership_visits(
    driver,
    dealership_id: str,
    date_from: date = None,   # si es None se usa hoy - 1 mes
    date_to:   date = None,   # si es None se usa hoy
):
    """
    Devuelve las visitas recibidas por el dealership en el rango [date_from, date_to].
    Por defecto el rango es el último mes calendario.
    """
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - relativedelta(months=1)

    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})<-[v:Visits]-(cst:Customer)
    WHERE v.Date >= date($date_from) AND v.Date <= date($date_to)
    RETURN
        cst.id             AS customer_id,
        cst.Name           AS customer_name,
        cst.Phone          AS phone,
        v.Date             AS visit_date,
        v.Has_Reservation  AS has_reservation,
        v.Test_Drive       AS test_drive
    ORDER BY v.Date DESC
    """

    params = {
        "dealership_id": dealership_id,
        "date_from":     str(date_from),
        "date_to":       str(date_to),
    }

    with driver.session(database=DATABASE) as session:
        result = session.run(query, params)
        return [record.data() for record in result]


# TASK 5 — Promedio de MSRP en Showroom de un concesionario
# CYPHER (para probar en Neo4j Browser):
#
# MATCH (d:Dealership {dealershipId: $dealership_id})-[r:`ON_SHOWROOM`]->(c:Car)
# RETURN
#     count(c)        AS total_cars,
#     avg(r.MSRP)     AS avg_msrp,
#     min(r.MSRP)     AS min_msrp,
#     max(r.MSRP)     AS max_msrp

def get_showroom_avg_msrp(driver, dealership_id: str):
    """
    Retorna estadísticas de MSRP (avg, min, max, count) de todos los carros
    que están actualmente en el showroom del dealership.
    """
    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[r:`ON_SHOWROOM`]->(c:Car)
    RETURN
        count(c)    AS total_cars,
        avg(r.MSRP) AS avg_msrp,
        min(r.MSRP) AS min_msrp,
        max(r.MSRP) AS max_msrp
    """

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, dealership_id=dealership_id).single()
        if not rec:
            raise ValueError("Dealership no encontrado o sin carros en showroom")
        return rec.data()


# TASK 7 — Definir descuento a carros de años anteriores vinculados a un dealership
# CYPHER (para probar en Neo4j Browser):
#   Reemplaza $current_year, $dealership_id y $discount_pct con valores reales.
#
# MATCH (d:Dealership {dealershipId: $dealership_id})-[:`ON_SHOWROOM`]->(c:Car)
# WHERE c.Year < $current_year
# SET c.Discount = $discount_pct
# RETURN count(c) AS updated_cars


def set_discount_old_cars(
    driver,
    dealership_id: str,
    discount_pct: float,   # ej: 0.10 → 10 %
):
    """
    Agrega la propiedad Discount (float, porcentaje como decimal) a todos los
    nodos Car de años anteriores al corriente vinculados al dealership activo.
    """
    current_year = date.today().year

    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[:`ON_SHOWROOM`]->(c:Car)
    WHERE c.Year < $current_year
    SET c.Discount = $discount_pct
    RETURN count(c) AS updated_cars
    """

    params = {
        "dealership_id": dealership_id,
        "current_year":  current_year,
        "discount_pct":  discount_pct,
    }

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, params).single()
        return {"updated_cars": rec["updated_cars"]}


# TASK 9 + 13 — Ajustar MSRP de carros en showroom
#               (modifica nodo Car Y relación ON_SHOWROOM a la vez)
# CYPHER (para probar en Neo4j Browser):
#   Reemplaza $dealership_id y $adjustment_pct con valores reales.
#   adjustment_pct positivo → sube el precio; negativo → baja.
#
# MATCH (d:Dealership {dealershipId: $dealership_id})-[r:`ON_SHOWROOM`]->(c:Car)
# SET r.MSRP     = round(r.MSRP * (1 + $adjustment_pct), 2)
# RETURN count(c) AS updated_cars
#
# Nota: la tarea 13 es parte de esta misma operación; al ajustar el MSRP
#       de la relación se cubren ambas tareas en una sola query.

def adjust_showroom_msrp(
    driver,
    dealership_id: str,
    adjustment_pct: float,   # ej: 0.05 → +5 %, -0.05 → -5 %
):
    """
    Aplica un ajuste porcentual al MSRP de la relación ON_SHOWROOM de todos
    los carros del dealership activo. Cubre las tareas 9 y 13 simultáneamente.
    """
    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[r:`ON_SHOWROOM`]->(c:Car)
    SET r.MSRP = round(r.MSRP * (1 + $adjustment_pct), 2)
    RETURN count(c) AS updated_cars
    """

    params = {
        "dealership_id":  dealership_id,
        "adjustment_pct": adjustment_pct,
    }

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, params).single()
        return {"updated_cars": rec["updated_cars"]}


# TASK 11 — Eliminar propiedad Discount de carros en showroom por marca
# CYPHER (para probar en Neo4j Browser):
#   Reemplaza $dealership_id y $brand con valores reales.
#
# MATCH (d:Dealership {dealershipId: $dealership_id})-[:`ON_SHOWROOM`]->(c:Car)
# WHERE c.Brand = $brand
# REMOVE c.Discount
# RETURN count(c) AS updated_cars

def remove_discount_by_brand(
    driver,
    dealership_id: str,
    brand: str,
):
    """
    Elimina la propiedad Discount de los nodos Car que pertenecen a la marca
    indicada y están en el showroom del dealership activo.
    """
    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[:`ON_SHOWROOM`]->(c:Car)
    WHERE c.Brand = $brand
    REMOVE c.Discount
    RETURN count(c) AS updated_cars
    """

    params = {
        "dealership_id": dealership_id,
        "brand":         brand,
    }

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, params).single()
        return {"updated_cars": rec["updated_cars"]}


# TASK 14 — Modificar Test_Drive en una visita específica
# CYPHER (para probar en Neo4j Browser):
#   Reemplaza $dealership_id, $customer_id y $visit_date con valores reales.
#
# MATCH (d:Dealership {dealershipId: $dealership_id})<-[v:Visits]-(cst:Customer {id: $customer_id})
# WHERE v.Date = date($visit_date)
# SET v.Test_Drive = NOT v.Test_Drive
# RETURN v.Test_Drive AS new_value

def toggle_test_drive(
    driver,
    dealership_id: str,
    customer_id:   str,
    visit_date:    str,   # formato "YYYY-MM-DD"
):
    """
    Invierte el valor de Test_Drive (true→false / false→true) en una
    relación Visits específica identificada por dealership, customer y fecha.
    """
    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})<-[v:Visits]-(cst:Customer {id: $customer_id})
    WHERE v.Date = date($visit_date)
    SET v.Test_Drive = NOT v.Test_Drive
    RETURN v.Test_Drive AS new_value
    """

    params = {
        "dealership_id": dealership_id,
        "customer_id":   customer_id,
        "visit_date":    visit_date,
    }

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, params).single()
        if not rec:
            raise ValueError("Visita no encontrada")
        return {"new_test_drive_value": rec["new_value"]}


# TASK 15 — Marcar como PENDING los Ships con tracking NULL hacia un dealership
# CYPHER (para probar en Neo4j Browser):
#   Reemplaza $dealership_id con el valor real.
#
# MATCH (d:Dealership {dealershipId: $dealership_id})-[s:Ships]->(c:Car)
# WHERE s.Tracking IS NULL
# SET s.Tracking = 'PENDING'
# RETURN count(s) AS updated_shipments

def set_pending_tracking(driver, dealership_id: str):
    """
    Busca todas las relaciones Ships hacia el dealership activo que tengan
    Tracking: NULL y les asigna el valor 'PENDING'.
    """
    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[s:Ships]->(c:Car)
    WHERE s.Tracking IS NULL
    SET s.Tracking = 'PENDING'
    RETURN count(s) AS updated_shipments
    """

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, dealership_id=dealership_id).single()
        return {"updated_shipments": rec["updated_shipments"]}


# TASK 18 — Eliminar un carro del showroom junto con todas sus relaciones
# CYPHER (para probar en Neo4j Browser):
#   Reemplaza $dealership_id y $car_id con valores reales.
#
# MATCH (d:Dealership {dealershipId: $dealership_id})-[:`ON_SHOWROOM`]->(c:Car {carId: $car_id})
# DETACH DELETE c
#
# DETACH DELETE elimina el nodo y TODAS sus relaciones automáticamente.

def delete_showroom_car(
    driver,
    dealership_id: str,
    car_id:        str,
):
    """
    Elimina un nodo Car que esté en el showroom del dealership activo,
    junto con todas sus relaciones (DETACH DELETE).
    Lanza ValueError si el carro no existe en ese showroom.
    """
    # Verificar existencia antes de borrar
    check_query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[:`ON_SHOWROOM`]->(c:Car {carId: $car_id})
    RETURN c.carId AS car_id
    """

    delete_query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[:`ON_SHOWROOM`]->(c:Car {carId: $car_id})
    DETACH DELETE c
    """

    params = {
        "dealership_id": dealership_id,
        "car_id":        car_id,
    }

    with driver.session(database=DATABASE) as session:
        rec = session.run(check_query, params).single()
        if not rec:
            raise ValueError("Carro no encontrado en el showroom de este dealership")
        session.run(delete_query, params)
        return {"status": "deleted", "car_id": car_id}