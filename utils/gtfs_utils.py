import streamlit as st
import gtfs_kit as gk
import pandas as pd
import tempfile
import os

def load_gtfs_data(file, dist_units="km"):
    """Carga el archivo GTFS usando gtfs_kit y devuelve un diccionario de DataFrames."""
    # Crear un archivo temporal para guardar el contenido del archivo subido
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_file_path = tmp_file.name
    
    # Cargar el archivo GTFS con gtfs_kit, pasando dist_units
    feed = gk.read_feed(tmp_file_path, dist_units=dist_units)
    
    # Convertir a DataFrames
    stops = feed.stops
    routes = feed.routes
    trips = feed.trips
    stop_times = feed.stop_times
    calendar = feed.calendar
    calendar_dates = feed.calendar_dates
    
    # Eliminar el archivo temporal después de usarlo
    os.remove(tmp_file_path)
    
    # Devolver los DataFrames en un diccionario
    return {
        "stops": stops,
        "routes": routes,
        "trips": trips,
        "stop_times": stop_times,
        "calendar": calendar,
        "calendar_dates": calendar_dates
    }

def check_required_files(gtfs_data):
    """Verifica si los archivos requeridos están presentes."""
    required_files = ["routes", "stops", "trips", "stop_times", "calendar", "calendar_dates"]
    missing_files = [file for file in required_files if file not in gtfs_data]
    
    if missing_files:
        st.warning(f"Faltan los siguientes archivos en el GTFS: {', '.join(missing_files)}")
    else:
        st.success("Todos los archivos necesarios están presentes.")

def check_integrity(gtfs_data):
    """Verifica la integridad de los datos GTFS."""
    stop_times = gtfs_data["stop_times"]
    stops = gtfs_data["stops"]
    
    # Verificar que todos los stop_id en stop_times existan en stops
    missing_stops = stop_times[~stop_times['stop_id'].isin(stops['stop_id'])]
    
    if not missing_stops.empty:
        st.warning(f"Se encontraron paradas faltantes en stop_times: {missing_stops}")
    else:
        st.success("La integridad de los datos es correcta.")
