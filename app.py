import streamlit as st
import pandas as pd

# 1. Configuraci¨®n de p¨¢gina
st.set_page_config(page_title="Dashboard Comparativo", layout="wide")

st.title("?? Reporte Comparativo de Servicios")

# Sidebar
st.sidebar.header("Carga de Archivos")
file_actual = st.sidebar.file_uploader("Archivo MES ACTUAL", type=["csv", "xlsx"])
file_pasado = st.sidebar.file_uploader("Archivo MES ANTERIOR", type=["csv", "xlsx"])

def load_data(file):
    if file is None: return None
    try:
        if file.name.endswith('.csv'):
            # El error de decodificaci¨®n se resuelve probando con 'latin1'
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0) # Reiniciar el puntero del archivo
                df = pd.read_csv(file, encoding='latin1')
        else:
            df = pd.read_excel(file)
        
        # Limpiar espacios en blanco en los nombres de columnas
        df.columns = df.columns.str.strip() 
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo {file.name}: {e}")
        return None

if file_actual and file_pasado:
    df_act = load_data(file_actual)
    df_pas = load_data(file_pasado)

    if df_act is not None and df_pas is not None:
        try:
            # Lista de servicios exactos
            servicios_telcel = [
                'Telcel Paquetes', 'Telcel factura', 'Telcel Venta de tiempo aire', 
                'Amigo Paguitos', 'Telcel Paquetes Mixtos', 'Telcel Paquetes Pospago'
            ]

            def generar_tabla_comparativa(df_a, df_p, lista_filtro, es_top5=False):
                # Filtrar
                if not es_top5:
                    a = df_a[df_a['SERVICIO'].isin(lista_filtro)].copy()
                    p = df_p[df_p['SERVICIO'].isin(lista_filtro)].copy()
                else:
                    otros = df_a[~df_a['SERVICIO'].isin(lista_filtro)]
                    top5_nombres = otros.sort_values('CONTEO ACT', ascending=False).head(5)['SERVICIO'].tolist()
                    a = df_a[df_a['SERVICIO'].isin(top5_nombres)].copy()
                    p = df_p[df_p['SERVICIO'].isin(top5_nombres)].copy()

                # Unir datos
                m = pd.merge(
                    a[['SERVICIO', 'CONTEO ACT']], 
                    p[['SERVICIO', 'CONTEO ACT']], 
                    on='SERVICIO', how='left', suffixes=(' (Act)', ' (Ant)')
                ).fillna(0)

                # Calcular Variaci¨®n
                def calc_var(row):
                    ant = row['CONTEO ACT (Ant)']
                    act = row['CONTEO ACT (Act)']
                    if ant == 0: return 100.0 if act > 0 else 0.0
                    return ((act - ant) / ant) * 100

                m['Var %'] = m.apply(calc_var, axis=1)

                # A?adir Sumatoria
                sum_act = m['CONTEO ACT (Act)'].sum()
                sum_ant = m['CONTEO ACT (Ant)'].sum()
                sum_var = ((sum_act - sum_ant) / sum_ant * 100) if sum_ant != 0 else 0
                
                fila_sum = pd.DataFrame([{
                    'SERVICIO': 'SUMATORIA',
                    'CONTEO ACT (Act)': sum_act,
                    'CONTEO ACT (Ant)': sum_ant,
                    'Var %': sum_var
                }])
                
                return pd.concat([m, fila_sum], ignore_index=True)

            # Procesar
            tabla1 = generar_tabla_comparativa(df_act, df_pas, servicios_telcel)
            tabla2 = generar_tabla_comparativa(df_act, df_pas, servicios_telcel, es_top5=True)

            # Formato y estilo
            def format_style(df):
                return df.style.format({
                    'CONTEO ACT (Act)': '{:,.0f}',
                    'CONTEO ACT (Ant)': '{:,.0f}',
                    'Var %': '{:,.2f}%'
                }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', subset=['Var %'])

            # Mostrar
            st.subheader("An¨¢lisis Servicios Telcel")
            st.table(format_style(tabla1))

            st.write("---")

            st.subheader("Top 5 Otros Servicios")
            st.table(format_style(tabla2))

        except Exception as e:
            st.error(f"Error en el procesamiento: {e}")
else:
    st.info("Sube ambos archivos para comparar.")