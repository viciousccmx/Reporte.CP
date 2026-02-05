import streamlit as st
import pandas as pd

# Configuraci¨®n de la p¨¢gina
st.set_page_config(page_title="Reporte Comparativo Completo", layout="wide")

st.markdown("""
    <style>
    /* Estilo para que las tablas ocupen el ancho total y se vean limpias */
    .stTable {
        width: 100%;
    }
    h2 {
        color: #003366;
        border-bottom: 2px solid #003366;
        padding-bottom: 10px;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("?? Reporte de Transacciones")

# Sidebar
st.sidebar.header("Carga de Archivos")
file_actual = st.sidebar.file_uploader("Archivo MES ACTUAL", type=["csv", "xlsx"])
file_pasado = st.sidebar.file_uploader("Archivo MES ANTERIOR", type=["csv", "xlsx"])

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

# Funci¨®n para aplicar color rojo a valores negativos (funciona con st.table)
def style_negative_red(val):
    if isinstance(val, str) and '-' in val:
        return 'color: red'
    return ''

if file_actual and file_pasado:
    try:
        df_act = load_data(file_actual)
        df_pas = load_data(file_pasado)

        servicios_telcel = [
            'Telcel Paquetes', 'Telcel factura', 'Telcel Venta de tiempo aire', 
            'Amigo Paguitos', 'Telcel Paquetes Mixtos', 'Telcel Paquetes Pospago'
        ]

        def procesar_tabla(df_a, df_p, lista_servicios, es_top5=False):
            if not es_top5:
                a = df_a[df_a['SERVICIO'].isin(lista_servicios)].copy()
                p = df_p[df_p['SERVICIO'].isin(lista_servicios)].copy()
            else:
                df_otros_act = df_a[~df_a['SERVICIO'].isin(lista_servicios)]
                top5_nombres = df_otros_act.sort_values('CONTEO ACT', ascending=False).head(5)['SERVICIO'].tolist()
                a = df_a[df_a['SERVICIO'].isin(top5_nombres)].copy()
                p = df_p[df_p['SERVICIO'].isin(top5_