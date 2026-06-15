#!/bin/bash

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación principal una vez para que cree la BD vacía y los defaults
python -c "from app import app, db, seed_db; app.app_context().push(); db.create_all(); seed_db()"

# Sembrar los datos masivos del segundo script
python seed_more_data.py

# Arrancar el servidor Flask en el puerto 5000 accesible desde fuera de la VM
flask run --host=0.0.0.0 --port=5000