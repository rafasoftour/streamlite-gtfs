import streamlit as st
import pandas as pd

def show_schedule_page(gtfs_data):
    # 📌 Selector de ruta con nombres combinados (short + long)
    gtfs_data['routes']['route_display'] = gtfs_data['routes'].apply(
        lambda row: f"({row['route_short_name']}) {row['route_long_name']}", axis=1
    )

    route_options = gtfs_data['routes'][['route_id', 'route_display']].drop_duplicates()
    selected_route_display = st.selectbox("Selecciona una Ruta 🚌", route_options['route_display'])

    # Obtener el route_id correspondiente
    selected_route_id = route_options[route_options['route_display'] == selected_route_display]['route_id'].iloc[0]

    # Filtrar trips para la ruta seleccionada
    trips_filtered = gtfs_data['trips'][gtfs_data['trips']['route_id'] == selected_route_id]

    # Selección de dirección y parada en la misma línea
    col1, col2 = st.columns(2)

    with col1:
        direction_ids = trips_filtered['direction_id'].unique()
        direction_mapping = {0: "Ida", 1: "Vuelta"}
        selected_direction = st.selectbox("Selecciona Dirección 🔄", direction_ids, format_func=lambda x: direction_mapping[x])

    # Filtrar trips por dirección
    trips_direction_filtered = trips_filtered[trips_filtered['direction_id'] == selected_direction]

    with col2:
        stop_options = gtfs_data['stops'][gtfs_data['stops']['stop_id'].isin(
            gtfs_data['stop_times'][gtfs_data['stop_times']['trip_id'].isin(trips_direction_filtered['trip_id'])]['stop_id'].unique()
        )][['stop_id', 'stop_name']].drop_duplicates()
        
        selected_stop_name = st.selectbox("Selecciona una Parada 🚏", stop_options['stop_name'])
        selected_stop_id = stop_options[stop_options['stop_name'] == selected_stop_name]['stop_id'].iloc[0]

    # Mostrar los horarios de la parada seleccionada
    show_stop_times(gtfs_data, selected_route_id, selected_direction, selected_stop_id, selected_stop_name)

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


def show_schedule_page2(gtfs_data):
    # Asegurarse de que la columna route_display se haya creado antes de usarla
    gtfs_data['routes']['route_display'] = gtfs_data['routes'].apply(
        lambda row: f"({row['route_short_name']}) {row['route_long_name']}", axis=1
    )
    
    # Selección de la ruta
    route_options = gtfs_data['routes'][['route_id', 'route_display']].drop_duplicates()
    selected_route_display = st.selectbox("Selecciona una Ruta 🚌", route_options['route_display'], key="r1")
    selected_route_id = route_options[route_options['route_display'] == selected_route_display]['route_id'].iloc[0]

    # Selección de la fecha con formato español (DD/MM/YYYY)
    selected_date = st.date_input("Selecciona una Fecha", pd.to_datetime("today"), key="date_input", format="DD/MM/YYYY")
    
    # Obtener los días de la semana de la fecha seleccionada (lunes=0, domingo=6)
    selected_day_of_week = selected_date.weekday()

    # Mapeo de días de la semana a las columnas correctas en el archivo calendar
    weekday_columns = {
        0: 'monday',
        1: 'tuesday',
        2: 'wednesday',
        3: 'thursday',
        4: 'friday',
        5: 'saturday',
        6: 'sunday'
    }

    # Verificar si el día seleccionado tiene una columna correspondiente
    weekday_column = weekday_columns.get(selected_day_of_week)
    
    if weekday_column:
        # Filtrar los servicios habilitados para ese día
        calendar_filtered = gtfs_data['calendar'][gtfs_data['calendar'][weekday_column] == 1]
        
        # Filtrar las excepciones (calendar_dates)
        exceptions_filtered = gtfs_data['calendar_dates'][(
            gtfs_data['calendar_dates']['date'] == selected_date.strftime('%Y%m%d')) & 
            (gtfs_data['calendar_dates']['exception_type'] == 1)
        ]

        # Filtrar los trips que están habilitados en el día seleccionado
        trips_route = gtfs_data['trips'][(
            gtfs_data['trips']['route_id'] == selected_route_id) & 
            (gtfs_data['trips']['service_id'].isin(calendar_filtered['service_id'])) | 
            (gtfs_data['trips']['service_id'].isin(exceptions_filtered['service_id']))
        ]

        # Filtrar las paradas y horarios para esos trips
        stop_times_filtered = gtfs_data['stop_times'][gtfs_data['stop_times']['trip_id'].isin(trips_route['trip_id'])]

        # Unir con los datos de las paradas (nombre y ubicación)
        stop_times_filtered = stop_times_filtered.merge(
            gtfs_data['stops'][['stop_id', 'stop_name', 'stop_lat', 'stop_lon']],
            on='stop_id', how='left'
        )

        # Unir con los trips para obtener el trip_id y otros detalles
        stop_times_filtered = stop_times_filtered.merge(
            trips_route[['trip_id', 'trip_headsign', 'direction_id']],
            on='trip_id', how='left'
        )

        # Filtrar por dirección (ida o vuelta)
        ida_filtered = stop_times_filtered[stop_times_filtered['direction_id'] == 0]
        vuelta_filtered = stop_times_filtered[stop_times_filtered['direction_id'] == 1]

        # Ordenar por stop_sequence para asegurar que las paradas estén en el orden correcto dentro de la ruta
        ida_filtered = ida_filtered.sort_values(by=['stop_sequence', 'departure_time'])
        vuelta_filtered = vuelta_filtered.sort_values(by=['stop_sequence', 'departure_time'])

        # Mostrar los horarios y los detalles de los trips en un DataFrame
        st.write(f"### Horarios de la Ruta '{selected_route_display}' para el {selected_date.strftime('%d/%m/%Y')}")

        # Crear los DataFrames con las columnas que queremos mostrar (ida)
        df_schedule_ida = ida_filtered[['stop_name', 'trip_headsign', 'departure_time', 'trip_id', 'direction_id', 'stop_sequence']]
        df_schedule_vuelta = vuelta_filtered[['stop_name', 'trip_headsign', 'departure_time', 'trip_id', 'direction_id', 'stop_sequence']]

        # Convertir el horario de llegada y salida al formato deseado (solo mostrar la hora sin fecha)
        df_schedule_ida['departure_time'] = pd.to_datetime(df_schedule_ida['departure_time'], format='%H:%M:%S').dt.strftime('%H:%M')
        df_schedule_vuelta['departure_time'] = pd.to_datetime(df_schedule_vuelta['departure_time'], format='%H:%M:%S').dt.strftime('%H:%M')

        # # Repetir el nombre de la parada y agregar trip_id y departure_time para que se vea la frecuencia
        # df_schedule_ida = df_schedule_ida.groupby(['stop_name', 'trip_headsign', 'trip_id'], as_index=False).agg({
        #     'departure_time': ', '.join
        # })

        # df_schedule_vuelta = df_schedule_vuelta.groupby(['stop_name', 'trip_headsign', 'trip_id'], as_index=False).agg({
        #     'departure_time': ', '.join
        # })

        # # Ordenar por stop_sequence para cada trip, para asegurar que el orden es el correcto
        # df_schedule_ida['stop_name'] = pd.Categorical(df_schedule_ida['stop_name'], categories=sorted(df_schedule_ida['stop_name'].unique(), key=lambda x: stop_times_filtered[stop_times_filtered['stop_name'] == x]['stop_sequence'].iloc[0]))
        # df_schedule_vuelta['stop_name'] = pd.Categorical(df_schedule_vuelta['stop_name'], categories=sorted(df_schedule_vuelta['stop_name'].unique(), key=lambda x: stop_times_filtered[stop_times_filtered['stop_name'] == x]['stop_sequence'].iloc[0]))

        # Mostrar los DataFrames con Streamlit
        st.write("#### Ida (0:00 - Dirección de ida)")
        st.dataframe(df_schedule_ida)

        st.write("#### Vuelta (1:00 - Dirección de vuelta)")
        st.dataframe(df_schedule_vuelta)

    else:
        st.write("No se encontró una columna para el día seleccionado.")
