#!/bin/bash

# Script para generar y subir un video a YT Shorts

# Verificar qué intérprete usar (python)
if [ -x "$(command -v python3)" ]; then
  PYTHON=python3
else
  PYTHON=python
fi

# Leer .mp/youtube.json, recorrer el array de cuentas, obtener cada id e imprimir todos los ids
youtube_ids=$($PYTHON -c "import json; print('\n'.join([account['id'] for account in json.load(open('.mp/youtube.json'))['accounts']]))")

echo "¿A qué cuenta querés subir el video?"

# Imprimir los ids
for id in $youtube_ids; do
  echo $id
done

# Pedir el id
read -p "Ingresá el id: " id

# Verificar si el id está en la lista
if [[ " ${youtube_ids[@]} " =~ " ${id} " ]]; then
  echo "ID encontrado"
else
  echo "ID no encontrado"
  exit 1
fi

# Ejecutar script de python
$PYTHON src/cron.py youtube $id
