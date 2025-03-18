import streamlit as st
import folium
from streamlit_folium import folium_static

def mostrar_paradas():
    feed = st.session_state["feed"]
    st.subheader("📍 Paradas")

    # Mapa con paradas
    m = folium.Map(location=[feed.stops.stop_lat.mean(), feed.stops.stop_lon.mean()], zoom_start=12)
    for _, stop in feed.stops.iterrows():
        folium.Marker(
            location=[stop.stop_lat, stop.stop_lon],
            popup=stop.stop_name,
            icon=folium.Icon(color="blue")
        ).add_to(m)

    folium_static(m, width=1200)

    # Mostrar lista de paradas
    st.dataframe(feed.stops)
