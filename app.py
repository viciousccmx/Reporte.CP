import streamlit as st
import pandas as pd

# 1. Configuraci車n de p芍gina
st.set_page_config(page_title="Reporte Comparativo", layout="wide")

st.title("?? Reporte de Transacciones")

# Funci車n de carga mejorada con m迆ltiples encodings
def load_data(file):
    if file is None: return None
    try:
        # Intentamos leer con UTF-8, si falla vamos a Latin-1
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, encoding='latin1')
        
        # Limpieza profunda de columnas
        df.columns = [str(col).strip() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"No se pudo leer el archivo {file.name}. Error: {e}")
        return None

# Sidebar
st.sidebar.header("Carga de Datos")
file_act = st.sidebar.file_uploader("Archivo MES ACTUAL", type=["csv", "xlsx"])
file_ant = st.sidebar.file_uploader("Archivo MES ANTERIOR", type=["csv", "xlsx"])

if file_act and file_ant:
    df_act = load_data(file_act)
    df_ant = load_data(file_ant)

    if df_act is not None and df_ant is not None:
        try:
            # Servicios requeridos
            servicios_telcel = [
                'Telcel Paquetes', 'Telcel factura', 'Telcel Venta de tiempo aire', 
                'Amigo Paguitos', 'Telcel Paquetes Mixtos', 'Telcel Paquetes Pospago'
            ]

            def procesar(df_a, df_p, lista, es_top=False):
                # Filtrado seguro
                if not es_top:
                    a = df_a[df_a['SERVICIO'].isin(lista)].copy()
                    p = df_p[df_p['SERVICIO'].isin(lista)].copy()
                else:
                    otros = df_a[~df_a['SERVICIO'].isin(lista)]
                    top5 = otros.sort_values('CONTEO ACT', ascending=False).head(5)['SERVICIO'].tolist()
                    a = df_a[df_a['SERVICIO'].isin(top5)].copy()
                    p = df_p[df_p['SERVICIO'].isin(top5)].copy()

                # Uni車n de tablas
                res = pd.merge(
                    a[['SERVICIO', 'CONTEO ACT']], 
                    p[['SERVICIO', 'CONTEO ACT']], 
                    on='SERVICIO', how='left', suffixes=(' (Act)', ' (Ant)')
                ).fillna(0)

                # C芍lculo de variaci車n
                res['% Var'] = 0.0
                mask = res['CONTEO ACT (Ant)'] != 0
                res.loc[mask, '% Var'] = ((res['CONTEO ACT (Act)'] - res['CONTEO ACT (Ant)']) / res['CONTEO ACT (Ant)']) * 100
                
                # Fila de Sumatoria
                s_act = res['CONTEO ACT (Act)'].sum()
                s_ant = res['CONTEO ACT (Ant)'].sum()
                s_var = ((s_act - s_ant) / s_ant * 100) if s_ant != 0 else 0
                
                fila_sum = pd.DataFrame([['SUMATORIA', s_act, s_ant, s_var]], 
                                       columns=['SERVICIO', 'CONTEO ACT (Act)', 'CONTEO ACT (Ant)', '% Var'])
                
                return pd.concat([res, fila_sum], ignore_index=True)

            # Generar Tablas
            t1 = procesar(df_act, df_ant, servicios_telcel)
            t2 = procesar(df_act, df_ant, servicios_telcel, es_top=True)

            # Funci車n para aplicar formato y color sin romper st.table
            def aplicar_estilo(df):
                return df.style.format({
                    'CONTEO ACT (Act)': '{:,.0f}',
                    'CONTEO ACT (Ant)': '{:,.0f}',
                    '% Var': '{:,.2f}%'
                }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', subset=['% Var'])

            # Mostrar una por fila
            st.subheader("An芍lisis Servicios Telcel")
            st.table(aplicar_estilo(t1))

            st.write("---")

            st.subheader("Top 5 Otros Servicios")
            st.table(aplicar_estilo(t2))

        except KeyError as e:
            st.error(f"Error: No se encontr車 la columna {e}. Revisa que tus archivos tengan 'SERVICIO' y 'CONTEO ACT'.")
        except Exception as e:
            st.error(f"Error inesperado: {e}")
else:
    st.info("Sube los archivos en la barra lateral.")