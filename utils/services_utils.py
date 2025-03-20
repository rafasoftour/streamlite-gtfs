import streamlit as st
import pandas as pd

def show_services_page(gtfs_data):
    st.header("🗓️ Información de Servicios")

    # 📌 Selector de ruta con nombres combinados (short + long)
    gtfs_data['routes']['route_display'] = gtfs_data['routes'].apply(
        lambda row: f"({row['route_short_name']}) {row['route_long_name']}", axis=1
    )

    route_options = gtfs_data['routes'][['route_id', 'route_display']].drop_duplicates()
    selected_route_display = st.selectbox("Selecciona una Ruta 🚌", route_options['route_display'])

    # Obtener el route_id correspondiente
    selected_route_id = route_options[route_options['route_display'] == selected_route_display]['route_id'].iloc[0]

    # 📌 Filtrar trips para obtener los service_id de la ruta
    service_ids = gtfs_data['trips'][gtfs_data['trips']['route_id'] == selected_route_id]['service_id'].unique()

    # 📌 Mostrar los servicios en una tabla
    st.subheader("Servicios Disponibles")
    service_info = gtfs_data['calendar'][gtfs_data['calendar']['service_id'].isin(service_ids)]
    
    if not service_info.empty:
        # Traducir los días a etiquetas más amigables
        day_labels = {
            'monday': "Lun", 'tuesday': "Mar", 'wednesday': "Mié",
            'thursday': "Jue", 'friday': "Vie", 'saturday': "Sáb", 'sunday': "Dom"
        }
        
        # Crear una columna con los días en los que opera el servicio
        service_info['Días Operativos'] = service_info.apply(
            lambda row: ", ".join([label for key, label in day_labels.items() if row[key] == 1]), axis=1
        )

        st.dataframe(service_info[['service_id', 'start_date', 'end_date', 'Días Operativos']])

    else:
        st.write("No hay información de servicios en `calendar`. Verificando `calendar_dates`...")

    # 📌 Verificar excepciones en calendar_dates
    exceptions_info = gtfs_data['calendar_dates'][gtfs_data['calendar_dates']['service_id'].isin(service_ids)]
    
    if not exceptions_info.empty:
        st.subheader("📅 Excepciones de Servicio")
        exceptions_info['exception_type'] = exceptions_info['exception_type'].map({1: "Añadido", 2: "Eliminado"})
        st.dataframe(exceptions_info[['service_id', 'date', 'exception_type']])
    else:
        st.write("No hay excepciones en `calendar_dates`.")

