import pandas as pd
import os
from datetime import datetime

# Encontrar automáticamente la carpeta real donde vive este archivo motor.py
CARPETA_ACTUAL = os.path.dirname(os.path.abspath(__file__))

# --- RUTA PARA LA PRESENTACIÓN ---
# Apuntamos directamente al archivo de Excel generado. 
# Si moviste el archivo a la carpeta 'datos', cambia esta línea por: 
# ARCHIVO_EXCEL = os.path.join(CARPETA_ACTUAL, 'datos', 'Base_Datos_Torno_Presentacion.xlsx')
ARCHIVO_EXCEL = os.path.join(CARPETA_ACTUAL, 'datos', 'Base_Datos_Torno_Presentacion.xlsx')


def cargar_datos():
    """Carga el conjunto de datos de la presentación."""
    try:
        # Leer el archivo de Excel
        df = pd.read_excel(ARCHIVO_EXCEL)
        print("✅ Archivo de presentación cargado con éxito. Filas:", len(df))
        
        # Devolvemos el mismo DataFrame dos veces para mantener la compatibilidad 
        # con tu código original que esperaba df_original y df_limpio
        return df.copy(), df.copy()
        
    except FileNotFoundError as e:
        print(f"❌ Error: No se encontró el archivo de Excel. {e}")
        return None, None


def resumen_produccion():
    """Muestra estadísticas rápidas basadas en el archivo del Dashboard."""
    _, df_dash = cargar_datos()
    
    if df_dash is not None:
        print(f"\n--- RESUMEN GENERAL DEL TORNO (DASHBOARD) ---")
        print(f"Total de solicitudes registradas: {len(df_dash)}")
        print("\nDistribución por Estado:")
        print(df_dash['ESTADO'].value_counts().to_string())
        print("\nProducción Total por Operario:")
        print(df_dash.groupby('OPERARIO')['QTY'].sum().to_string())


def agregar_solicitud(solicitante, prioridad, nombre_pieza, material, cantidad, dimensiones="SEGUN PLANO", operario="Por Asignar"):
    """Crea una nueva orden de trabajo en el archivo de Excel."""
    _, df_dash = cargar_datos()
    
    if df_dash is not None:
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        
        nueva_fila = pd.DataFrame([{
            'FECHA SOLICITUD': fecha_hoy,
            'SOLICITANTE': str(solicitante).title(),
            'PRIORIDAD': prioridad.upper(),
            'NOMBRE PIEZA': nombre_pieza.upper(),
            'MATERIAL': material.upper(),
            'QTY': int(cantidad),
            'DIMENSIONES': dimensiones,
            'ESTADO': 'EN PROCESO',
            'OPERARIO': operario.title(),
            'FECHA ENTREGA': 'PENDIENTE',
            'TIEMPO DEMORADO (DÍAS)': None, 
            'nro de remision': None,
            'TIPO_DEFECTO': 'Sin defecto',
            'INCIDENTE': 'Ninguno',
            'NIVEL_RIESGO': 'Bajo'
        }])
        
        # Unir y salvar en archivo Excel
        df_dash = pd.concat([df_dash, nueva_fila], ignore_index=True)
        df_dash.to_excel(ARCHIVO_EXCEL, index=False)
        
        print(f"\n✅ ¡Orden de trabajo para '{solicitante}' guardada exitosamente en el Excel!")


def marcar_entregado(indice_fila, operario_real=None):
    """Cambia el estado de una pieza a ENTREGADO en el archivo Excel."""
    _, df_dash = cargar_datos()
    
    if df_dash is not None:
        if indice_fila >= len(df_dash):
            print("❌ Error: El índice de fila no existe.")
            return
            
        fecha_hoy_str = datetime.now().strftime("%d/%m/%Y")
        fecha_hoy_dt = datetime.now()
        
        # Cálculo de días (Adaptado para leer fechas en formato string o datetime)
        fecha_sol = df_dash.at[indice_fila, 'FECHA SOLICITUD']
        try:
            if isinstance(fecha_sol, str):
                fecha_sol_dt = datetime.strptime(fecha_sol.split(" ")[0], "%Y-%m-%d") # Ajuste por si viene con hora
            else:
                fecha_sol_dt = fecha_sol # Si ya es datetime
            dias_demora = max(0, (fecha_hoy_dt - fecha_sol_dt).days)
        except Exception:
            dias_demora = 0 
            
        # Conseguir consecutivo de remisión
        todos_los_nros = pd.to_numeric(df_dash['nro de remision'], errors='coerce')
        siguiente_remision = int(todos_los_nros.max() + 1) if not todos_los_nros.isna().all() else 4140

        # Actualizar datos
        df_dash.at[indice_fila, 'ESTADO'] = 'ENTREGADO'
        df_dash.at[indice_fila, 'FECHA ENTREGA'] = fecha_hoy_str
        df_dash.at[indice_fila, 'TIEMPO DEMORADO (DÍAS)'] = int(dias_demora)
        df_dash.at[indice_fila, 'nro de remision'] = int(siguiente_remision)
        if operario_real:
            df_dash.at[indice_fila, 'OPERARIO'] = str(operario_real).title()
            
        # Guardar en Excel
        df_dash.to_excel(ARCHIVO_EXCEL, index=False)
        
        print(f"\n✅ ¡Fila {indice_fila} marcada como ENTREGADO! Remisión No. {siguiente_remision}. Demoró: {dias_demora} día(s).")


def asignar_operario(indice_fila, nombre_operario):
    """Asigna un operario a una tarea específica."""
    _, df_dash = cargar_datos()
    
    if df_dash is not None:
        df_dash.at[indice_fila, 'OPERARIO'] = nombre_operario.title()
        df_dash.to_excel(ARCHIVO_EXCEL, index=False)
        print(f"✅ Operario {nombre_operario} asignado a la fila {indice_fila}.")


if __name__ == "__main__":
    print("--- INICIANDO MOTOR DEL SISTEMA ---")
    resumen_produccion()