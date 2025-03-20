import streamlit as st
import pandas as pd

def show_schedule_page(gtfs_data):
    st.title("Horarios de Paradas 🚏")

    # 📌 Selector de ruta con nombres combinados (short + long)
    gtfs_data['routes']['route_display'] = gtfs_data['routes'].apply(
        lambda row: f"({row['route_short_name']}) {row['route_long_name']}", axis=1
    )

    route_options = gtfs_data['routes'][['route_id', 'route_display']].drop_duplicates()
    selected_route_display = st.selectbox("Selecciona una Ruta 🚌", route_options['route_display'])

    # Obtener el route_id correspondiente
    selected_route_id = route_options[route_options['route_display'] == selected_route_display]['route_id'].iloc[0]


    # 📌 Selección de dirección
    direction_mapping = {0: "Ida", 1: "Vuelta"}
    trips_filtered = gtfs_data['trips'][gtfs_data['trips']['route_id'] == selected_route_id]
    direction_ids = trips_filtered['direction_id'].unique()

    selected_direction = st.selectbox(
        "Selecciona Dirección 🔄",
        [direction_mapping[d] for d in direction_ids]
    )

    # Convertir nombre de dirección a `direction_id`
    selected_direction_id = list(direction_mapping.keys())[
        list(direction_mapping.values()).index(selected_direction)
    ]

    # 📌 Filtrar trips por dirección
    trips_direction_filtered = trips_filtered[trips_filtered['direction_id'] == selected_direction_id]

    # 📌 Selección de parada con nombres
    stop_times_filtered = gtfs_data['stop_times'][gtfs_data['stop_times']['trip_id'].isin(trips_direction_filtered['trip_id'])]
    stop_options = gtfs_data['stops'][['stop_id', 'stop_name']].drop_duplicates()
    stops_with_names = stop_times_filtered.merge(stop_options, on='stop_id', how='left')

    selected_stop_name = st.selectbox("Selecciona una Parada 🚏", stops_with_names['stop_name'].unique())

    # Obtener el stop_id correspondiente
    selected_stop_id = stops_with_names[stops_with_names['stop_name'] == selected_stop_name]['stop_id'].iloc[0]

    # 📌 Mostrar los horarios de la parada seleccionada
    show_stop_times(gtfs_data, selected_route_id, selected_direction_id, selected_stop_id, selected_stop_name)

def show_stop_times(gtfs_data, route_id, direction_id, stop_id, stop_name):
    # Unir stop_times con trips para obtener el route_id y ordenar por trip_id y stop_sequence
    stop_times_with_routes = gtfs_data['stop_times'].merge(
        gtfs_data['trips'][['trip_id', 'route_id', 'direction_id']],
        on='trip_id',
        how='left'
    )

    # Filtrar los datos por ruta, dirección y parada seleccionadas
    stop_times_filtered = stop_times_with_routes[
        (stop_times_with_routes['route_id'] == route_id) & 
        (stop_times_with_routes['direction_id'] == direction_id) & 
        (stop_times_with_routes['stop_id'] == stop_id)
    ].sort_values(by=['trip_id', 'stop_sequence', 'arrival_time'])

    # Mostrar los horarios con orden correcto
    st.write(f"📍 Horarios para la parada {stop_name} ({stop_id}) en la ruta {route_id} ({direction_id})")
    st.dataframe(stop_times_filtered[['trip_id', 'stop_sequence', 'arrival_time', 'departure_time']])


