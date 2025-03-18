import streamlit as st
import pandas as pd

def mostrar_horarios():
    if "feed" in st.session_state:
        feed = st.session_state["feed"]

        st.subheader("⏰ Horarios de Paradas")

        # Seleccionar parada
        parada_seleccionada = st.selectbox("Selecciona una parada", feed.stops["stop_name"])

        # Filtrar los horarios de la parada seleccionada
        horarios = feed.stop_times[feed.stop_times["stop_id"] == feed.stops[feed.stops["stop_name"] == parada_seleccionada]["stop_id"].values[0]]

        # Mostrar los horarios en una tabla
        if not horarios.empty:
            st.write("Horarios de la parada:", parada_seleccionada)
            st.dataframe(horarios[["trip_id", "arrival_time", "departure_time"]])
        else:
            st.error(f"No se encontraron horarios para la parada {parada_seleccionada}.")
