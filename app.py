import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Dashboard Comparativo", layout="wide")
st.title("Reporte de Transacciones e Importes")

def cargar_datos(archivo):
    if archivo is None:
        return None
    try:
        contenido = archivo.getvalue()
        # Probamos combinaciones de codificacion y delimitadores
        for enc in ['utf-8', 'latin1', 'cp1252']:
            try:
                if archivo.name.endswith('.csv'):
                    # sep=None con engine='python' detecta si es coma, punto y coma o tabulador
                    df = pd.read_csv(io.BytesIO(contenido), encoding=enc, sep=None, engine='python')
                else:
                    df = pd.read_excel(archivo)
                
                # Normalizar: quitar espacios y convertir nombres de columnas a MAYUSCULAS
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                # Si encontramos la columna clave, devolvemos el dataframe
                if 'SERVICIO' in df.columns:
                    return df
            except:
                continue
        return df # Devolvemos lo que se haya podido cargar para inspeccionar columnas
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

    # --- VALIDACION DE COLUMNAS ---
    cols_necesarias = ['SERVICIO', 'CONTEO ACT', 'IMPORTE ACT']
    error_columnas = False

    for nombre, df in [("ACTUAL", df_act), ("ANTERIOR", df_ant)]:
        if df is not None:
            faltantes = [c for c in cols_necesarias if c not in df.columns]
            if faltantes:
                st.error(f"⚠️ Error en el archivo {nombre}: Faltan las columnas: {', '.join(faltantes)}")
                st.write(f"Columnas detectadas en {nombre}:", list(df.columns))
                error_columnas = True
        else:
            st.error(f"No se pudo procesar el archivo {nombre}.")
            error_columnas = True

    if not error_columnas:
        try:
            # Lista de servicios Telcel
            telcel_list = [
                'TELCEL PAQUETES', 'TELCEL FACTURA', 'TELCEL VENTA DE TIEMPO AIRE', 
                'AMIGO PAGUITOS', 'TELCEL PAQUETES MIXTOS', 'TELCEL PAQUETES POSPAGO'
            ]

            def procesar(df_a, df_p, filtro, es_top=False):
                # Asegurar que la columna servicio sea texto y mayusculas
                df_a['SERVICIO'] = df_a['SERVICIO'].astype(str).str.strip().str.upper()
                df_p['SERVICIO'] = df_p['SERVICIO'].astype(str).str.strip().str.upper()

                if not es_top:
                    a = df_a[df_a['SERVICIO'].isin(filtro)].copy()
                else:
                    otros = df_a[~df_a['SERVICIO'].isin(filtro)]
                    top5_names = otros.sort_values('CONTEO ACT', ascending=False).head(5)['SERVICIO']
                    a = df_a[df_a['SERVICIO'].isin(top5_names)].copy()

                cols = ['SERVICIO', 'CONTEO ACT', 'IMPORTE ACT']
                res = pd.merge(a[cols], df_p[cols], on='SERVICIO', how='left', suffixes=('_ACT', '_ANT')).fillna(0)

                # Calculos de variacion
                for col in ['CONTEO ACT', 'IMPORTE ACT']:
                    res[f'VAR % {col.split()[0]}'] = 0.0
                    ant, act = f'{col}_ANT', f'{col}_ACT'
                    mask = res[ant] != 0
                    res.loc[mask, f'VAR % {col.split()[0]}'] = ((res[act] - res[ant]) / res[ant]) * 100
                
                # Fila Sumatoria
                s_c_act, s_c_ant = res['CONTEO ACT_ACT'].sum(), res['CONTEO ACT_ANT'].sum()
                s_i_act, s_i_ant = res['IMPORTE ACT_ACT'].sum(), res['IMPORTE ACT_ANT'].sum()
                
                fila_sum = pd.DataFrame([{
                    'SERVICIO': 'SUMATORIA',
                    'CONTEO ACT_ACT': s_c_act, 'CONTEO ACT_ANT': s_c_ant,
                    'VAR % CONTEO': 0 if s_c_ant == 0 else ((s_c_act - s_c_ant) / s_c_ant) * 100,
                    'IMPORTE ACT_ACT': s_i_act, 'IMPORTE ACT_ANT': s_i_ant,
                    'VAR % IMPORTE': 0 if s_i_ant == 0 else ((s_i_act - s_i_ant) / s_i_ant) * 100
                }])
                return pd.concat([res, fila_sum], ignore_index=True)

            t1 = procesar(df_act, df_ant, telcel_list)
            t2 = procesar(df_act, df_ant, telcel_list, es_top=True)

            # Orden final de columnas
            orden = ['SERVICIO', 'CONTEO ACT_ACT', 'CONTEO ACT_ANT', 'VAR % CONTEO', 'IMPORTE ACT_ACT', 'IMPORTE ACT_ANT', 'VAR % IMPORTE']
            
            def formato(df):
                return df[orden].style.format({
                    'CONTEO ACT_ACT': '{:,.0f}', 'CONTEO ACT_ANT': '{:,.0f}', 'VAR % CONTEO': '{:,.2f}%',
                    'IMPORTE ACT_ACT': '${:,.2f}', 'IMPORTE ACT_ANT': '${:,.2f}', 'VAR % IMPORTE': '{:,.2f}%'
                }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', 
                          subset=['VAR % CONTEO', 'VAR % IMPORTE'])

            st.subheader("Análisis de Servicios Telcel")
            st.table(formato(t1))
            st.write("---")
            st.subheader("Top 5 Otros Servicios")
            st.table(formato(t2))

        except Exception as e:
            st.error(f"Error en el proceso: {e}")
else:
    st.info("Sube ambos archivos para comparar.")
