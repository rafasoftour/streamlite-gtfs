# utils/validation_utils.py

import pandas as pd
import streamlit as st
from shapely.geometry import Point, LineString

def check_unused_shapes(gtfs_data):
    st.subheader("🔍 Validación: Shapes no utilizados")

    if "trips" not in gtfs_data or "shapes" not in gtfs_data:
        st.warning("Faltan los archivos `trips.txt` o `shapes.txt`.")
        return

    trips_df = gtfs_data["trips"]
    shapes_df = gtfs_data["shapes"]

    used_shape_ids = set(trips_df["shape_id"].dropna().unique())
    all_shape_ids = set(shapes_df["shape_id"].unique())

    unused_shape_ids = sorted(all_shape_ids - used_shape_ids)

    if unused_shape_ids:
        st.error(f"Se encontraron {len(unused_shape_ids)} `shape_id` no utilizados en ningún `trip`.")
        st.dataframe(pd.DataFrame({"unused_shape_id": unused_shape_ids}))
    else:
        st.success("✅ Todos los shapes están correctamente utilizados en trips.")

def check_trips_without_stop_times(gtfs_data):
    st.subheader("🛑 Validación: Trips sin paradas")

    if "trips" not in gtfs_data or "stop_times" not in gtfs_data:
        st.warning("Faltan los archivos `trips.txt` o `stop_times.txt`.")
        return

    trips_df = gtfs_data["trips"]
    stop_times_df = gtfs_data["stop_times"]

    trips_with_stops = set(stop_times_df["trip_id"].unique())
    all_trip_ids = set(trips_df["trip_id"].unique())

    trips_without_stops = sorted(all_trip_ids - trips_with_stops)

    if trips_without_stops:
        st.error(f"Se encontraron {len(trips_without_stops)} trips sin paradas.")
        st.dataframe(pd.DataFrame({"trip_id_sin_paradas": trips_without_stops}))
    else:
        st.success("✅ Todos los trips tienen paradas asociadas.")

# utils/validation_utils.py

def check_invalid_stop_ids(gtfs_data):
    st.subheader("🚫 Validación: stop_id inválidos en stop_times.txt")

    if "stop_times" not in gtfs_data or "stops" not in gtfs_data:
        st.warning("Faltan los archivos `stop_times.txt` o `stops.txt`.")
        return

    stop_times_df = gtfs_data["stop_times"]
    stops_df = gtfs_data["stops"]

    used_stop_ids = set(stop_times_df["stop_id"].unique())
    defined_stop_ids = set(stops_df["stop_id"].unique())

    invalid_stop_ids = sorted(used_stop_ids - defined_stop_ids)

    if invalid_stop_ids:
        st.error(f"Se encontraron {len(invalid_stop_ids)} `stop_id` en stop_times.txt que no existen en stops.txt.")
        st.dataframe(pd.DataFrame({"stop_id_inválido": invalid_stop_ids}))
    else:
        st.success("✅ Todos los stop_id utilizados existen en stops.txt.")

def check_stops_far_from_shapes(gtfs_data, threshold_meters=500):
    st.subheader("📏 Validación: Paradas lejos del trazado del shape")

    trips = gtfs_data.get("trips")
    stop_times = gtfs_data.get("stop_times")
    stops = gtfs_data.get("stops")
    shapes = gtfs_data.get("shapes")

    if any(df is None for df in [trips, stop_times, stops, shapes]):
        st.warning("Faltan archivos necesarios: trips, stop_times, stops o shapes.")
        return

    # Preprocesar shapes
    shape_lines = {}
    for shape_id, group in shapes.groupby("shape_id"):
        shape_points = group.sort_values("shape_pt_sequence")[["shape_pt_lon", "shape_pt_lat"]].values
        shape_lines[shape_id] = LineString(shape_points)

    # Asociar cada trip con su shape y sus paradas
    trips_with_stops = stop_times.merge(trips[["trip_id", "shape_id"]], on="trip_id")
    trips_with_stops = trips_with_stops.merge(stops[["stop_id", "stop_lat", "stop_lon"]], on="stop_id")

    problematic_trips = []

    for trip_id, group in trips_with_stops.groupby("trip_id"):
        shape_id = group["shape_id"].iloc[0]
        if shape_id not in shape_lines:
            continue

        shape_line = shape_lines[shape_id]
        all_far = True
        for _, row in group.iterrows():
            stop_point = Point(row["stop_lon"], row["stop_lat"])
            distance = stop_point.distance(shape_line) * 111000  # approx meters
            if distance < threshold_meters:
                all_far = False
                break

        if all_far:
            problematic_trips.append({
                "trip_id": trip_id,
                "shape_id": shape_id,
                "n_paradas": len(group)
            })

    if problematic_trips:
        st.error(f"Se encontraron {len(problematic_trips)} trips cuyas paradas están alejadas del shape.")
        st.dataframe(pd.DataFrame(problematic_trips))
    else:
        st.success("✅ Todas las paradas están razonablemente alineadas con sus shapes.")