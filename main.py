import streamlit as st
from utils.gtfs_utils import load_gtfs_data, check_required_files, check_integrity
import pandas as pd

st.set_page_config("Gestor GTFS", layout="wide")

def main():
    st.title("Validación de Archivos GTFS")
    
    # Subir archivo GTFS
    uploaded_file = st.sidebar.file_uploader("Sube un archivo GTFS", type=["zip"])
    
    if uploaded_file is not None:
        # Cargar los datos del archivo GTFS
        gtfs_data = load_gtfs_data(uploaded_file)
        
        # Comprobar si los archivos requeridos están presentes
        check_required_files(gtfs_data)

        # Crear tabs para mostrar las distintas secciones
        tab1, tab2, tab3 = st.tabs(["Resumen del archivo", "Comprobación de integridad", "Datos internos"])
        def show_gtfs_tabs():
            """Muestra los tabs de la aplicación con las diferentes vistas"""
            tab = st.selectbox("Selecciona una opción", [ "Rutas / Lineas", "Paradas", "Horarios de paradas", "Calendarios"])

            if tab == "Rutas / Lineas":
                display_routes(gtfs_data)
            elif tab == "Paradas":
                display_stops(gtfs_data)
            elif tab == "Horarios de paradas":
                display_stop_times(gtfs_data)
            elif tab == "Calendarios":
                display_calendar_and_dates(gtfs_data)

        # Tab 1: Resumen del archivo
        with tab1:
            st.subheader("Resumen del archivo GTFS")
            display_summary(gtfs_data)
        
        # Tab 2: Comprobación de integridad
        with tab2:
            st.subheader("Comprobación de integridad")
            check_integrity(gtfs_data)
        
        # Tab 3: Mapa de paradas
        with tab3:
            st.subheader("Datos internos")
            show_gtfs_tabs()
             
    else:
        st.sidebar.write("Por favor, sube un archivo GTFS para comenzar.")

def display_summary(gtfs_data):
    """ Muestra un resumen básico del archivo GTFS """
    st.write("Archivos cargados:")
    for key, value in gtfs_data.items():
        st.write(f"{key}: {value.shape[0]} filas")
    
def display_map(gtfs_data):
    """ Mostrar las paradas en un mapa (pendiente de implementación) """
    st.write("Aquí se mostrarían las paradas en un mapa.")

def display_stops(gtfs_data):
    """ Muestra las paradas del GTFS como un dataframe """
    stops = gtfs_data.get("stops")
    if stops is not None:
        # Crear un espacio vacío para actualizar el dataframe
        placeholder = st.empty()

        # Mostrar la cantidad total de registros
        st.write("Total de paradas: ", stops.shape[0])

        # Limitar la visualización a las primeras 1000 filas
        displayed_data = stops.head(1000)
        
        # Mostrar los primeros resultados en el espacio vacío
        placeholder.dataframe(displayed_data)

        # Añadir un botón para mostrar más datos
        if stops.shape[0] > 1000:
            if st.button("Mostrar más paradas"):
                # Mostrar más registros, actualizando el dataframe en el mismo lugar
                placeholder.dataframe(stops)
    else:
        st.warning("No se han encontrado datos de paradas.")
    
def display_stop_times(gtfs_data):
    """ Muestra los horarios de las paradas """
    stop_times = gtfs_data.get("stop_times")
    if stop_times is not None:
        # Crear un espacio vacío para actualizar el dataframe
        placeholder = st.empty()

        # Mostrar la cantidad total de registros
        st.write("Total de registros de horarios de paradas: ", stop_times.shape[0])

        # Limitar la visualización a las primeras 1000 filas
        displayed_data = stop_times.head(1000)
        
        # Mostrar los primeros resultados en el espacio vacío
        placeholder.dataframe(displayed_data)

        # Añadir un botón para mostrar más datos
        if stop_times.shape[0] > 1000:
            if st.button("Mostrar más horarios de paradas"):
                # Mostrar más registros, actualizando el dataframe en el mismo lugar
                placeholder.dataframe(stop_times)
    else:
        st.warning("No se han encontrado datos de horarios de paradas.")

def display_calendar_and_dates(gtfs_data):
    """ Muestra los datos de calendar y calendar_dates como dataframes """
    calendar = gtfs_data.get("calendar")
    calendar_dates = gtfs_data.get("calendar_dates")
    
    # Mostrar la información de 'calendar'
    if calendar is not None:
        st.subheader("Calendario de Servicios (calendar.txt)")
        st.write("Total de registros en calendar.txt: ", calendar.shape[0])
        st.dataframe(calendar)

    else:
        st.warning("No se han encontrado datos de calendar.txt.")

    # Mostrar la información de 'calendar_dates'
    if calendar_dates is not None:
        st.subheader("Excepciones de Calendario (calendar_dates.txt)")
        st.write("Total de registros en calendar_dates.txt: ", calendar_dates.shape[0])
        st.dataframe(calendar_dates)
    
    else:
        st.warning("No se han encontrado datos de calendar_dates.txt.")

def display_routes(gtfs_data):
    """ Muestra los datos de routes como dataframe """
    routes = gtfs_data.get("routes")
    
    if routes is not None:
        st.subheader("Rutas (routes.txt)")
        st.write("Total de registros en routes.txt: ", routes.shape[0])
        st.dataframe(routes)
    else:
        st.warning("No se han encontrado datos de routes.txt.")



if __name__ == "__main__":
    main()
