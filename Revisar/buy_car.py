from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import random
from datetime import date
import uuid

load_dotenv(override=True)

URI = os.getenv("URI")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))  # type: ignore[arg-type]

# Función para obtener los carros en exhibición de un concesionario específico

def get_showroom_cars(driver, dealership_id: int):
    query = """
    MATCH (d:Dealership {dealershipId: $dealership_id})-[r:`ON_SHOWROOM`]->(c:Car)
    RETURN
        c.carId AS car_id,
        c.Model AS model,
        c.Brand AS brand,
        c.Color AS color,
        c.Year AS year,
        c.Plate AS plate,
        c.Group AS group,
        r.On_Site_Since AS on_site_since,
        r.MSRP AS msrp,
        r.Negotiable AS negotiable
    """

    with driver.session(database=DATABASE) as session:
        result = session.run(query, dealership_id=dealership_id)
        return [record.data() for record in result]
    
import random

def get_price_range(driver, car_id: int):
    query = """
    MATCH (:Dealership)-[r:`On Showroom`]->(c:Car {carId: $car_id})
    RETURN r.MSRP AS msrp
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(query, car_id=car_id).single()

        if not record:
            raise ValueError("Carro no encontrado")

        msrp = record["msrp"]

        if msrp is None:
            raise ValueError("MSRP no disponible")

        pct = random.uniform(0, 0.15)

        min_price = round(msrp * (1 - pct), 2)
        max_price = round(msrp * (1 + pct), 2)

        return {
            "msrp": msrp,
            "min": min_price,
            "max": max_price,
            "pct": pct
        }

#Función para obtener el MSRP de un carro específico

def get_msrp(driver, car_id: int):
    query = """
    MATCH (:Dealership)-[r:`ON_SHOWROOM`]->(c:Car {carId: $car_id})
    RETURN r.MSRP AS msrp
    """

    with driver.session(database=DATABASE) as session:
        record = session.run(query, car_id=car_id).single()

        if not record:
            raise ValueError("Carro no encontrado")

        msrp = record["msrp"]

        if msrp is None:
            raise ValueError("MSRP no disponible")

        return msrp

#Función para ofertas sobre un msrp obtenido

def negotiate_price(msrp: float):
    # 1. generar wiggle room
    pct = random.uniform(0, 0.15)
    min_price = round(msrp * (1 - pct), 2)
    max_price = round(msrp * (1 + pct), 2)

    # 2. setup
    offers = [round(msrp, 2)]
    attempts = 0
    max_attempts = 5

    print(f"Precio inicial (MSRP): {msrp}")

    # 3. loop interactivo
    while attempts < max_attempts:
        try:
            user_input = input(f"Ingresa tu oferta #{attempts + 1}: ")
            offer = float(user_input)
        except ValueError:
            print("Entrada inválida. Ingresa un número.")
            continue

        offer = round(offer, 2)
        offers.append(offer)

        # check rango
        if min_price <= offer <= max_price:
            print("Oferta aceptada")
            return {
                "status": "success",
                "accepted_offer": offer,
                "offers": offers,
                "range": (min_price, max_price)
            }

        print("Oferta rechazada")
        attempts += 1

    # 4. fallo
    print("No se llegó a un acuerdo")
    return {
        "status": "failed",
        "offers": offers,
        "range": (min_price, max_price)
    }
    

def create_transaction_from_offers(
    driver,
    success: bool,
    offers: list,
    car_id: int,
    customer_id: int,
    payment_type: str = "Unknown",
    financing_months: int = None #type: ignore[assignment]
):
    if not success:
        return {
            "status": "skipped",
            "reason": "negotiation_failed",
            "offers": offers
        }

    if not offers or len(offers) < 2:
        raise ValueError("Lista de ofertas inválida")

    final_price = float(offers[-1])
    msrp = float(offers[0])

    if msrp <= 0:
        raise ValueError("MSRP inválido")

    discount_pct = round(100 * (1 - final_price / msrp), 2)

    query = """
    MATCH (cst:Customer {customerId: $customer_id})
    MATCH (car:Car {carId: $car_id})

    OPTIONAL MATCH (d:Dealership)-[r:`ON_SHOWROOM`]->(car)

    WITH cst, car, r
    WHERE cst IS NOT NULL AND car IS NOT NULL

    CREATE (t:Transaction {
        id: $transaction_id,
        MSRP: $msrp,
        Final_Price: $final_price,
        Date: date(),
        Payment_Type: $payment_type,
        Financing_Months: $financing_months
    })

    CREATE (cst)-[:Makes {
        Offers: $offers,
        Notes: $notes,
        Custom_Order: false
    }]->(t)

    CREATE (t)-[:Involves {
        MSRP: $msrp,
        Date: date(),
        Discount: $discount
    }]->(car)

    FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END | DELETE r)

    CREATE (cst)-[:OWNS {
        Since: date(),
        Milage: 0,
        Has_Crashed: false
    }]->(car)

    RETURN t
    """

    params = {
        "transaction_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "car_id": car_id,
        "msrp": msrp,
        "final_price": final_price,
        "offers": offers,
        "payment_type": payment_type,
        "financing_months": financing_months,
        "notes": "Auto-generated negotiation",
        "discount": f"{discount_pct}%"
    }

    with driver.session(database=DATABASE) as session:
        rec = session.run(query, params).single()
        if not rec:
            raise ValueError("Customer o Car no encontrados")
        return rec["t"]