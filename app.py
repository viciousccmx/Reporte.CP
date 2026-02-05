import streamlit as st
import pandas as pd

# 1. Configuraci¨®n de la p¨¢gina
st.set_page_config(page_title="Dashboard Pro", layout="wide")

st.markdown("""
    <style>
    .stTable { width: 100%; }
    .css-12oz5g7 { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("?? Reporte Comparativo de Servicios")

# Funci¨®n de carga ultra-robusta
def load_data(file):
    if file is None: return None
    try:
        if file.name.endswith('.csv'):
            # Intenta con 3 codificaciones comunes para evitar errores de decode
            for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                try:
                    file.seek(0)
                    df = pd.read_csv(file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
        else:
            df = pd.read_excel(file)
        
        # Estandarizar nombres de columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error cr¨ªtico al leer {file.name}: {e}")
        return None

# Sidebar
st.sidebar.header("Carga de Archivos")
f_act = st.sidebar.file_uploader("MES ACTUAL", type=["csv", "xlsx"])
f_ant = st.sidebar.file_uploader("MES ANTERIOR", type=["csv", "xlsx"])

if f_act and f_ant:
    df_act = load_data(f_act)
    df_ant = load_data(f_ant)

    if df_act is not None and df_ant is not None:
        try:
            # Lista de servicios (en may¨²sculas para coincidir con el strip().upper())
            telcel_list = [
                'TELCEL PAQUETES', 'TELCEL FACTURA', 'TELCEL VENTA DE TIEMPO AIRE', 
                'AMIGO PAGUITOS', 'TELCEL PAQUETES MIXTOS', 'TELCEL PAQUETES POSPAGO'
            ]

            def procesar_df(act_df, ant_df, filtro, es_top=False):
                # Limpiar columna servicio
                act_df['SERVICIO'] = act_df['SERVICIO'].str.strip().str.upper()
                ant_df['SERVICIO'] = ant_df['SERVICIO'].str.strip().str.upper()

                if not es_top:
                    a = act_df[act_df['SERVICIO'].isin(filtro)].copy()
                else:
                    otros = act_df[~act_df['SERVICIO'].isin(filtro)]
                    top5 = otros.sort_values('CONTEO ACT', ascending=False).head(5)
                    a = act_df[act_df['SERVICIO'].isin(top5['SERVICIO'])].copy()

                # Merge
                res = pd.merge(
                    a[['SERVICIO', 'CONTEO ACT']], 
                    ant_df[['SERVICIO', 'CONTEO ACT']], 
                    on='SERVICIO', how='left', suffixes=('_ACT', '_ANT')
                ).fillna(0)

                # Variaci¨®n
                res['VAR_%'] = 0.0
                mask = res['CONTEO ACT_ANT'] != 0
                res.loc[mask, 'VAR_%'] = ((res['CONTEO ACT_ACT'] - res['CONTEO ACT_ANT']) / res['CONTEO ACT_ANT']) * 100
                
                # Sumatoria
                s_act = res['CONTEO ACT_ACT'].sum()
                s_ant = res['CONTEO ACT_ANT'].sum()
                s_var = ((s_act - s_ant) / s_ant * 100) if s_ant != 0 else 0
                
                fila_sum = pd.DataFrame([['SUMATORIA', s_act, s_ant, s_var]], 
                                       columns=['SERVICIO', 'CONTEO ACT_ACT', 'CONTEO ACT_ANT', 'VAR_%'])
                
                return pd.concat([res, fila_sum], ignore_index=True)

            # Tablas
            t1 = procesar_df(df_act, df_ant, telcel_list)
            t2 = procesar_df(df_act, df_ant, telcel_list, es_top=True)

            # Formateo visual seguro (sin applymap que suele dar error en web)
            def format_table(df):
                styled = df.style.format({
                    'CONTEO ACT_ACT': '{:,.0f}',
                    'CONTEO ACT_ANT': '{:,.0f}',
                    'VAR_%': '{:,.2f}%'
                })
                # Pintar de rojo variaciones negativas
                return styled.apply(lambda x: ['color: red' if isinstance(v, (int, float)) and v < 0 else '' for v in x], subset=['VAR_%'])

            st.subheader("An¨¢lisis Servicios Telcel")
            st.table(format_table(t1))

            st.write("---")

            st.subheader("Top 5 Otros Servicios")
            st.table(format_table(t2))

        except Exception as e:
            st.error(f"Error en el procesamiento de datos: {e}")
            st.info("Verifica que las columnas se llamen 'SERVICIO' y 'CONTEO ACT'")
else:
    st.info("Sube ambos archivos para generar el dashboard.")