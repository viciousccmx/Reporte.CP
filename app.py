import streamlit as st
import pandas as pd
import io

# 1. Configuracion de la pagina
st.set_page_config(page_title="Dashboard Profesional", layout="wide")

# 2. CSS para formato impecable y justificado
st.markdown("""
    <style>
    .stTable td, .stTable th {
        white-space: nowrap !important;
        text-align: center !important;
        padding: 10px 20px !important;
    }
    .stTable td:nth-child(1), .stTable th:nth-child(1) {
        text-align: left !important;
    }
    .stTable {
        width: 100%;
        border-collapse: collapse;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Reporte de Transacciones e Importes")

def cargar_datos(archivo):
    if archivo is None: return None
    try:
        contenido = archivo.getvalue()
        for enc in ['utf-8-sig', 'latin1', 'utf-8', 'cp1252']:
            try:
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(contenido), encoding=enc, sep=None, engine='python')
                else:
                    df = pd.read_excel(archivo)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if 'SERVICIO' in df.columns: return df
            except: continue
        return df
    except Exception as e:
        st.error(f"Error al leer {archivo.name}: {e}")
        return None

# Sidebar
st.sidebar.header("Carga de Archivos")
f_actual = st.sidebar.file_uploader("Archivo MES ACTUAL", type=["csv", "xlsx"])
f_anterior = st.sidebar.file_uploader("Archivo MES ANTERIOR", type=["csv", "xlsx"])

if f_actual and f_anterior:
    df_act = cargar_datos(f_actual)
    df_ant = cargar_datos(f_anterior)

    cols_nec = ['SERVICIO', 'CONTEO ACT', 'IMPORTE ACT']
    
    if df_act is not None and df_ant is not None and all(c in df_act.columns for c in cols_nec):
        try:
            telcel_list = [
                'TELCEL PAQUETES', 'TELCEL FACTURA', 'TELCEL VENTA DE TIEMPO AIRE', 
                'AMIGO PAGUITOS', 'TELCEL PAQUETES MIXTOS', 'TELCEL PAQUETES POSPAGO'
            ]

            def procesar_dashboard(df_a, df_p, filtro, es_top=False):
                df_a['SERVICIO'] = df_a['SERVICIO'].astype(str).str.strip().str.upper()
                df_p['SERVICIO'] = df_p['SERVICIO'].astype(str).str.strip().str.upper()

                if not es_top:
                    # Tabla Telcel: Sumatoria de solo estos servicios
                    a_subset = df_a[df_a['SERVICIO'].isin(filtro)].copy()
                    p_subset = df_p[df_p['SERVICIO'].isin(filtro)].copy()
                    display_df = a_subset
                else:
                    # Tabla Otros: Listar Top 5 pero sumar TODOS los demas
                    a_subset = df_a[~df_a['SERVICIO'].isin(filtro)].copy()
                    p_subset = df_p[~df_p['SERVICIO'].isin(filtro)].copy()
                    top5_names = a_subset.sort_values('CONTEO ACT', ascending=False).head(5)['SERVICIO']
                    display_df = a_subset[a_subset['SERVICIO'].isin(top5_names)].copy()

                # Columnas para calculos
                cols = ['SERVICIO', 'CONTEO ACT', 'IMPORTE ACT']
                res = pd.merge(display_df[cols], df_p[cols], on='SERVICIO', how='left', suffixes=('_ACT', '_ANT')).fillna(0)

                # Calculos de variacion en las filas
                for k in ['CONTEO', 'IMPORTE']:
                    ant, act = f'{k} ACT_ANT', f'{k} ACT_ACT'
                    res[f'VAR % {k}'] = ((res[act] - res[ant]) / res[ant] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                
                # --- LOGICA CORREGIDA DE SUMATORIA ---
                # Sumamos de a_subset y p_subset (que contienen todos los servicios del grupo)
                s_c_act = a_subset['CONTEO ACT'].sum()
                s_c_ant = p_subset['CONTEO ACT'].sum()
                s_i_act = a_subset['IMPORTE ACT'].sum()
                s_i_ant = p_subset['IMPORTE ACT'].sum()
                
                fila_sum = pd.DataFrame([{
                    'SERVICIO': 'SUMATORIA',
                    'CONTEO ACT_ACT': s_c_act, 'CONTEO ACT_ANT': s_c_ant,
                    'VAR % CONTEO': 0 if s_c_ant == 0 else ((s_c_act - s_c_ant) / s_c_ant) * 100,
                    'IMPORTE ACT_ACT': s_i_act, 'IMPORTE ACT_ANT': s_i_ant,
                    'VAR % IMPORTE': 0 if s_i_ant == 0 else ((s_i_act - s_i_ant) / s_i_ant) * 100
                }])
                return pd.concat([res, fila_sum], ignore_index=True)

            # Generar tablas
            t1 = procesar_dashboard(df_act, df_ant, telcel_list)
            t2 = procesar_dashboard(df_act, df_ant, telcel_list, es_top=True)

            orden = ['SERVICIO', 'CONTEO ACT_ACT', 'CONTEO ACT_ANT', 'VAR % CONTEO', 'IMPORTE ACT_ACT', 'IMPORTE ACT_ANT', 'VAR % IMPORTE']
            titulos = {'SERVICIO': 'SERVICIO', 'CONTEO ACT_ACT': 'CONTEO ACT.', 'CONTEO ACT_ANT': 'CONTEO ANT.', 'VAR % CONTEO': 'VAR % (C)', 
                       'IMPORTE ACT_ACT': 'IMPORTE ACT.', 'IMPORTE ACT_ANT': 'IMPORTE ANT.', 'VAR % IMPORTE': 'VAR % (I)'}

            def formato(df):
                return df[orden].rename(columns=titulos).style.format({
                    'CONTEO ACT.': '{:,.0f}', 'CONTEO ANT.': '{:,.0f}', 'VAR % (C)': '{:,.2f}%',
                    'IMPORTE ACT.': '${:,.2f}', 'IMPORTE ANT.': '${:,.2f}', 'VAR % (I)': '{:,.2f}%'
                }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', subset=['VAR % (C)', 'VAR % (I)'])

            st.subheader("Análisis de Servicios Telcel")
            st.table(formato(t1))
            st.write("---")
            st.subheader("Top 5 Otros Servicios (Sumatoria incluye todos los no-Telcel)")
            st.table(formato(t2))

        except Exception as e:
            st.error(f"Error en el proceso: {e}")
else:
    st.info("Sube ambos archivos para comparar.")
