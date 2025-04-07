import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

def show_route_shape_debug_page(gtfs_data):
    st.title("🧪 Depuración visual de rutas y shapes")

    routes_df = gtfs_data.get("routes")
    trips_df = gtfs_data.get("trips")
    shapes_df = gtfs_data.get("shapes")
    stop_times_df = gtfs_data.get("stop_times")

    if any(df is None for df in (routes_df, trips_df, shapes_df, stop_times_df)):
        st.error("Faltan datos necesarios (routes, trips, shapes o stop_times).")
        return

    # 🔹 Selector por nombre de ruta
    route_names = routes_df["route_long_name"].dropna().unique().tolist()
    selected_route_name = st.sidebar.selectbox("Selecciona una ruta por nombre", route_names)

    selected_route_id = routes_df[routes_df["route_long_name"] == selected_route_name]["route_id"].values[0]

    st.markdown(f"**route_id seleccionado:** `{selected_route_id}`")

    # 🔸 Filtrar trips para esa ruta
    trips_for_route = trips_df[trips_df["route_id"] == selected_route_id].copy()

    if trips_for_route.empty:
        st.warning("No hay trips asociados a esta ruta.")
        return

    # Comprobar qué trips tienen stop_times
    trip_ids_with_stops = stop_times_df["trip_id"].unique()
    trips_for_route["has_stops"] = trips_for_route["trip_id"].isin(trip_ids_with_stops)

    # Mostrar tabla
    st.subheader("🎫 Trips asociados")
    st.dataframe(trips_for_route[["trip_id", "shape_id", "has_stops"]])

    # Opcional: mostrar trips sin paradas
    show_trips_without_stops = st.sidebar.checkbox("Mostrar trips sin paradas (shapes en rojo)", value=True)

    # Mapa con los shapes
    st.subheader("🗺 Shapes asociados a los trips")

    all_latlons = []

    for _, trip in trips_for_route.iterrows():
        if not trip["has_stops"] and not show_trips_without_stops:
            continue

        shape_id = trip["shape_id"]
        if pd.isna(shape_id):
            continue

        shape_points = shapes_df[shapes_df["shape_id"] == shape_id].sort_values("shape_pt_sequence")
        latlons = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))
        all_latlons.extend(latlons)

    if all_latlons:
        avg_lat = sum(lat for lat, lon in all_latlons) / len(all_latlons)
        avg_lon = sum(lon for lat, lon in all_latlons) / len(all_latlons)
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
    else:
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=7)

    # Añadir líneas al mapa
    for _, trip in trips_for_route.iterrows():
        if not trip["has_stops"] and not show_trips_without_stops:
            continue

        shape_id = trip["shape_id"]
        if pd.isna(shape_id):
            continue

        shape_points = shapes_df[shapes_df["shape_id"] == shape_id].sort_values("shape_pt_sequence")
        latlons = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))
        color = "green" if trip["has_stops"] else "red"

        if len(latlons) > 1:
            folium.PolyLine(
                latlons,
                color=color,
                weight=3,
                tooltip=f"trip_id: {trip['trip_id']} ({'✅' if trip['has_stops'] else '❌'})"
            ).add_to(m)

    st_folium(m, width=2000, height=600)

    # 🔸 Extra: mostrar shapes sin trips (huérfanos)
    st.subheader("🔍 Shapes no asociados a ningún trip")

    used_shape_ids = set(trips_df["shape_id"].dropna().unique())
    all_shape_ids = set(shapes_df["shape_id"].dropna().unique())
    unused_shape_ids = all_shape_ids - used_shape_ids

    if not unused_shape_ids:
        st.success("✅ Todos los shapes están asociados a trips.")
        return

    st.info(f"Se han encontrado {len(unused_shape_ids)} shape_id no usados por ningún trip.")
    show_unused = st.checkbox("Mostrar shapes no asociados en el mapa (en azul)")

    if show_unused:
        all_unused_latlons = []

        for shape_id in unused_shape_ids:
            shape_points = shapes_df[shapes_df["shape_id"] == shape_id].sort_values("shape_pt_sequence")
            latlons = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))
            all_unused_latlons.extend(latlons)

        if all_unused_latlons:
            avg_lat = sum(lat for lat, lon in all_unused_latlons) / len(all_unused_latlons)
            avg_lon = sum(lon for lat, lon in all_unused_latlons) / len(all_unused_latlons)
            m_unused = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
        else:
            m_unused = folium.Map(location=[40.4168, -3.7038], zoom_start=7)

        for shape_id in unused_shape_ids:
            shape_points = shapes_df[shapes_df["shape_id"] == shape_id].sort_values("shape_pt_sequence")
            latlons = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))
            if len(latlons) > 1:
                folium.PolyLine(latlons, color="blue", weight=2, tooltip=f"Shape huérfano: {shape_id}").add_to(m_unused)

        st_folium(m_unused, width=2000, height=600)
