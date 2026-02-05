import streamlit as st
import pandas as pd
import io

# Configuracion de pagina
st.set_page_config(page_title="Dashboard Comparativo", layout="wide")

st.title("Reporte de Transacciones e Importes")

def cargar_datos(archivo):
    if archivo is None:
        return None
    try:
        contenido = archivo.getvalue()
        for codificacion in ['latin1', 'utf-8', 'cp1252']:
            try:
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(contenido), encoding=codificacion)
                else:
                    df = pd.read_excel(archivo)
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
                    a = df_a[df_a['SERVICIO'].isin(filtro)].copy()
                else:
                    otros = df_a[~df_a['SERVICIO'].isin(filtro)]
                    top5_nombres = otros.sort_values('CONTEO ACT', ascending=False).head(5)['SERVICIO']
                    a = df_a[df_a['SERVICIO'].isin(top5_nombres)].copy()

                cols_interes = ['SERVICIO', 'CONTEO ACT', 'IMPORTE ACT']
                
                # Unir meses
                res = pd.merge(
                    a[cols_interes], 
                    df_p[cols_interes], 
                    on='SERVICIO', how='left', suffixes=('_ACT', '_ANT')
                ).fillna(0)

                # Variaciones
                res['VAR % CONTEO'] = 0.0
                mask_c = res['CONTEO ACT_ANT'] != 0
                res.loc[mask_c, 'VAR % CONTEO'] = ((res['CONTEO ACT_ACT'] - res['CONTEO ACT_ANT']) / res['CONTEO ACT_ANT']) * 100
                
                res['VAR % IMPORTE'] = 0.0
                mask_i = res['IMPORTE ACT_ANT'] != 0
                res.loc[mask_i, 'VAR % IMPORTE'] = ((res['IMPORTE ACT_ACT'] - res['IMPORTE ACT_ANT']) / res['IMPORTE ACT_ANT']) * 100
                
                # Fila Sumatoria
                s_c_act, s_c_ant = res['CONTEO ACT_ACT'].sum(), res['CONTEO ACT_ANT'].sum()
                s_i_act, s_i_ant = res['IMPORTE ACT_ACT'].sum(), res['IMPORTE ACT_ANT'].sum()
                
                fila_sum = pd.DataFrame([{
                    'SERVICIO': 'SUMATORIA',
                    'CONTEO ACT_ACT': s_c_act,
                    'CONTEO ACT_ANT': s_c_ant,
                    'VAR % CONTEO': 0 if s_c_ant == 0 else ((s_c_act - s_c_ant) / s_c_ant) * 100,
                    'IMPORTE ACT_ACT': s_i_act,
                    'IMPORTE ACT_ANT': s_i_ant,
                    'VAR % IMPORTE': 0 if s_i_ant == 0 else ((s_i_act - s_i_ant) / s_i_ant) * 100
                }])
                
                return pd.concat([res, fila_sum], ignore_index=True)

            t1 = procesar_tablas(df_act, df_ant, telcel_list)
            t2 = procesar_tablas(df_act, df_ant, telcel_list, es_top=True)

            column_order = ['SERVICIO', 'CONTEO ACT_ACT', 'CONTEO ACT_ANT', 'VAR % CONTEO', 'IMPORTE ACT_ACT', 'IMPORTE ACT_ANT', 'VAR % IMPORTE']
            t1, t2 = t1[column_order], t2[column_order]

            def estilizar(df):
                return df.style.format({
                    'CONTEO ACT_ACT': '{:,.0f}', 'CONTEO ACT_ANT': '{:,.0f}', 'VAR % CONTEO': '{:,.2f}%',
                    'IMPORTE ACT_ACT': '${:,.2f}', 'IMPORTE ACT_ANT': '${:,.2f}', 'VAR % IMPORTE': '{:,.2f}%'
                }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', 
                          subset=['VAR % CONTEO', 'VAR % IMPORTE'])

            st.subheader("Analisis de Servicios Telcel")
            st.table(estilizar(t1))
            st.write("---")
            st.subheader("Top 5 Otros Servicios")
            st.table(estilizar(t2))

        except Exception as e:
            st.error(f"Error en el proceso: {e}")
else:
    st.info("Sube los archivos en el panel izquierdo.")