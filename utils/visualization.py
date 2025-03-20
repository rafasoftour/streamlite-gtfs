import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

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

def display_route_map(gtfs_data, route_id):
    """Muestra el mapa con el shape de la ruta seleccionada"""
    
    trips = gtfs_data.get("trips")
    shapes = gtfs_data.get("shapes")

    if trips is None or trips.empty or shapes is None or shapes.empty:
        st.warning("No hay datos suficientes para mostrar la ruta en el mapa.")
        return

    # 🔹 Buscar el `shape_id` asociado al `route_id` en `trips`
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

    # 🔹 Agregar la línea de la ruta al mapa
    route_coords = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))
    folium.PolyLine(route_coords, color="blue", weight=4.5, opacity=0.8).add_to(route_map)

    # 🔹 Mostrar el mapa en Streamlit
    folium_static(route_map)