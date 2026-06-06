import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configurar semilla para que los datos aleatorios sean consistentes
np.random.seed(42)

# --- 1. DEFINICIÓN DE VARIABLES ---
cantidad_registros = 150

solicitantes = [
    "Planta Mosquera", 
    "Fitness Market - Principal", 
    "Bodytech Sede Norte", 
    "Zona Centro", 
    "Mantenimiento General"
]
piezas = [
    "Eje de transmisión", "Buje separador", "Polea dentada", 
    "Pasador de seguridad", "Acople de motor", "Tuerca especial", 
    "Soporte de rodamiento"
]
materiales = ["ACERO", "ACERO PLATA", "ALUMINIO", "BRONCE", "ACERO PLATA Y ALUMINIO"]
operarios = ["Cristian", "Juan Carlos", "Miguel", "Andrés"]
estados = ["ENTREGADO", "EN PROCESO", "RECHAZADO"]
prioridades = ["BAJA (MP)", "MEDIA (FL)", "ALTA (FS)"]

# --- 2. GENERACIÓN DE DATOS BASE ---
datos = {
    "FECHA SOLICITUD": [datetime.now() - timedelta(days=np.random.randint(1, 60)) for _ in range(cantidad_registros)],
    "SOLICITANTE": np.random.choice(solicitantes, cantidad_registros),
    "PRIORIDAD": np.random.choice(prioridades, cantidad_registros, p=[0.5, 0.3, 0.2]),
    "NOMBRE PIEZA": np.random.choice(piezas, cantidad_registros),
    "MATERIAL": np.random.choice(materiales, cantidad_registros),
    "QTY": np.random.randint(2, 85, cantidad_registros),
    "DIMENSIONES": "SEGUN PLANO",
    "ESTADO": np.random.choice(estados, cantidad_registros, p=[0.65, 0.20, 0.15])
}

df = pd.DataFrame(datos)

# --- 3. LÓGICA CONDICIONAL PARA COLUMNAS ESPECÍFICAS ---

# Operador (Si está en proceso puede no tener operador, si está entregado/rechazado sí)
df['OPERARIO'] = np.where(
    df['ESTADO'] == 'EN PROCESO',
    np.random.choice(operarios + [None], len(df), p=[0.2, 0.2, 0.2, 0.2, 0.2]),
    np.random.choice(operarios, len(df))
)

# Tiempos de entrega (Solo para Entregados o Rechazados)
df['TIEMPO DEMORADO (DÍAS)'] = np.where(
    df['ESTADO'].isin(['ENTREGADO', 'RECHAZADO']),
    np.random.randint(1, 14, len(df)),
    np.nan
)

# Número de remisión (Solo para Entregados)
df['nro de remision'] = np.where(
    df['ESTADO'] == 'ENTREGADO',
    np.random.randint(4000, 5000, len(df)).astype(str),
    ""
)

# Tipos de defecto (Solo para Rechazados)
defectos_lista = ["Fuera de tolerancia", "Mal acabado", "Rosca dañada", "Error de lectura de plano"]
df['TIPO_DEFECTO'] = np.where(
    df['ESTADO'] == 'RECHAZADO',
    np.random.choice(defectos_lista, len(df)),
    "Sin defecto"
)

# Incidentes de Seguridad Industrial (SST) - Mayoría sin incidentes
incidentes_lista = ["Ninguno", "Corte leve", "Proyección de viruta", "Parada de emergencia"]
df['INCIDENTE'] = np.random.choice(incidentes_lista, len(df), p=[0.88, 0.05, 0.05, 0.02])

# Nivel de riesgo asignado aleatoriamente según el material
df['NIVEL_RIESGO'] = np.where(
    df['MATERIAL'].isin(["ACERO PLATA", "BRONCE"]),
    np.random.choice(["Medio", "Alto"], len(df), p=[0.7, 0.3]),
    np.random.choice(["Bajo", "Medio"], len(df), p=[0.8, 0.2])
)

# --- 4. EXPORTAR A EXCEL ---
nombre_archivo = "Base_Datos_Torno_Presentacion.xlsx"
df.to_excel(nombre_archivo, index=False)

print(f"✅ ¡Datos generados con éxito! Se creó el archivo: {nombre_archivo}")
print(f"Total de registros: {len(df)}")