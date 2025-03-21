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

def get_stop_schedule(gtfs_data, df_stop_times, route_id, direction_id):
    # Asegurarnos de que 'stop_times' tiene 'route_id' a través de 'trips'
    df_stop_times = df_stop_times.merge(gtfs_data['trips'][['trip_id', 'route_id']], on='trip_id', how='left')

    # Filtrar las paradas y horarios según ruta y dirección
    filtered = df_stop_times[(df_stop_times['route_id'] == route_id) & (df_stop_times['direction_id'] == direction_id)]

    # Ordenar por stop_sequence para obtener las paradas en orden
    filtered = filtered.sort_values(by=['stop_sequence', 'arrival_time'])

    # Obtener la primera hora de llegada para cada parada (la primera en la secuencia)
    first_arrival_times = filtered.groupby('stop_name')['arrival_time'].first().reset_index()

    # Calcular la frecuencia media de paso por cada parada
    # Primero, convertimos la hora de llegada a un objeto de tipo datetime para calcular las diferencias
    filtered['arrival_time'] = pd.to_datetime(filtered['arrival_time'], format='%H:%M:%S')

    # Calcular la diferencia de tiempo entre cada par de llegadas para cada parada
    filtered['time_diff'] = filtered.groupby('stop_name')['arrival_time'].diff().dt.total_seconds() / 60.0  # en minutos

    # Calcular la frecuencia media por parada (excluyendo el primer NaN)
    mean_frequency = filtered.groupby('stop_name')['time_diff'].mean().reset_index()
    
    # Unir las dos tablas (primera hora de llegada y frecuencia media)
    result = pd.merge(first_arrival_times, mean_frequency, on='stop_name', how='left')

    # Renombrar las columnas para mayor claridad
    result.columns = ['stop_name', 'first_arrival_time', 'average_frequency_min']

    # Devolver el DataFrame con la información solicitada
    return result

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
        # Filtrar los servicios habilitados para ese día de la semana
        calendar_filtered = gtfs_data['calendar'][gtfs_data['calendar'][weekday_column] == 1].copy()

        # Convertir las fechas en calendar.txt a formato datetime para compararlas
        calendar_filtered['start_date'] = pd.to_datetime(calendar_filtered['start_date'], format='%Y%m%d').dt.date
        calendar_filtered['end_date'] = pd.to_datetime(calendar_filtered['end_date'], format='%Y%m%d').dt.date
        
        # Filtrar solo los servicios cuya fecha seleccionada está en su rango de actividad
        calendar_filtered = calendar_filtered[
            (calendar_filtered['start_date'] <= selected_date) & 
            (calendar_filtered['end_date'] >= selected_date)
        ]

        # Filtrar las excepciones de calendar_dates que activan servicios en esa fecha
        exceptions_filtered = gtfs_data['calendar_dates'][(
            gtfs_data['calendar_dates']['date'] == selected_date.strftime('%Y%m%d')) & 
            (gtfs_data['calendar_dates']['exception_type'] == 1)
        ]

        # Si no hay servicios activos ni excepciones, no mostramos datos
        if calendar_filtered.empty and exceptions_filtered.empty:
            st.write("No hay datos disponibles para la fecha seleccionada.")
        else:
            # Obtener los IDs de servicio válidos combinando los del calendar con las excepciones
            valid_services = set(calendar_filtered['service_id']).union(set(exceptions_filtered['service_id']))

            # Filtrar los viajes de la ruta seleccionada con servicios válidos
            trips_route = gtfs_data['trips'][
                (gtfs_data['trips']['route_id'] == selected_route_id) & 
                (gtfs_data['trips']['service_id'].isin(valid_services))
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

            # Llamar a la función para obtener el DataFrame con la primera hora y la frecuencia media
            result_df_ida = get_stop_schedule(gtfs_data, stop_times_filtered, selected_route_id, 0)
            result_df_vuelta = get_stop_schedule(gtfs_data, stop_times_filtered, selected_route_id, 1)


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

            st.write("#### Dirección de ida")
            st.dataframe(df_schedule_ida)

            st.write("#### Dirección de vuelta")
            st.dataframe(df_schedule_vuelta)

            # Mostrar los resultados
            st.write(f"### Horarios y Frecuencia Media para la Ruta '{selected_route_display}' (Ida)")
            st.dataframe(result_df_ida)
            st.write(f"### Horarios y Frecuencia Media para la Ruta '{selected_route_display}' (Vuelta)")
            st.dataframe(result_df_vuelta)

    else:
        st.write("No se encontró una columna para el día seleccionado.")
