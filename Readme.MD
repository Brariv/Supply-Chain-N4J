# Supply Chain Management System

# Instructions to run:

###1. Ensure you have Python 3.10+ installed.
### 2. Install required packages:
```
pip install -r requirements.txt
```
### 3. Set up Neo4j and create a database named `supply_chain`. Update the `URI`, `USER`, and `PASSWORD` variables in `FrontEnd/Base.py` with your Neo4j credentials.
```
Copy the .env.example file to .env and fill in your Neo4j credentials:
URI=YOUR_NEO4J_URI
USER=YOUR_NEO4J_USERNAME
PASSWORD=YOUR_NEO4J_PASSWORD
```
### 4. Run the application:
```
python FrontEnd/Base.py
```