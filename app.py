import streamlit as st
import pandas as pd

# 1. Configuración de la página web
st.set_page_config(page_title="Dashboard de Servicios", layout="wide")

# Estilos CSS para mejorar la apariencia
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTable { background-color: white; border-radius: 5px; }
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Dashboard de Análisis de Servicios")

# 2. Sección para subir el archivo
st.sidebar.header("Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV o Excel", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Cargar el archivo según su formato
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 3. Definición de servicios para la primera tabla (Telcel)
        servicios_telcel = [
            'Telcel Paquetes', 
            'Telcel factura', 
            'Telcel Venta de tiempo aire', 
            'Amigo Paguitos', 
            'Telcel Paquetes Mixtos', 
            'Telcel Paquetes Pospago'
        ]
        
        # Filtrar y preparar Tabla 1
        df_telcel = df[df['SERVICIO'].isin(servicios_telcel)].copy()
        df_telcel['SERVICIO'] = pd.Categorical(df_telcel['SERVICIO'], categories=servicios_telcel, ordered=True)
        df_telcel = df_telcel.sort_values('SERVICIO')
        
        cols_finales = ['SERVICIO', 'CONTEO ACT', 'IMPORTE ACT']
        df_t1 = df_telcel[cols_finales].copy()
        
        # Fila de Sumatoria para Tabla 1
        sum_row_t1 = pd.DataFrame({
            'SERVICIO': ['SUMATORIA'],
            'CONTEO ACT': [df_t1['CONTEO ACT'].sum()],
            'IMPORTE ACT': [df_t1['IMPORTE ACT'].sum()]
        })
        df_t1_final = pd.concat([df_t1, sum_row_t1], ignore_index=True)

        # 4. Preparar Tabla 2: Top 5 Otros Servicios
        df_otros = df[~df['SERVICIO'].isin(servicios_telcel)].copy()
        df_top5 = df_otros.sort_values(by='CONTEO ACT', ascending=False).head(5)
        df_t2 = df_top5[cols_finales].copy()
        
        # Fila de Sumatoria para Tabla 2
        sum_row_t2 = pd.DataFrame({
            'SERVICIO': ['SUMATORIA'],
            'CONTEO ACT': [df_t2['CONTEO ACT'].sum()],
            'IMPORTE ACT': [df_t2['IMPORTE ACT'].sum()]
        })
        df_t2_final = pd.concat([df_t2, sum_row_t2], ignore_index=True)

        # 5. Mostrar Dashboards en Columnas
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Análisis Servicios Telcel")
            st.dataframe(df_t1_final.style.format({
                "CONTEO ACT": "{:,.0f}",
                "IMPORTE ACT": "${:,.2f}"
            }), use_container_width=True, hide_index=True)

        with col2:
            st.subheader("Top 5 Otros Servicios")
            st.dataframe(df_t2_final.style.format({
                "CONTEO ACT": "{:,.0f}",
                "IMPORTE ACT": "${:,.2f}"
            }), use_container_width=True, hide_index=True)

        st.success("Dashboard generado correctamente.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👋 Bienvenida/o. Por favor, carga un archivo desde la barra lateral para comenzar.")
