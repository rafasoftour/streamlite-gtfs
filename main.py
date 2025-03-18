import streamlit as st
from tab_cargar import cargar_gtfs
from tab_lineas import mostrar_lineas
from tab_paradas import mostrar_paradas
from tab_mostrar_horarios import mostrar_horarios

# Configurar la página en "wide mode"
st.set_page_config(page_title="Test Gtfs", layout="wide")

st.title("Procesador de archivos GTFS")

tab1, tab2, tab3, tab4 = st.tabs(["📂 Cargar GTFS", "🚍 Líneas", "📍 Paradas", "⏰ Mostrar horarios"])

with tab1:
    cargar_gtfs()

if "feed" in st.session_state:
    with tab2:
        mostrar_lineas()
    with tab3:
        mostrar_paradas()
    with tab4:
        mostrar_horarios()
