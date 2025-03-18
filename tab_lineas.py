import streamlit as st
import folium
from streamlit_folium import folium_static

def mostrar_lineas():
    if "feed" in st.session_state:
        feed = st.session_state["feed"]
        
        # Verificar si el archivo GTFS contiene datos de shapes
        if "shapes" in feed:
            st.subheader("🚍 Rutas en el Mapa")

            # Crear el mapa centrado en el promedio de las latitudes y longitudes de las paradas
            m = folium.Map(location=[feed.stops.stop_lat.mean(), feed.stops.stop_lon.mean()], zoom_start=12)

            # Mostrar las rutas en el mapa usando los datos de shapes.txt
            for _, shape in feed.shapes.iterrows():
                # Filtrar las paradas asociadas a esta forma (shape_id)
                paradas = feed.stop_times[feed.stop_times["shape_id"] == shape.shape_id]
                
                # Crear una lista de coordenadas (lat, lon) de las paradas asociadas
                coordinates = [
                    [feed.stops.loc[feed.stops["stop_id"] == stop_id, "stop_lat"].values[0],
                     feed.stops.loc[feed.stops["stop_id"] == stop_id, "stop_lon"].values[0]]
                    for stop_id in paradas["stop_id"]
                ]

                # Añadir la línea de la ruta en el mapa
                folium.PolyLine(
                    locations=coordinates,
                    color="blue",
                    weight=3,
                    opacity=0.7
                ).add_to(m)

                # Añadir las paradas de la ruta en el mapa
                for stop_id in paradas["stop_id"]:
                    stop = feed.stops.loc[feed.stops["stop_id"] == stop_id].iloc[0]
                    folium.Marker(
                        location=[stop.stop_lat, stop.stop_lon],
                        popup=stop.stop_name,
                        icon=folium.Icon(color="red")
                    ).add_to(m)

            # Mostrar el mapa con el estilo "wide"
            folium_static(m, width=1200)

        else:
            st.error("El archivo GTFS no contiene datos de shapes.")
