import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static



def normalize_gtfs_time(time_str):
    """Corrige los horarios en formato GTFS que superan las 24:00:00."""
    hours, minutes, seconds = map(int, time_str.split(":"))
    
    if hours >= 24:
        hours -= 24  # Restar 24 horas para normalizarlo a una hora del día siguiente
    
    # En caso de que la hora sea 24, la ajustamos a 00.
    if hours == 24:
        hours = 0
    
    return f"{hours:02}:{minutes:02}:{seconds:02}"

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

def get_stop_schedule(gtfs_data, stop_times_filtered, route_id, direction_id):
    # Filtrar por dirección
    stop_times_filtered = stop_times_filtered[stop_times_filtered['direction_id'] == direction_id]
    
    # Agrupar por paradas
    stops_schedule = []
    for stop_id, group in stop_times_filtered.groupby('stop_id'):
        group = group.sort_values(by='departure_time')
        
        # Obtener los horarios ordenados
        # departure_times = group['departure_time'].tolist()

        # Normalizar horarios antes de procesarlos

        departure_times = [normalize_gtfs_time(t) for t in group['departure_time']]
        # Calcular diferencias entre horarios sucesivos
        time_diffs = pd.to_datetime(departure_times, format='%H:%M:%S').diff().dropna()
        time_diffs_minutes = time_diffs.total_seconds() / 60  # Convertir a minutos
        
        # Media de la frecuencia
        avg_frequency = pd.Series(time_diffs_minutes).mean() if not time_diffs_minutes.empty else None
        
        # Guardar los datos en la lista
        stops_schedule.append({
            'stop_name': group['stop_name'].iloc[0],
            'departure_times': ', '.join(departure_times),
            'time_diffs': ', '.join(time_diffs_minutes.astype(str)) if not time_diffs_minutes.empty else '-',
            'avg_frequency (min)': round(avg_frequency, 2) if avg_frequency is not None else '-'
        })
    
    # Convertir a DataFrame y devolverlo
    return pd.DataFrame(stops_schedule)


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
    selected_date = st.date_input("Selecciona una fecha", pd.to_datetime("today"), key="date_input", format="DD/MM/YYYY")
    
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
            # df_schedule_ida['departure_time'] = pd.to_datetime(normalize_gtfs_time(df_schedule_ida['departure_time']), format='%H:%M:%S').dt.strftime('%H:%M')
            # df_schedule_vuelta['departure_time'] = pd.to_datetime(normalize_gtfs_time(df_schedule_vuelta['departure_time']), format='%H:%M:%S').dt.strftime('%H:%M')

            # Aplicar la normalización a los tiempos
            df_schedule_ida['departure_time'] = df_schedule_ida['departure_time'].astype(str).apply(normalize_gtfs_time)
            df_schedule_ida['departure_time'] = pd.to_datetime(df_schedule_ida['departure_time'], format='%H:%M:%S').dt.strftime('%H:%M')

            df_schedule_vuelta['departure_time'] = df_schedule_vuelta['departure_time'].astype(str).apply(normalize_gtfs_time)
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

def show_routes_per_stop(gtfs_data):
    stop_times = gtfs_data['stop_times']
    trips = gtfs_data['trips']
    routes = gtfs_data['routes']
    stops = gtfs_data['stops']
    shapes = gtfs_data['shapes']

    # Unir stop_times con trips para obtener el route_id y direction_id
    stop_routes = stop_times.merge(trips[['trip_id', 'route_id', 'direction_id']], on='trip_id', how='left')

    # Agrupar por stop_id, route_id y direction_id
    stop_routes_count = stop_routes.groupby(['stop_id', 'route_id', 'direction_id']).size().reset_index(name='frequency')

    # Unir con nombres de paradas y rutas
    stops_with_routes = stop_routes_count.merge(stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']], on='stop_id', how='left')
    stops_with_routes = stops_with_routes.merge(routes[['route_id', 'route_short_name', 'route_color']], on='route_id', how='left')

    # Interfaz en Streamlit
    st.subheader("Consulta de líneas por parada")

    # 🔍 Buscador de paradas
    search_query = st.text_input("Buscar parada por nombre:")
    filtered_stops = stops_with_routes['stop_name'].unique()

    if search_query:
        filtered_stops = [stop for stop in filtered_stops if search_query.lower() in stop.lower()]

    # Selector de parada
    selected_stop_name = st.selectbox("Selecciona una parada:", filtered_stops)

    # Filtrar datos por la parada seleccionada
    selected_stop_data = stops_with_routes[stops_with_routes['stop_name'] == selected_stop_name]

    if not selected_stop_data.empty:
        st.write(f"### Parada: {selected_stop_name}")
        route_legends = []  # Lista para almacenar las leyendas de las rutas
        # Agrupar por dirección de la ruta
        directions = {0: ("🚀➡️ Ida", "blue"), 1: ("🔄⬅️ Vuelta", "red")}

        for direction_id, (direction_label, color) in directions.items():
            direction_data = selected_stop_data[selected_stop_data['direction_id'] == direction_id]

            if not direction_data.empty:
                st.markdown(f"### <span style='color:{color};'>{direction_label}</span>", unsafe_allow_html=True)

                # Ordenar por frecuencia
                direction_data = direction_data.sort_values(by='frequency', ascending=False)

                for _, row in direction_data.iterrows():
                    st.markdown(f"🚍 <span style='color:{color};'>**Línea {row['route_short_name']}**</span> - {row['frequency']} pasadas/día", unsafe_allow_html=True)

                    # ⏰ Obtener horarios únicos por ruta
                    trip_ids = trips[(trips['route_id'] == row['route_id']) & (trips['direction_id'] == direction_id)]['trip_id']
                    route_times = stop_times[(stop_times['stop_id'] == row['stop_id']) & (stop_times['trip_id'].isin(trip_ids))]

                    # Extraer y ordenar horarios únicos
                    unique_times = sorted(route_times['departure_time'].unique())

                    # Mostrar horarios limpios
                    st.markdown(f"⏳ <span style='color:{color};'>**Horarios:**</span> {', '.join(unique_times)}", unsafe_allow_html=True)
        
        # Crear un mapa centrado en la parada seleccionada
        m = folium.Map(location=[selected_stop_data['stop_lat'].iloc[0], selected_stop_data['stop_lon'].iloc[0]], zoom_start=15)

        # Añadir marcador para la parada
        folium.Marker(
            location=[selected_stop_data['stop_lat'].iloc[0], selected_stop_data['stop_lon'].iloc[0]],
            popup=f"<strong>{selected_stop_name}</strong>",
            icon=folium.Icon(color="green", icon="info-sign")
        ).add_to(m)

        # Mostrar las rutas asociadas a la parada seleccionada
        selected_routes = selected_stop_data['route_id'].unique()

        # Filtrar los shapes de las rutas seleccionadas
        for route_id in selected_routes:
            # Obtener el nombre y color de la línea
            route_name = selected_stop_data[selected_stop_data['route_id'] == route_id]['route_short_name'].iloc[0]
            route_color = selected_stop_data[selected_stop_data['route_id'] == route_id]['route_color'].iloc[0]  # Usar el color de la ruta

            # Asegurarse de que el color esté en formato válido (agregar '#' si es necesario)
            if not route_color.startswith('#'):
                route_color = '#' + route_color  # Agregar el '#' al inicio del color hexadecimal
            
            
            # Filtrar los shapes para esta ruta
            route_shapes = shapes[shapes['shape_id'].isin(trips[trips['route_id'] == route_id]['shape_id'])]

            # Convertir las coordenadas de los shapes en una lista de latitudes y longitudes
            route_coordinates = route_shapes[['shape_pt_lat', 'shape_pt_lon']].values.tolist()

            # Dibujar la línea de la ruta en el mapa usando el color de la ruta
            folium.PolyLine(route_coordinates, color=route_color, weight=2.5, opacity=1).add_to(m)

            # Agregar leyenda para la línea
            route_legends.append(f"<div style='color:{route_color};'>Línea {route_name}</div>")

        # Mostrar las leyendas al lado del mapa
        if route_legends:
            st.markdown("<div style='font-size: 14px; font-weight: bold;'>Leyenda de rutas:</div>", unsafe_allow_html=True)
            for legend in route_legends:
                st.markdown(legend, unsafe_allow_html=True)

        # Mostrar el mapa con las rutas y la parada
        st.subheader("Mapa de rutas y parada")
        folium_static(m, 2000, 600)
    else:
        st.write("No hay rutas registradas para esta parada.")
