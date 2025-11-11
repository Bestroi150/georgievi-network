import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# Import the new modules
from network_analysis import show_network_analysis
from geographical_network import show_geographical_network
from topics_keywords_analysis import show_topics_keywords_analysis
from commodity_analysis import show_commodity_network_analysis
from temporal_analysis import show_temporal_network_analysis

st.set_page_config(page_title="Визуализация на исторически писма", layout="wide")

XML_FILE = "data.xml"

@st.cache_data
def load_data(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    objects = root.findall('.//tei:listObject/tei:object', namespaces=ns)

    entries = []
    for obj in objects:
        shelfmark_elem = obj.find('.//tei:idno', namespaces=ns)
        shelfmark = shelfmark_elem.text if shelfmark_elem is not None else None

        sender_desc = obj.find('.//tei:desc[@type="sender"]', namespaces=ns)
        if sender_desc is not None:
            sender_name = sender_desc.find('tei:persName', namespaces=ns)
            sender_place = sender_desc.find('tei:placeName', namespaces=ns)
            sender_date = sender_desc.find('tei:date', namespaces=ns)
            sender_name = sender_name.text if sender_name is not None else None
            sender_place = sender_place.text if sender_place is not None else None
            sender_date = sender_date.text if sender_date is not None else None
        else:
            sender_name = None
            sender_place = None
            sender_date = None

        addressee_desc = obj.find('.//tei:desc[@type="addresse"]', namespaces=ns)
        if addressee_desc is not None:
            addressee_name = addressee_desc.find('tei:persName', namespaces=ns)
            addressee_place = addressee_desc.find('tei:placeName', namespaces=ns)
            addressee_name = addressee_name.text if addressee_name is not None else None
            addressee_place = addressee_place.text if addressee_place is not None else None
        else:
            addressee_name = None
            addressee_place = None

        main_topics = [i.text for i in obj.findall('.//tei:list[@type="main_topics"]/tei:item', namespaces=ns)]
        keywords = [i.text for i in obj.findall('.//tei:list[@type="keywords"]/tei:item', namespaces=ns)]
        other_info = [i.text for i in obj.findall('.//tei:list[@type="other_info"]/tei:item', namespaces=ns)]

        places_elems = obj.findall('.//tei:desc[@type="mentioned_places"]/tei:placeName', namespaces=ns)
        mentioned_places = []
        for p in places_elems:
            place_name = p.text
            latitude = p.attrib.get('latitude')
            longitude = p.attrib.get('longitude')
            ref = p.attrib.get('ref')
            if latitude and longitude:
                try:
                    lat = float(latitude)
                    lon = float(longitude)
                except ValueError:
                    lat = None
                    lon = None
            else:
                lat = None
                lon = None
            mentioned_places.append({
                'name': place_name,
                'latitude': lat,
                'longitude': lon,
                'ref': ref
            })

        mentioned_persons = [p.text for p in obj.findall('.//tei:desc[@type="mentioned_persons"]/tei:persName', namespaces=ns)]

        entries.append({
            'shelfmark': shelfmark,
            'sender_name': sender_name,
            'sender_place': sender_place,
            'sender_date': sender_date,
            'addressee_name': addressee_name,
            'addressee_place': addressee_place,
            'main_topics': main_topics,
            'keywords': keywords,
            'other_info': other_info,
            'mentioned_places': mentioned_places,
            'mentioned_persons': mentioned_persons
        })
    return entries

def filter_correspondence(data, sender, addressee):
    return [d for d in data if d['sender_name'] == sender and d['addressee_name'] == addressee]

# --- Load Data ---
data = load_data(XML_FILE)

st.title("Визуализация на исторически писма (TEI XML)")

# --- Define Tabs ---
tab_docs, tab_map, tab_stats, tab_search, tab_network, tab_geo_network, tab_topics, tab_commodity, tab_temporal = st.tabs([
    "Документи", 
    "Карта", 
    "Статистика", 
    "Търсене по Shelfmark", 
    "Мрежов анализ",
    "Географска мрежа",
    "Теми и думи",
    "Стокови потоци",
    "Темпорален анализ"
])

# ---------------------------------------------------------------------------------
# 1) DOCS TAB
# ---------------------------------------------------------------------------------
with tab_docs:
    st.sidebar.header("Избор на кореспонденция")

    # Първо избираме изпращач
    all_senders = sorted({d['sender_name'] for d in data if d['sender_name']})
    selected_sender = st.sidebar.selectbox("Изберете изпращач:", ["(Няма)"] + all_senders)

    if selected_sender != "(Няма)":
        # Филтрираме документите само за този изпращач
        sender_docs = [d for d in data if d['sender_name'] == selected_sender]
        # Извличаме уникалните получатели на този изпращач
        sender_addressees = sorted({d['addressee_name'] for d in sender_docs if d['addressee_name']})
        selected_addressee = st.sidebar.selectbox("Изберете получател:", ["(Няма)"] + sender_addressees)

        if selected_addressee != "(Няма)":
            # Филтрираме по избран изпращач и получател
            filtered_docs = filter_correspondence(data, selected_sender, selected_addressee)
            if filtered_docs:
                st.write(f"Намерени {len(filtered_docs)} документа между {selected_sender} и {selected_addressee}:")
                # Избор на конкретен документ по сигнатура
                shelfmarks = [d['shelfmark'] for d in filtered_docs]
                selected_shelfmark = st.selectbox("Изберете документ:", shelfmarks)
                selected_entry = next(d for d in filtered_docs if d['shelfmark'] == selected_shelfmark)

                # Визуализираме детайлите
                st.subheader(f"Документ: {selected_entry['shelfmark']}")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Информация за изпращача")
                    st.write(f"**Име:** {selected_entry['sender_name']}")
                    st.write(f"**Местоположение:** {selected_entry['sender_place']}")
                    st.write(f"**Дата:** {selected_entry['sender_date']}")

                with col2:
                    st.markdown("### Информация за получателя")
                    st.write(f"**Име:** {selected_entry['addressee_name']}")
                    st.write(f"**Местоположение:** {selected_entry['addressee_place']}")

                st.markdown("---")
                st.markdown("### Основни теми")
                if selected_entry['main_topics']:
                    for t in selected_entry['main_topics']:
                        st.write("- " + t)
                else:
                    st.write("Няма данни")

                st.markdown("### Ключови думи")
                if selected_entry['keywords']:
                    for k in selected_entry['keywords']:
                        st.write("- " + k)
                else:
                    st.write("Няма данни")

                st.markdown("### Друга информация")
                if selected_entry['other_info']:
                    for o in selected_entry['other_info']:
                        st.write("- " + o)
                else:
                    st.write("Няма данни")

                st.markdown("### Споменати места")
                places_data = [p for p in selected_entry['mentioned_places'] if p['latitude'] is not None and p['longitude'] is not None]

                if places_data:
                    df_places = pd.DataFrame([{"lat": p["latitude"], "lon": p["longitude"]} for p in places_data])
                    st.map(df_places)
                    st.markdown("#### Подробности за споменатите места:")
                    for p in places_data:
                        st.write(f"- **{p['name']}**: [Повече информация]({p['ref']}) (lat: {p['latitude']}, lon: {p['longitude']})")
                else:
                    if selected_entry['mentioned_places']:
                        st.write("Няма координатни данни за споменатите места")
                        for p in selected_entry['mentioned_places']:
                            st.write(f"- **{p['name']}** (без координати)")
                    else:
                        st.write("Няма споменати места")

                st.markdown("### Споменати личности")
                if selected_entry['mentioned_persons']:
                    for person in selected_entry['mentioned_persons']:
                        st.write("- " + person)
                else:
                    st.write("Няма данни")
            else:
                st.write(f"Няма намерени документи за кореспонденция между {selected_sender} и {selected_addressee}.")
        else:
            st.write("Моля, изберете получател.")
    else:
        st.write("Моля, изберете изпращач.")

# ---------------------------------------------------------------------------------
# 2) MAP TAB
# ---------------------------------------------------------------------------------
with tab_map:
    st.header("Карта на всички споменати места")
    all_places = []
    place_counts = {}
    for entry in data:
        for p in entry['mentioned_places']:
            if p['latitude'] is not None and p['longitude'] is not None:
                key = (p['latitude'], p['longitude'], p['name'], p['ref'])
                if key in place_counts:
                    place_counts[key] += 1
                else:
                    place_counts[key] = 1

    if place_counts:
        for key, count in place_counts.items():
            lat, lon, name, ref = key
            all_places.append({
                'name': name,
                'latitude': lat,
                'longitude': lon,
                'ref': ref,
                'count': count
            })

        df_all_places = pd.DataFrame(all_places)
        avg_lat = df_all_places['latitude'].mean()
        avg_lon = df_all_places['longitude'].mean()

        # Map display options
        col1, col2 = st.columns([3, 1])
        with col2:
            st.subheader("Настройки на картата")
            map_height = st.slider("Височина на картата", 400, 800, 500, 50)
            show_fullscreen = st.checkbox("Покажи в пълен екран", False)
            
        # Folium map with enhanced features
        m = folium.Map(
            location=[avg_lat, avg_lon], 
            zoom_start=5,
            prefer_canvas=True,
            control_scale=True
        )
        
        # Add multiple tile layers including topographic
        folium.TileLayer('openstreetmap', name='OpenStreetMap', control=True).add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Topographic (Esri)',
            overlay=False,
            control=True
        ).add_to(m)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
            attr='Google',
            name='Terrain (Google)',
            overlay=False,
            control=True
        ).add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite (Esri)',
            overlay=False,
            control=True
        ).add_to(m)

        # Add marker clustering
        from folium.plugins import MarkerCluster, Fullscreen
        
        # Add fullscreen button
        Fullscreen(
            position="topright",
            title="Покажи в пълен екран",
            title_cancel="Излез от пълен екран",
            force_separate_button=True,
        ).add_to(m)
        
        marker_cluster = MarkerCluster(
            name="Споменати места",
            control=True,
            show=True
        ).add_to(m)

        for _, place in df_all_places.iterrows():
            popup_html = f"<b>{place['name']}</b><br>"
            if place['ref']:
                popup_html += f"<a href='{place['ref']}' target='_blank'>Допълнителна информация</a><br>"
            popup_html += f"Брой споменавания: {place['count']}"
            
            # Create marker with different colors based on mention count
            if place['count'] >= 5:
                icon_color = 'red'
            elif place['count'] >= 3:
                icon_color = 'orange'
            elif place['count'] >= 2:
                icon_color = 'green'
            else:
                icon_color = 'blue'
                
            folium.Marker(
                location=[place['latitude'], place['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{place['name']} ({place['count']} споменавания)",
                icon=folium.Icon(color=icon_color, icon='info-sign')
            ).add_to(marker_cluster)

        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add minimap
        from folium.plugins import MiniMap
        minimap = MiniMap(toggle_display=True)
        m.add_child(minimap)

        # Display the map
        if show_fullscreen:
            st_folium(m, width=None, height=map_height, returned_objects=["last_object_clicked"])
        else:
            st_folium(m, width=700, height=map_height, returned_objects=["last_object_clicked"])
            
        # Legend
        st.markdown("""
        **Легенда на картата:**
        - 🔴 Червени маркери: 5+ споменавания
        - 🟠 Оранжеви маркери: 3-4 споменавания  
        - 🟢 Зелени маркери: 2 споменавания
        - 🔵 Сини маркери: 1 споменаване
        
        **Слоеве на картата:**
        - **OpenStreetMap**: Стандартна карта
        - **Topographic**: Топографска карта с релеф
        - **Terrain**: Терен с релефни данни
        - **Satellite**: Сателитни изображения
        """)
        
    else:
        st.write("Няма споменати места с координати.")

# ---------------------------------------------------------------------------------
# 3) STATS TAB
# ---------------------------------------------------------------------------------
with tab_stats:
    st.header("Статистика")

    df = pd.DataFrame(data)
    if not df.empty:
        # Първи график: Пай диаграма за брой документи по изпращач
        st.subheader("Разпределение на документите по изпращач")
        sender_counts = df['sender_name'].value_counts().reset_index()
        sender_counts.columns = ['sender_name', 'count']
        fig_pie_sender = px.pie(sender_counts, names='sender_name', values='count', title='Брой документи по изпращач')
        st.plotly_chart(fig_pie_sender, width='stretch')

        st.markdown("---")

        # Втори: интерактивна таблица за брой документи по получател
        st.subheader("Брой документи по получател")
        addressee_counts = df['addressee_name'].value_counts().reset_index()
        addressee_counts.columns = ['Получател', 'Брой документи']

        if not addressee_counts.empty:
            gb_addressee = GridOptionsBuilder.from_dataframe(addressee_counts)
            gb_addressee.configure_pagination(paginationAutoPageSize=True)
            gb_addressee.configure_side_bar()
            gb_addressee.configure_default_column(enableSorting=True, enableFiltering=True)
            gridOptions_addressee = gb_addressee.build()

            AgGrid(
                addressee_counts,
                gridOptions=gridOptions_addressee,
                height=400,
                fit_columns_on_grid_load=True,
                theme='alpine',
                enable_enterprise_modules=False,
                allow_unsafe_jscode=False
            )
        else:
            st.write("Няма данни за получатели.")

        st.markdown("---")

        # Трети: най-често споменавани ключови думи
        st.subheader("Най-често споменавани ключови думи")
        all_keywords = []
        for kw_list in df['keywords']:
            all_keywords.extend(kw_list)
        if all_keywords:
            keywords_series = pd.Series(all_keywords).value_counts().reset_index()
            keywords_series.columns = ['Ключова дума', 'Брой споменавания']

            # Филтрираме празните ключови думи, ако има
            keywords_table = keywords_series.dropna(subset=['Ключова дума'])

            if not keywords_table.empty:
                gb_keywords = GridOptionsBuilder.from_dataframe(keywords_table)
                gb_keywords.configure_pagination(paginationAutoPageSize=True)
                gb_keywords.configure_side_bar()
                gb_keywords.configure_default_column(enableSorting=True, enableFiltering=True)
                gb_keywords.configure_selection('single')
                gridOptions_keywords = gb_keywords.build()

                grid_response = AgGrid(
                    keywords_table,
                    gridOptions=gridOptions_keywords,
                    height=400,
                    fit_columns_on_grid_load=True,
                    theme='alpine',
                    enable_enterprise_modules=False,
                    allow_unsafe_jscode=False,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED
                )

                selected_rows = grid_response.get('selected_rows', [])
                selected_keyword = None

                if isinstance(selected_rows, list) and len(selected_rows) > 0:
                    first_row = selected_rows[0]
                    if isinstance(first_row, dict):
                        selected_keyword = first_row.get('Ключова дума', None)
                elif isinstance(selected_rows, pd.DataFrame):
                    if not selected_rows.empty:
                        first_row = selected_rows.iloc[0]
                        selected_keyword = first_row.get('Ключова дума', None)

                if selected_keyword:
                    st.markdown(f"### Документи свързани с ключовата дума: **{selected_keyword}**")
                    related_docs = df[df['keywords'].apply(lambda kws: selected_keyword in kws)]

                    if not related_docs.empty:
                        related_shelfmarks = related_docs['shelfmark'].dropna().unique().tolist()
                        st.write(f"**Намерените shelfmarks ({len(related_shelfmarks)}):**")
                        for sm in related_shelfmarks:
                            st.write(f"- {sm}")
                    else:
                        st.write("Няма намерени документи за тази ключова дума.")
                else:
                    st.write("Моля, изберете ключова дума от таблицата.")
            else:
                st.write("Няма ключови думи след филтрация.")
        else:
            st.write("Няма ключови думи.")
    else:
        st.write("Няма данни за статистика.")

# ---------------------------------------------------------------------------------
# 4) SEARCH TAB
# ---------------------------------------------------------------------------------
with tab_search:
    st.header("Търсене по Shelfmark")

    all_shelfmarks = sorted({d['shelfmark'] for d in data if d['shelfmark']})
    search_query = st.text_input("Въведете Shelfmark или част от него:", "")

    if search_query:
        filtered_shelfmarks = [sm for sm in all_shelfmarks if search_query.lower() in sm.lower()]
    else:
        filtered_shelfmarks = all_shelfmarks

    selected_shelfmark = st.selectbox("Изберете Shelfmark:", ["(Няма)"] + filtered_shelfmarks)

    if selected_shelfmark != "(Няма)":
        selected_entry = next((d for d in data if d['shelfmark'] == selected_shelfmark), None)
        if selected_entry:
            st.subheader(f"Документ: {selected_entry['shelfmark']}")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Информация за изпращача")
                st.write(f"**Име:** {selected_entry['sender_name']}")
                st.write(f"**Местоположение:** {selected_entry['sender_place']}")
                st.write(f"**Дата:** {selected_entry['sender_date']}")

            with col2:
                st.markdown("### Информация за получателя")
                st.write(f"**Име:** {selected_entry['addressee_name']}")
                st.write(f"**Местоположение:** {selected_entry['addressee_place']}")

            st.markdown("---")
            st.markdown("### Основни теми")
            if selected_entry['main_topics']:
                for t in selected_entry['main_topics']:
                    st.write("- " + t)
            else:
                st.write("Няма данни")

            st.markdown("### Ключови думи")
            if selected_entry['keywords']:
                for k in selected_entry['keywords']:
                    st.write("- " + k)
            else:
                st.write("Няма данни")

            st.markdown("### Друга информация")
            if selected_entry['other_info']:
                for o in selected_entry['other_info']:
                    st.write("- " + o)
            else:
                st.write("Няма данни")

            st.markdown("### Споменати места")
            places_data = [p for p in selected_entry['mentioned_places'] if p['latitude'] is not None and p['longitude'] is not None]

            if places_data:
                df_places = pd.DataFrame([{"lat": p["latitude"], "lon": p["longitude"]} for p in places_data])
                st.map(df_places)
                st.markdown("#### Подробности за споменатите места:")
                for p in places_data:
                    st.write(f"- **{p['name']}**: [Повече информация]({p['ref']}) (lat: {p['latitude']}, lon: {p['longitude']})")
            else:
                if selected_entry['mentioned_places']:
                    st.write("Няма координатни данни за споменатите места")
                    for p in selected_entry['mentioned_places']:
                        st.write(f"- **{p['name']}** (без координати)")
                else:
                    st.write("Няма споменати места")

            st.markdown("### Споменати личности")
            if selected_entry['mentioned_persons']:
                for person in selected_entry['mentioned_persons']:
                    st.write("- " + person)
            else:
                st.write("Няма данни")
        else:
            st.write("Документът с този Shelfmark не беше намерен.")
    else:
        st.write("Моля, изберете Shelfmark от списъка.")

# ---------------------------------------------------------------------------------
# 5) NETWORK ANALYSIS TAB
# ---------------------------------------------------------------------------------
with tab_network:
    st.header("Мрежов анализ на кореспонденциите")
    # Call our newly created function from network_analysis.py
    show_network_analysis(data)

# ---------------------------------------------------------------------------------
# 6) GEOGRAPHICAL NETWORK TAB
# ---------------------------------------------------------------------------------
with tab_geo_network:
    st.header("Географска мрежа на места")
    # Call our newly created function from geographical_network.py
    show_geographical_network(data)

# ---------------------------------------------------------------------------------
# 7) TOPICS AND KEYWORDS ANALYSIS TAB
# ---------------------------------------------------------------------------------
with tab_topics:
    st.header("Анализ на теми и ключови думи")
    # Call function from topics_keywords_analysis.py
    show_topics_keywords_analysis(data)

# ---------------------------------------------------------------------------------
# 8) COMMODITY NETWORK FLOW TAB
# ---------------------------------------------------------------------------------
with tab_commodity:
    st.header("Анализ на стоковите потоци")
    # Call function from commodity_analysis.py
    show_commodity_network_analysis(data)

# ---------------------------------------------------------------------------------
# 9) TEMPORAL NETWORK ANALYSIS TAB
# ---------------------------------------------------------------------------------
with tab_temporal:
    st.header("Темпорален анализ на комуникациите")
    # Call function from temporal_analysis.py
    show_temporal_network_analysis(data)
