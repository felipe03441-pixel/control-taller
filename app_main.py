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
    h1, h2, h3 { color: #FFFFFF!important; } /* Blanco para resaltar sobre el fondo azul */
    
    /* Color de las tarjetas de métricas */
    [data-testid="stMetricValue"] { color: #00FF66; } /* Verde brillante para los números grandes */
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
    
    # Manejo de nulos en listas desplegables
    materiales_disp = [m for m in df_actual['MATERIAL'].unique() if pd.notna(m)]
    operarios_disp = [o for o in df_actual['OPERARIO'].unique() if pd.notna(o)]
    
    material_sel = st.sidebar.multiselect("Filtrar Material", materiales_disp, default=materiales_disp)
    operario_sel = st.sidebar.multiselect("Filtrar Operario", operarios_disp, default=operarios_disp)
    
    # Aplicar filtros
    df_filtrado = df_actual[
        (df_actual['MATERIAL'].isin(material_sel)) & 
        (df_actual['OPERARIO'].isin(operario_sel))
    ]
else:
    df_filtrado = df_actual.copy()

st.sidebar.divider()
st.sidebar.caption("Dashboard CNC v2.0 | Producción y Mantenimiento")


# ==========================================
# 1. MÓDULOS DE ANÁLISIS (DASHBOARD GENERAL)
# ==========================================

if menu == "📊 Dashboard General":
    st.header("📊 Dashboard General de Producción")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Piezas Solicitadas", f"{int(df_filtrado['QTY'].sum()):,}")
    col2.metric("Piezas Entregadas", f"{int(df_filtrado[df_filtrado['ESTADO']=='ENTREGADO']['QTY'].sum()):,}")
    
    tiempo_prom = df_filtrado['TIEMPO DEMORADO (DÍAS)'].mean()
    col3.metric("Tiempo Prom. Entrega", f"{tiempo_prom:.1f} días" if not pd.isna(tiempo_prom) else "N/A")
    
    tasa_rechazo = (df_filtrado['ESTADO']=='RECHAZADO').mean() * 100
    col4.metric("Tasa de Rechazo", f"{tasa_rechazo:.1f}%" if not pd.isna(tasa_rechazo) else "0.0%")
    
    st.divider()
    
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
            values='QTY', 
            index='OPERARIO', 
            columns='MATERIAL', 
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
    
    if not df_filtr
