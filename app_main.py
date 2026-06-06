import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import Motor
import io

# --- CONFIGURACIÓN DE PÁGINA Y TEMA ---
st.set_page_config(page_title="Sistema Torno CNC v2.0", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Color de fondo principal y texto */
    .stApp { background-color: #1F5A94; color: #CED5D9; }
    
    /* Color del menú lateral */
    .stSidebar { background-color: #C94F12; border-right: 2px solid #E2E8F0; }
    
    /* Color de los Títulos */
    h1, h2, h3 { color: #FFFFFF!important; } 
    
    /* Color de las tarjetas de métricas */
    [data-testid="stMetricValue"] { color: #00FF66; } 
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS REALES ---
df_original, df_actual = Motor.cargar_datos()

if df_actual is None:
    st.error("❌ No se pudo cargar la base de datos. Verifica la carpeta 'datos'.")
    st.stop()

# --- PREPARACIÓN DE DATOS (Manejo de columnas nuevas) ---
if 'ESTADO' not in df_actual.columns:
    df_actual['ESTADO'] = 'EN PROCESO'
if 'TIPO_DEFECTO' not in df_actual.columns:
    df_actual['TIPO_DEFECTO'] = 'Sin defecto'
if 'INCIDENTE' not in df_actual.columns:
    df_actual['INCIDENTE'] = 'Ninguno'
if 'NIVEL_RIESGO' not in df_actual.columns:
    df_actual['NIVEL_RIESGO'] = 'Bajo'

# Asegurar limpieza de columnas numéricas para las métricas
if 'QTY' in df_actual.columns:
    df_actual['QTY'] = pd.to_numeric(df_actual['QTY'], errors='coerce').fillna(0)
if 'TIEMPO DEMORADO (DÍAS)' in df_actual.columns:
    df_actual['TIEMPO DEMORADO (DÍAS)'] = pd.to_numeric(df_actual['TIEMPO DEMORADO (DÍAS)'], errors='coerce').fillna(0)

# --- SISTEMA DE SEGURIDAD ---
if 'es_admin' not in st.session_state:
    st.session_state['es_admin'] = False

with st.sidebar:
    st.title("⚙️ Menú Principal")
    
    if not st.session_state['es_admin']:
        clave_ingresada = st.text_input("🔑 Contraseña Admin", type="password")
        if clave_ingresada == "Torno2026":
            st.session_state['es_admin'] = True
            st.rerun()
        elif clave_ingresada != "":
            st.error("Contraseña incorrecta")
    else:
        st.success("✅ Sesión Iniciada")
        if st.button("Cerrar Sesión"):
            st.session_state['es_admin'] = False
            st.rerun()

es_admin = st.session_state['es_admin']

st.sidebar.divider()

# --- NAVEGACIÓN UNIFICADA ---
menu = st.sidebar.radio("Navegación", [
    "📊 Dashboard General",
    "🔀 Cruce de Datos", 
    "⭐ Control de Calidad", 
    "🔍 Hallazgos", 
    "⚠️ Incidentes", 
    "🛡️ Riesgos",
    "📝 Nueva Orden de Trabajo", 
    "✅ Control de Entregas",
    "👷 Vista Operario"
])

# --- FILTROS GLOBALES (Solo para pantallas analíticas) ---
pantallas_analiticas = ["📊 Dashboard General", "🔀 Cruce de Datos", "⭐ Control de Calidad", "🔍 Hallazgos", "⚠️ Incidentes", "🛡️ Riesgos"]

if menu in pantallas_analiticas:
    st.sidebar.divider()
    st.sidebar.caption("Filtros Globales de Análisis")
    
    materiales_disp = [m for m in df_actual['MATERIAL'].unique() if pd.notna(m)]
    operarios_disp = [o for o in df_actual['OPERARIO'].unique() if pd.notna(o)]
    
    material_sel = st.sidebar.multiselect("Filtrar Material", materiales_disp, default=materiales_disp)
    operario_sel = st.sidebar.multiselect("Filtrar Operario", operarios_disp, default=operarios_disp)
    
    df_filtrado = df_actual[
        (df_actual['MATERIAL'].isin(material_sel)) & 
        (df_actual['OPERARIO'].isin(operario_sel))
    ]
else:
    df_filtrado = df_actual.copy()

st.sidebar.divider()
st.sidebar.caption("Dashboard CNC v2.0 | Producción y Mantenimiento")


# ==========================================
# 1. MÓDULOS DE ANÁLISIS 
# ==========================================

if menu == "📊 Dashboard General":
    st.header("📊 Dashboard General de Producción")
    
    # MÉTRICAS
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Piezas Solicitadas", f"{int(df_filtrado['QTY'].sum()):,}")
    col2.metric("Piezas Entregadas", f"{int(df_filtrado[df_filtrado['ESTADO']=='ENTREGADO']['QTY'].sum()):,}")
    
    tiempo_prom = df_filtrado['TIEMPO DEMORADO (DÍAS)'].mean()
    col3.metric("Tiempo Prom. Entrega", f"{tiempo_prom:.1f} días" if not pd.isna(tiempo_prom) else "N/A")
    
    tasa_rechazo = (df_filtrado['ESTADO']=='RECHAZADO').mean() * 100
    col4.metric("Tasa de Rechazo", f"{tasa_rechazo:.1f}%" if not pd.isna(tasa_rechazo) else "0.0%")
    
    st.divider()
    
    # FILA 1 DE GRÁFICAS
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Distribución por Material")
        if not df_filtrado.empty:
            fig1 = px.pie(df_filtrado, names='MATERIAL', hole=0.4)
            fig1.update_traces(textposition='inside', textinfo='percent+label')
            fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#cdd6f4')
            st.plotly_chart(fig1, use_container_width=True, key="grafica_pastel_materiales")
    
    with col_g2:
        st.subheader("Top Operarios por Producción")
        prod_op = df_filtrado.groupby('OPERARIO')['QTY'].sum().reset_index().sort_values('QTY', ascending=False)
        if not prod_op.empty:
            fig2 = px.bar(prod_op.head(5), x='OPERARIO', y='QTY', color='QTY', color_continuous_scale='Viridis')
            fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#cdd6f4')
            st.plotly_chart(fig2, use_container_width=True, key="grafica_top_operarios")

    st.divider()

    # FILA 2 DE GRÁFICAS (NUEVAS)
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.subheader("📈 Tendencia de Solicitudes")
        if not df_filtrado.empty and 'FECHA SOLICITUD' in df_filtrado.columns:
            tendencia = df_filtrado.groupby('FECHA SOLICITUD')['QTY'].sum().reset_index()
            fig_line = px.line(tendencia, x='FECHA SOLICITUD', y='QTY', markers=True, color_discrete_sequence=['#00FF66'])
            fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#CED5D9')
            st.plotly_chart(fig_line, use_container_width=True, key="grafica_tendencia_tiempo")

    with col_g4:
        st.subheader("🌪️ Embudo de Estados")
        if not df_filtrado.empty:
            embudo_datos = df_filtrado['ESTADO'].value_counts().reset_index()
            embudo_datos.columns = ['ESTADO', 'CANTIDAD']
            fig_funnel = px.funnel(embudo_datos, x='CANTIDAD', y='ESTADO', color='ESTADO',
                                   color_discrete_map={'ENTREGADO': '#059669', 'EN PROCESO': '#F59E0B', 'RECHAZADO': '#DC2626'})
            fig_funnel.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#CED5D9')
            st.plotly_chart(fig_funnel, use_container_width=True, key="grafica_embudo_estados")

    st.divider()
    
    st.subheader("Órdenes Recientes")
    st.dataframe(df_filtrado.tail(10), use_container_width=True)

    st.divider()
    st.subheader("📥 Exportar Datos")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name='Reporte_Filtrado')
    
    st.download_button(
        label="Descargar Reporte en Excel",
        data=buffer.getvalue(),
        file_name="Reporte_Produccion_Torno.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True
    )

elif menu == "🔀 Cruce de Datos":
    st.header("🔀 Cruce de Datos")
    st.write("Análisis de rechazos por operario y material.")
    
    if not df_filtrado.empty:
        cruce = df_filtrado.pivot_table(
            values='QTY', index='OPERARIO', columns='MATERIAL', 
            aggfunc=lambda x: (df_filtrado.loc[x.index, 'ESTADO'] == 'RECHAZADO').sum(),
            fill_value=0
        )
        st.dataframe(cruce, use_container_width=True)
        
        fig = px.imshow(cruce, text_auto=True, aspect="auto", title="Mapa de Calor - Rechazos")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#cdd6f4')
        st.plotly_chart(fig, use_container_width=True, key="cruce_mapa_calor")
    else:
        st.info("No hay datos para cruzar con los filtros actuales.")

elif menu == "⭐ Control de Calidad":
    st.header("⭐ Control de Calidad")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Porcentaje de Rechazo por Material")
        if not df_filtrado.empty:
            rechazo_mat = df_filtrado.groupby('MATERIAL')['ESTADO'].value_counts(normalize=True).unstack(fill_value=0) * 100
            if 'RECHAZADO' in rechazo_mat.columns:
                st.bar_chart(rechazo_mat['RECHAZADO'])
            else:
                st.success("No hay piezas rechazadas en los filtros actuales.")
    
    with col2:
        st.subheader("Dispersión de Tiempos de Entrega")
        if not df_filtrado.empty:
            fig = px.box(df_filtrado, x='MATERIAL', y='TIEMPO DEMORADO (DÍAS)', color='MATERIAL')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#cdd6f4')
            st.plotly_chart(fig, use_container_width=True, key="calidad_dispersion")

elif menu == "🔍 Hallazgos":
    st.header("🔍 Hallazgos de Calidad")
    df_rechazados = df_filtrado[df_filtrado['ESTADO'] == 'RECHAZADO']
    if not df_rechazados.empty:
        hallazgos = df_rechazados['TIPO_DEFECTO'].value_counts()
        st.bar_chart(hallazgos)
        st.subheader("Detalle de Piezas Rechazadas")
        st.dataframe(df_rechazados[['OPERARIO','MATERIAL','TIPO_DEFECTO','QTY']], use_container_width=True)
    else:
        st.success("🎉 Cero hallazgos negativos en los filtros actuales.")

elif menu == "⚠️ Incidentes":
    st.header("⚠️ Registro de Incidentes (SST)")
    if not df_filtrado.empty:
        inc = df_filtrado['INCIDENTE'].value_counts()
        st.bar_chart(inc)
        
        incidentes_reales = df_filtrado[df_filtrado['INCIDENTE'] != 'Ninguno']
        if not incidentes_reales.empty:
            st.subheader("Detalle de Incidentes")
            st.dataframe(incidentes_reales[['OPERARIO','MATERIAL','INCIDENTE','TIEMPO DEMORADO (DÍAS)']], use_container_width=True)
        else:
            st.success("✅ No se registran incidentes (Cero accidentes) en los filtros actuales.")

elif menu == "🛡️ Riesgos":
    st.header("🛡️ Matriz de Riesgos")
    if not df_filtrado.empty:
        riesgos = df_filtrado.groupby(['MATERIAL','NIVEL_RIESGO']).size().unstack(fill_value=0)
        st.dataframe(riesgos, use_container_width=True)
        
        fig = px.imshow(riesgos, text_auto=True, color_continuous_scale='RdYlGn_r', title="Nivel de Riesgo por Material")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#cdd6f4')
        st.plotly_chart(fig, use_container_width=True, key="riesgos_matriz")


# ==========================================
# 2. MÓDULOS OPERATIVOS
# ==========================================

elif menu == "📝 Nueva Orden de Trabajo":
    st.title("📝 Registrar Nueva Orden")
    if es_admin:
        sedes_existentes = sorted([str(s) for s in df_actual['SOLICITANTE'].unique() if pd.notna(s)])
        opciones_sedes = sedes_existentes + ["Otro"]
        
        col1, col2 = st.columns(2)
        with col1:
            sede_seleccionada = st.selectbox("Selecciona la Sede Solicitante:", opciones_sedes)
            if sede_seleccionada == "Otro":
                solicitante = st.text_input("❌ Escribe el nombre de la nueva sede:")
            else:
                solicitante = sede_seleccionada
                
            pieza = st.text_input("Nombre de la Pieza")
            cantidad = st.number_input("Cantidad (QTY)", min_value=1, step=1)
            
        with col2:
            prioridad = st.selectbox("Prioridad", ["BAJA (MP)", "MEDIA (FL)", "ALTA (FS)"])
            material = st.selectbox("Material", ["ACERO", "ACERO PLATA", "ALUMINIO", "BRONCE", "ACERO PLATA Y ALUMINIO", "POR DEFINIR"])
            dimensiones = st.text_input("Dimensiones (Opcional)", value="SEGUN MUESTRA")
            
        st.write("") 
        
        if st.button("➕ Guardar Orden en Sistema", use_container_width=True):
            if solicitante == "" or pieza == "":
                st.error("⚠️ La Sede y el Nombre de la Pieza son obligatorios.")
            else:
                Motor.agregar_solicitud(solicitante, prioridad, pieza, material, cantidad, dimensiones)
                st.success(f"✅ ¡Orden creada exitosamente para {solicitante}! Ya aparece 'EN PROCESO'.")
                st.rerun()
    else:
        st.error("🔒 Acceso denegado. Ingresa la contraseña en el menú lateral para usar esta función.")

elif menu == "✅ Control de Entregas":
    st.title("✅ Control de Producción y Entregas")
    if es_admin:
        df_pendientes = df_actual[df_actual['ESTADO'] == 'EN PROCESO']
        if not df_pendientes.empty:
            st.write("### 🛠️ Trabajos Activos en Taller:")
            st.dataframe(df_pendientes[['SOLICITANTE', 'PRIORIDAD', 'NOMBRE PIEZA', 'QTY', 'MATERIAL']], use_container_width=True)
            
            st.divider()
            st.subheader("Marcar trabajo como Terminado")
            
            opciones = []
            for indice, fila in df_pendientes.iterrows():
                opciones.append(f"Índice {indice} | {fila['QTY']}x {fila['NOMBRE PIEZA']} - {fila['SOLICITANTE']}")
                
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                trabajo_seleccionado = st.selectbox("Selecciona el trabajo finalizado:", opciones)
            with col_btn:
                st.write("") 
                st.write("") 
                if st.button("Confirmar Entrega 🚀", use_container_width=True):
                    indice_real = int(trabajo_seleccionado.split(" ")[1])
                    Motor.marcar_entregado(indice_real)
                    st.success("¡Pieza entregada con éxito! Remisión generada.")
                    st.balloons() 
                    st.rerun()
        else:
            st.success("🎉 ¡Excelente trabajo! El taller no tiene órdenes pendientes.")
            
        st.divider()
        st.subheader("🔍 Buscador de Remisiones")
        busqueda = st.text_input("Ingresa el número de remisión para ver los detalles:")
        df_entregados = df_actual[df_actual['ESTADO'] == 'ENTREGADO'].copy()
        
        if busqueda and 'nro de remision' in df_entregados.columns:
            df_entregados['Remision_Limpia'] = pd.to_numeric(df_entregados['nro de remision'], errors='coerce').fillna(0).astype(int).astype(str)
            resultado = df_entregados[df_entregados['Remision_Limpia'] == busqueda.strip()]
            
            if not resultado.empty:
                st.success(f"✅ Encontrado:")
                st.dataframe(resultado.drop(columns=['Remision_Limpia']), use_container_width=True)
            else:
                st.warning("⚠️ No se encontró ninguna pieza vinculada a esa remisión.")
    else:
        st.error("🔒 Acceso denegado. Ingresa la contraseña en el menú lateral.")

elif menu == "👷 Vista Operario":
    st.title("👷 Panel de Producción Operario")
    
    lista_operarios = [op for op in df_actual['OPERARIO'].unique() if pd.notna(op)]
    if not lista_operarios:
        lista_operarios = ["Operario Uno", "Operario Dos", "Operario Tres"]
        
    nombre_operario = st.selectbox("Selecciona tu nombre:", lista_operarios)
    st.divider()
    
    df_pendientes = df_actual[df_actual['ESTADO'] == 'EN PROCESO']
    if not df_pendientes.empty:
        st.subheader("Trabajos en Taller:")
        st.dataframe(df_pendientes[['SOLICITANTE', 'NOMBRE PIEZA', 'QTY', 'OPERARIO']], use_container_width=True)
        
        st.divider()
        st.subheader("Asignar trabajo a mi nombre")
        
        opciones_trabajo = []
        for idx, row in df_pendientes.iterrows():
            opciones_trabajo.append(f"Fila {idx} - {row['NOMBRE PIEZA']} (Para: {row['SOLICITANTE']})")
            
        seleccion = st.selectbox("¿Qué pieza vas a fabricar?", opciones_trabajo)
        
        if st.button("Tomar Trabajo"):
            idx_real = int(seleccion.split(" ")[1])
            Motor.asignar_operario(idx_real, nombre_operario)
            st.toast(f"¡Trabajo asignado a {nombre_operario}! ⚙️", icon="👷")
            st.success(f"¡Trabajo asignado a {nombre_operario}!")
            st.rerun()
    else:
        st.info("No hay trabajos activos en el taller en este momento.")
