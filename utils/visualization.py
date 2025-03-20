import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

def display_stops(gtfs_data):
    """ Muestra las paradas del GTFS como un dataframe """
    st.title("Información de las paradas en fichero")
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

def display_calendar_and_dates(gtfs_data):
    """ Muestra los datos de calendar y calendar_dates como dataframes """
    st.title("Información de calendarios en fichero")
    calendar = gtfs_data.get("calendar")
    calendar_dates = gtfs_data.get("calendar_dates")
    
    # Mostrar la información de 'calendar'
    if calendar is not None:
        st.subheader("Calendario de Servicios")
        st.write("Total de registros en calendar.txt: ", calendar.shape[0])
        st.dataframe(calendar)

    else:
        st.warning("No se han encontrado datos de calendar.txt.")

    # Mostrar la información de 'calendar_dates'
    if calendar_dates is not None:
        st.subheader("Excepciones de Calendario")
        st.write("Total de registros en calendar_dates.txt: ", calendar_dates.shape[0])
        st.dataframe(calendar_dates)
    
    else:
        st.warning("No se han encontrado datos de calendar_dates.txt.")

def display_routes(gtfs_data):
    """ Muestra los datos de routes como dataframe """
    st.title("Rutas / Lineas en fichero")
    routes = gtfs_data.get("routes")
    
    if routes is not None:
        st.write("Total de registros en routes.txt: ", routes.shape[0])
        st.dataframe(routes)
    else:
        st.warning("No se han encontrado datos de routes.txt.")

def display_route_map(gtfs_data, route_id):
    """Muestra el mapa con la ruta y las paradas correspondientes"""

    trips = gtfs_data.get("trips")
    shapes = gtfs_data.get("shapes")
    stops = gtfs_data.get("stops")
    stop_times = gtfs_data.get("stop_times")

    if trips is None or trips.empty or shapes is None or shapes.empty or stops is None or stops.empty or stop_times is None or stop_times.empty:
        st.warning("No hay datos suficientes para mostrar la ruta con paradas.")
        return

    # 🔹 Obtener el `shape_id` correspondiente a la `route_id`
    shape_ids = trips.loc[trips["route_id"] == route_id, "shape_id"].unique()

    if len(shape_ids) == 0:
        st.warning("No se encontraron shapes para esta ruta.")
        return

    shape_id = shape_ids[0]  # Tomamos el primer shape_id disponible

    # 🔹 Filtrar los puntos del shape correspondiente
    shape_points = shapes[shapes["shape_id"] == shape_id].sort_values("shape_pt_sequence")

    if shape_points.empty:
        st.warning("No se encontraron coordenadas para la ruta seleccionada.")
        return

    # 🔹 Crear el mapa centrado en el primer punto del shape
    first_point = [shape_points.iloc[0]["shape_pt_lat"], shape_points.iloc[0]["shape_pt_lon"]]
    route_map = folium.Map(location=first_point, zoom_start=12)

    # 🔹 Dibujar la ruta en el mapa
    route_coords = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))
    folium.PolyLine(route_coords, color="blue", weight=4.5, opacity=0.8).add_to(route_map)

    # 🔹 Obtener los `stop_id` correspondientes a los `trip_id` de la ruta
    trip_ids = trips.loc[trips["route_id"] == route_id, "trip_id"].unique()
    stop_ids = stop_times.loc[stop_times["trip_id"].isin(trip_ids), "stop_id"].unique()

    # 🔹 Filtrar las paradas correspondientes
    stops_on_route = stops[stops["stop_id"].isin(stop_ids)]

    # 🔹 Agregar las paradas al mapa
    for _, stop in stops_on_route.iterrows():
        folium.Marker(
            location=[stop["stop_lat"], stop["stop_lon"]],
            popup=f"{stop['stop_name']} ({stop['stop_id']})",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(route_map)

    # 🔹 Mostrar el mapa en Streamlit
    folium_static(route_map, width=2000, height=600)

def display_route_directions(gtfs_data, route_id):
    """Muestra las paradas organizadas por dirección para una ruta específica"""

    trips = gtfs_data.get("trips")
    stop_times = gtfs_data.get("stop_times")
    stops = gtfs_data.get("stops")

    if trips is None or trips.empty or stop_times is None or stop_times.empty or stops is None or stops.empty:
        st.warning("No hay datos suficientes para mostrar las paradas por dirección.")
        return

    # 🔹 Obtener los trips de la ruta especificada
    trips_filtered = trips[trips["route_id"] == route_id]
    if trips_filtered.empty:
        st.warning("No se encontraron viajes para esta ruta.")
        return

    # 🔹 Filtrar los viajes según la dirección (0 = ida, 1 = vuelta)
    ida_trips = trips_filtered[trips_filtered["direction_id"] == 0]
    vuelta_trips = trips_filtered[trips_filtered["direction_id"] == 1]

    # 🔹 Obtener las paradas de ida y vuelta
    ida_stop_ids = stop_times[stop_times["trip_id"].isin(ida_trips["trip_id"])]["stop_id"].unique()
    vuelta_stop_ids = stop_times[stop_times["trip_id"].isin(vuelta_trips["trip_id"])]["stop_id"].unique()

    ida_stop_times = stop_times[stop_times["stop_id"].isin(ida_stop_ids)].sort_values("stop_sequence")
    vuelta_stop_times = stop_times[stop_times["stop_id"].isin(vuelta_stop_ids)].sort_values("stop_sequence")

    if ida_stop_times.empty or vuelta_stop_times.empty:
        st.warning("No se encontraron paradas para una de las direcciones.")
        return

    # 🔹 Obtener los detalles de las paradas (names, etc.) a partir de 'stops'
    ida_stops = stops[stops["stop_id"].isin(ida_stop_times["stop_id"])]
    vuelta_stops = stops[stops["stop_id"].isin(vuelta_stop_times["stop_id"])]

    if ida_stops.empty or vuelta_stops.empty:
        st.warning("No se encontraron paradas para una de las direcciones.")
        return

    # 🔹 Mostrar las paradas en dos columnas: ida y vuelta
    col1, col2 = st.columns(2)

    with col1:
        st.header("Dirección: Ida")
        for _, stop in ida_stops.iterrows():
            st.write(f"• {stop['stop_name']}")

    with col2:
        st.header("Dirección: Vuelta")
        for _, stop in vuelta_stops.iterrows():
            st.write(f"• {stop['stop_name']}")

def display_route_directions_map(gtfs_data, route_id):
    """Muestra un mapa para las paradas de ida y vuelta de una ruta específica"""

    trips = gtfs_data.get("trips")
    stop_times = gtfs_data.get("stop_times")
    stops = gtfs_data.get("stops")

    if trips is None or trips.empty or stop_times is None or stop_times.empty or stops is None or stops.empty:
        st.warning("No hay datos suficientes para mostrar las paradas por dirección.")
        return

    # 🔹 Obtener los trips de la ruta especificada
    trips_filtered = trips[trips["route_id"] == route_id]
    if trips_filtered.empty:
        st.warning("No se encontraron viajes para esta ruta.")
        return

    # 🔹 Filtrar los viajes según la dirección (0 = ida, 1 = vuelta)
    ida_trips = trips_filtered[trips_filtered["direction_id"] == 0]
    vuelta_trips = trips_filtered[trips_filtered["direction_id"] == 1]

    # 🔹 Obtener las paradas de ida y vuelta
    ida_stop_ids = stop_times[stop_times["trip_id"].isin(ida_trips["trip_id"])]["stop_id"].unique()
    vuelta_stop_ids = stop_times[stop_times["trip_id"].isin(vuelta_trips["trip_id"])]["stop_id"].unique()

    # 🔹 Obtener las paradas y las coordenadas
    ida_stops = stops[stops["stop_id"].isin(ida_stop_ids)]
    vuelta_stops = stops[stops["stop_id"].isin(vuelta_stop_ids)]

    # 🔹 Crear un mapa para la ida
    ida_map = folium.Map(location=[ida_stops["stop_lat"].mean(), ida_stops["stop_lon"].mean()], zoom_start=13)
    ida_marker_cluster = MarkerCluster().add_to(ida_map)

    # Añadir paradas al mapa de ida
    for _, stop in ida_stops.iterrows():
        folium.Marker(
            location=[stop["stop_lat"], stop["stop_lon"]],
            popup=stop["stop_name"]
        ).add_to(ida_marker_cluster)

    # 🔹 Crear un mapa para la vuelta
    vuelta_map = folium.Map(location=[vuelta_stops["stop_lat"].mean(), vuelta_stops["stop_lon"].mean()], zoom_start=13)
    vuelta_marker_cluster = MarkerCluster().add_to(vuelta_map)

    # Añadir paradas al mapa de vuelta
    for _, stop in vuelta_stops.iterrows():
        folium.Marker(
            location=[stop["stop_lat"], stop["stop_lon"]],
            popup=stop["stop_name"]
        ).add_to(vuelta_marker_cluster)

    # 🔹 Mostrar los mapas en Streamlit
    st.subheader("Mapa de paradas - Dirección: Ida")
    folium_static(ida_map, width=2000, height=600)

    st.subheader("Mapa de paradas - Dirección: Vuelta")
    folium_static(vuelta_map, width=2000, height=600)

def display_route_directions_with_shapes(gtfs_data, route_id):
    """Muestra un mapa para las paradas y shapes de ida y vuelta de una ruta específica"""

    trips = gtfs_data.get("trips")
    stop_times = gtfs_data.get("stop_times")
    stops = gtfs_data.get("stops")
    shapes = gtfs_data.get("shapes")

    if trips is None or trips.empty or stop_times is None or stop_times.empty or stops is None or stops.empty or shapes is None or shapes.empty:
        st.warning("No hay datos suficientes para mostrar las paradas y shapes por dirección.")
        return

    # 🔹 Obtener los trips de la ruta especificada
    trips_filtered = trips[trips["route_id"] == route_id]
    if trips_filtered.empty:
        st.warning("No se encontraron viajes para esta ruta.")
        return

    # 🔹 Filtrar los viajes según la dirección (0 = ida, 1 = vuelta)
    ida_trips = trips_filtered[trips_filtered["direction_id"] == 0]
    vuelta_trips = trips_filtered[trips_filtered["direction_id"] == 1]

    # 🔹 Obtener las paradas de ida y vuelta
    ida_stop_ids = stop_times[stop_times["trip_id"].isin(ida_trips["trip_id"])]["stop_id"].unique()
    vuelta_stop_ids = stop_times[stop_times["trip_id"].isin(vuelta_trips["trip_id"])]["stop_id"].unique()

    # 🔹 Obtener las paradas y las coordenadas
    ida_stops = stops[stops["stop_id"].isin(ida_stop_ids)]
    vuelta_stops = stops[stops["stop_id"].isin(vuelta_stop_ids)]

    # 🔹 Crear un mapa para la ida
    ida_map = folium.Map(location=[ida_stops["stop_lat"].mean(), ida_stops["stop_lon"].mean()], zoom_start=13)

    # Añadir paradas al mapa de ida sin usar MarkerCluster
    for _, stop in ida_stops.iterrows():
        folium.Marker(
            location=[stop["stop_lat"], stop["stop_lon"]],
            popup=stop["stop_name"]
        ).add_to(ida_map)

    # 🔹 Filtrar y mostrar los shapes de ida
    ida_shapes = shapes[shapes["shape_id"].isin(ida_trips["shape_id"])]
    for shape_id in ida_shapes["shape_id"].unique():
        shape_points = ida_shapes[ida_shapes["shape_id"] == shape_id][["shape_pt_lat", "shape_pt_lon"]]
        folium.PolyLine(
            locations=shape_points.values.tolist(),
            color="blue",  # Puedes cambiar el color según prefieras
            weight=3,
            opacity=0.7
        ).add_to(ida_map)

    # 🔹 Crear un mapa para la vuelta
    vuelta_map = folium.Map(location=[vuelta_stops["stop_lat"].mean(), vuelta_stops["stop_lon"].mean()], zoom_start=13)

    # Añadir paradas al mapa de vuelta sin usar MarkerCluster
    for _, stop in vuelta_stops.iterrows():
        folium.Marker(
            location=[stop["stop_lat"], stop["stop_lon"]],
            popup=stop["stop_name"]
        ).add_to(vuelta_map)

    # 🔹 Filtrar y mostrar los shapes de vuelta
    vuelta_shapes = shapes[shapes["shape_id"].isin(vuelta_trips["shape_id"])]
    for shape_id in vuelta_shapes["shape_id"].unique():
        shape_points = vuelta_shapes[vuelta_shapes["shape_id"] == shape_id][["shape_pt_lat", "shape_pt_lon"]]
        folium.PolyLine(
            locations=shape_points.values.tolist(),
            color="red",  # Puedes cambiar el color según prefieras
            weight=3,
            opacity=0.7
        ).add_to(vuelta_map)

    # 🔹 Mostrar los mapas en Streamlit
    st.subheader("Mapa de paradas - Dirección: Ida")
    folium_static(ida_map, 2000, 600)
    st.subheader("Lista paradas Ida")
    st.dataframe(ida_stops)

    st.subheader("Mapa de paradas - Dirección: Vuelta")
    folium_static(vuelta_map, 2000, 600)
    st.subheader("Lista paradas Vuelta")
    st.dataframe(vuelta_stops)
