import streamlit as st
import pandas as pd
import io

# Configuracion de pagina
st.set_page_config(page_title="Dashboard Comparativo Completo", layout="wide")

st.title("Reporte de Transacciones e Importes")

def cargar_datos(archivo):
    if archivo is None:
        return None
    try:
        contenido = archivo.getvalue()
        # Probar diferentes codificaciones para evitar errores de compilacion (como el 0xa8)
        for codificacion in ['latin1', 'utf-8', 'cp1252']:
            try:
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(contenido), encoding=codificacion)
                else:
                    df = pd.read_excel(archivo)
                
                # Estandarizar nombres de columnas a mayusculas
                df.columns = [str(c).strip().upper() for c in df.columns]
                return df
            except:
                continue
        return None
    except Exception as e:
        st.error(f"Error al leer archivo: {e}")
        return None

# Sidebar
st.sidebar.header("Carga de Archivos")
f_actual = st.sidebar.file_uploader("Archivo MES ACTUAL", type=["csv", "xlsx"])
f_anterior = st.sidebar.file_uploader("Archivo MES ANTERIOR", type=["csv", "xlsx"])

if f_actual and f_anterior:
    df_act = cargar_datos(f_actual)
    df_ant = cargar_datos(f_anterior)

    if df_act is not None and df_ant is not None:
        try:
            # Lista de servicios Telcel
            telcel_list = [
                'TELCEL PAQUETES', 'TELCEL FACTURA', 'TELCEL VENTA DE TIEMPO AIRE', 
                'AMIGO PAGUITOS', 'TELCEL PAQUETES MIXTOS', 'TELCEL PAQUETES POSPAGO'
            ]

            def procesar_tablas(df_a, df_p, filtro, es_top=False):
                # Limpieza de columna SERVICIO
                df_a['SERVICIO'] = df_a['SERVICIO'].astype(str).str.strip().str.upper()
                df_p['SERVICIO'] = df_p['SERVICIO'].astype(str).str.strip().str.upper()

                if not es_top:
                    a = df_a[df_a['