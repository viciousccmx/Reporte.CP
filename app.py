import streamlit as st
import pandas as pd
import chardet

st.set_page_config(page_title="Dashboard Comparativo", layout="wide")

st.title("?? Reporte de Transacciones")

def load_data(file):
    if file is None: return None
    try:
        if file.name.endswith('.csv'):
            # Detectar autom¨¢ticamente el encoding del archivo
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding_detectado = result['encoding']
            
            # Volver al inicio del archivo para leerlo
            file.seek(0)
            try:
                # Intentamos con el detectado, si falla probamos latin1
                df = pd.read_csv(file, encoding=encoding_detectado)
            except:
                file.seek(0)
                df = pd.read_csv(file, encoding='latin1')
        else:
            df = pd.read_excel(file)
        
        # Estandarizar nombres de columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al cargar {file.name}: {e}")
        return None

# Sidebar
st.sidebar.header("Carga de Datos")
f_act = st.sidebar.file_uploader("Archivo MES ACTUAL", type=["csv", "xlsx"])
f_ant = st.sidebar.file_uploader("Archivo MES ANTERIOR", type=["csv", "xlsx"])

if f_act and f_ant:
    df_act = load_data(f_act)
    df_ant = load_data(f_ant)

    if df_act is not None and df_ant is not None:
        try:
            # Lista de servicios en MAY¨²SCULAS
            telcel_list = [
                'TELCEL PAQUETES', 'TELCEL FACTURA', 'TELCEL VENTA DE TIEMPO AIRE', 
                'AMIGO PAGUITOS', 'TELCEL PAQUETES MIXTOS', 'TELCEL PAQUETES POSPAGO'
            ]

            def procesar(df_a, df_p, filtro, es_top=False):
                # Limpiar columna servicio
                df_a['SERVICIO'] = df_a['SERVICIO'].astype(str).str.strip().str.upper()
                df_p['SERVICIO'] = df_p['SERVICIO'].astype(str).str.strip().str.upper()

                if not es_top:
                    a = df_a[df_a['SERVICIO'].isin(filtro)].copy()
                else:
                    otros = df_a[~df_a['SERVICIO'].isin(filtro)]
                    top5 = otros.sort_values('CONTEO ACT', ascending=False).head(5)
                    a = df_a[df_a['SERVICIO'].isin(top5['SERVICIO'])].copy()

                # Merge
                res = pd.merge(
                    a[['SERVICIO', 'CONTEO ACT']], 
                    df_p[['SERVICIO', 'CONTEO ACT']], 
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

            t1 = procesar(df_act, df_ant, telcel_list)
            t2 = procesar(df_act, df_ant, telcel_list, es_top=True)

            # Formato visual
            def format_table(df):
                return df.style.format({
                    'CONTEO ACT_ACT': '{:,.0f}',
                    'CONTEO ACT_ANT': '{:,.0f}',
                    'VAR_%': '{:,.2f}%'
                }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', subset=['VAR_%'])

            st.subheader("An¨¢lisis Servicios Telcel")
            st.table(format_table(t1))

            st.write("---")

            st.subheader("Top 5 Otros Servicios")
            st.table(format_table(t2))

        except Exception as e:
            st.error(f"Error en el procesamiento: {e}")
else:
    st.info("Sube los archivos en la barra lateral.")