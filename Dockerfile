# Usamos una imagen base oficial de Python ligera
FROM python:3.11-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero el archivo de requerimientos
# (Esto optimiza el caché de Docker para no reinstalar dependencias si solo cambias código)
COPY requirements.txt .

# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del proyecto al contenedor
COPY . .

# Damos permisos de ejecución explícitos al script start.sh
RUN chmod +x start.sh

# Exponemos el puerto 5000 (el puerto por defecto en el que corre Flask según tu README)
EXPOSE 5000

# Indicamos a Docker que ejecute start.sh al encender el contenedor.
# Usamos "bash" por si el script tiene sintaxis específica de bash.
CMD ["bash", "./start.sh"]