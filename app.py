import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="Comparativo Mensual", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #003366; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Comparativo de Transacciones Mensuales")

# 2. Carga de archivos en la barra lateral
st.sidebar.header("Carga de Datos")
file_actual = st.sidebar.file_uploader("Archivo MES ACTUAL", type=["csv", "xlsx"])
file_pasado = st.sidebar.file_uploader("Archivo MES ANTERIOR", type=["csv", "xlsx"])

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

def color_variacion(val):
    """Aplica rojo si la variación es negativa"""
    color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
    return f'color: {color}'

if file_actual and file_pasado:
    try:
        df_act = load_data(file_actual)
        df_pas = load_data(file_pasado)

        # Servicios específicos de Telcel
        servicios_telcel = [
            'Telcel Paquetes', 'Telcel factura', 'Telcel Venta de tiempo aire', 
            'Amigo Paguitos', 'Telcel Paquetes Mixtos', 'Telcel Paquetes Pospago'
        ]

        def procesar_tabla(df_a, df_p, lista_servicios, es_top5=False):
            # Filtrar por los servicios deseados
            if not es_top5:
                # Caso Telcel: Filtro fijo
                a = df_a[df_a['SERVICIO'].isin(lista_servicios)].copy()
                p = df_p[df_p['SERVICIO'].isin(lista_servicios)].copy()
            else:
                # Caso Top 5: Excluir Telcel del actual y tomar los 5 mayores
                df_otros_act = df_a[~df_a['SERVICIO'].isin(lista_servicios)]
                top5_nombres = df_otros_act.sort_values('CONTEO ACT', ascending=False).head(5)['SERVICIO'].tolist()
                a = df_a[df_a['SERVICIO'].isin(top5_nombres)].copy()
                p = df_p[df_p['SERVICIO'].isin(top5_nombres)].copy()

            # Unir datos del mes actual y pasado
            res = pd.merge(
                a[['SERVICIO', 'CONTEO ACT']], 
                p[['SERVICIO', 'CONTEO ACT']], 
                on='SERVICIO', 
                how='left', 
                suffixes=(' (Actual)', ' (Anterior)')
            ).fillna(0)

            # Calcular Variación
            res['% Variación'] = ((res['CONTEO ACT (Actual)'] - res['CONTEO ACT (Anterior)']) / res['CONTEO ACT (Anterior)']) * 100
            res.replace([float('inf'), -float('inf')], 0, inplace=True) # Manejo de división por cero
            
            # Fila de Sumatoria
            sum_act = res['CONTEO ACT (Actual)'].sum()
            sum_ant = res['CONTEO ACT (Anterior)'].sum()
            sum_var = ((sum_act - sum_ant) / sum_ant * 100) if sum_ant != 0 else 0
            
            fila_sum = pd.DataFrame([{
                'SERVICIO': 'SUMATORIA',
                'CONTEO ACT (Actual)': sum_act,
                'CONTEO ACT (Anterior)': sum_ant,
                '% Variación': sum_var
            }])
            
            return pd.concat([res, fila_sum], ignore_index=True)

        # Generar tablas
        tabla_telcel = procesar_tabla(df_act, df_pas, servicios_telcel)
        tabla_top5 = procesar_tabla(df_act, df_pas, servicios_telcel, es_top5=True)

        # Mostrar en columnas
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Análisis Servicios Telcel")
            st.dataframe(
                tabla_telcel.style.format({
                    "CONTEO ACT (Actual)": "{:,.0f}",
                    "CONTEO ACT (Anterior)": "{:,.0f}",
                    "% Variación": "{:,.2f}%"
                }).applymap(color_variacion, subset=['% Variación']),
                use_container_width=True, hide_index=True
            )

        with col2:
            st.subheader("Top 5 Otros Servicios (vs Mes Anterior)")
            st.dataframe(
                tabla_top5.style.format({
                    "CONTEO ACT (Actual)": "{:,.0f}",
                    "CONTEO ACT (Anterior)": "{:,.0f}",
                    "% Variación": "{:,.2f}%"
                }).applymap(color_variacion, subset=['% Variación']),
                use_container_width=True, hide_index=True
            )

    except Exception as e:
        st.error(f"Hubo un error al procesar los archivos. Asegúrate de que ambos tengan la columna 'SERVICIO' y 'CONTEO ACT'. Error: {e}")
else:
    st.info("Sube ambos archivos (Mes Actual y Mes Anterior) para ver la comparativa.")