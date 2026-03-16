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
from labels import get_labels

st.set_page_config(page_title="Historical Letters | Исторически Писма", layout="wide")

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

# --- Language Selector ---
_lang_opt = st.sidebar.radio(
    "🌐 Language / Език",
    ["Български", "English"],
    horizontal=True,
    key="lang_radio"
)
_lang = 'en' if _lang_opt == "English" else 'bg'
st.session_state['lang'] = _lang
L = get_labels(_lang)

# --- Load Data ---
XML_FILE = "data_english.xml" if _lang == 'en' else "data.xml"
data = load_data(XML_FILE)

st.title(L['app_title'])

# --- Define Tabs ---
tab_docs, tab_map, tab_stats, tab_search, tab_network, tab_geo_network, tab_topics, tab_commodity, tab_temporal = st.tabs([
    L['tab_docs'],
    L['tab_map'],
    L['tab_stats'],
    L['tab_search'],
    L['tab_network'],
    L['tab_geo_network'],
    L['tab_topics'],
    L['tab_commodity'],
    L['tab_temporal']
])

# ---------------------------------------------------------------------------------
# 1) DOCS TAB
# ---------------------------------------------------------------------------------
with tab_docs:
    st.sidebar.header(L['sidebar_correspondence'])

    all_senders = sorted({d['sender_name'] for d in data if d['sender_name']})
    selected_sender = st.sidebar.selectbox(L['select_sender'], [L['none_option']] + all_senders)

    if selected_sender != L['none_option']:
        sender_docs = [d for d in data if d['sender_name'] == selected_sender]
        sender_addressees = sorted({d['addressee_name'] for d in sender_docs if d['addressee_name']})
        selected_addressee = st.sidebar.selectbox(L['select_addressee'], [L['none_option']] + sender_addressees)

        if selected_addressee != L['none_option']:
            # Филтрираме по избран изпращач и получател
            filtered_docs = filter_correspondence(data, selected_sender, selected_addressee)
            if filtered_docs:
                st.write(L['found_docs'].format(n=len(filtered_docs), s=selected_sender, a=selected_addressee))
                shelfmarks = [d['shelfmark'] for d in filtered_docs]
                selected_shelfmark = st.selectbox(L['select_doc'], shelfmarks)
                selected_entry = next(d for d in filtered_docs if d['shelfmark'] == selected_shelfmark)

                st.subheader(f"{L['doc_label']} {selected_entry['shelfmark']}")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"### {L['sender_info']}")
                    st.write(f"**{L['name']}:** {selected_entry['sender_name']}")
                    st.write(f"**{L['location']}:** {selected_entry['sender_place']}")
                    st.write(f"**{L['date']}:** {selected_entry['sender_date']}")

                with col2:
                    st.markdown(f"### {L['addressee_info']}")
                    st.write(f"**{L['name']}:** {selected_entry['addressee_name']}")
                    st.write(f"**{L['location']}:** {selected_entry['addressee_place']}")

                st.markdown("---")
                st.markdown(f"### {L['main_topics']}")
                if selected_entry['main_topics']:
                    for t in selected_entry['main_topics']:
                        st.write("- " + t)
                else:
                    st.write(L['no_data'])

                st.markdown(f"### {L['keywords']}")
                if selected_entry['keywords']:
                    for k in selected_entry['keywords']:
                        st.write("- " + k)
                else:
                    st.write(L['no_data'])

                st.markdown(f"### {L['other_info']}")
                if selected_entry['other_info']:
                    for o in selected_entry['other_info']:
                        st.write("- " + o)
                else:
                    st.write(L['no_data'])

                st.markdown(f"### {L['mentioned_places']}")
                places_data = [p for p in selected_entry['mentioned_places'] if p['latitude'] is not None and p['longitude'] is not None]

                if places_data:
                    df_places = pd.DataFrame([{"lat": p["latitude"], "lon": p["longitude"]} for p in places_data])
                    st.map(df_places)
                    st.markdown(f"#### {L['place_details']}")
                    for p in places_data:
                        st.write(f"- **{p['name']}**: [{L['more_info']}]({p['ref']}) (lat: {p['latitude']}, lon: {p['longitude']})")
                else:
                    if selected_entry['mentioned_places']:
                        st.write(L['no_coords'])
                        for p in selected_entry['mentioned_places']:
                            st.write(f"- **{p['name']}**")
                    else:
                        st.write(L['no_places'])

                st.markdown(f"### {L['mentioned_persons']}")
                if selected_entry['mentioned_persons']:
                    for person in selected_entry['mentioned_persons']:
                        st.write("- " + person)
                else:
                    st.write(L['no_data'])
            else:
                st.write(L['no_docs_found'].format(s=selected_sender, a=selected_addressee))
        else:
            st.write(L['select_addressee_prompt'])
    else:
        st.write(L['select_sender_prompt'])

# ---------------------------------------------------------------------------------
# 2) MAP TAB
# ---------------------------------------------------------------------------------
with tab_map:
    st.header(L['map_header'])
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
            st.subheader(L['map_settings'])
            map_height = st.slider(L['map_height_label'], 400, 800, 500, 50)
            show_fullscreen = st.checkbox(L['fullscreen_cb'], False)
            
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
            title=L['fullscreen_title'],
            title_cancel=L['fullscreen_cancel'],
            force_separate_button=True,
        ).add_to(m)
        
        marker_cluster = MarkerCluster(
            name=L['clusters_label'],
            control=True,
            show=True
        ).add_to(m)

        for _, place in df_all_places.iterrows():
            popup_html = f"<b>{place['name']}</b><br>"
            if place['ref']:
                popup_html += f"<a href='{place['ref']}' target='_blank'>{L['add_info']}</a><br>"
            popup_html += f"{L['mention_count_label']} {place['count']}"
            
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
                tooltip=f"{place['name']} ({place['count']} {L['mentions']})",
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
        st.markdown(L['map_legend'])
        
    else:
        st.write(L['no_coord_places'])

# ---------------------------------------------------------------------------------
# 3) STATS TAB
# ---------------------------------------------------------------------------------
with tab_stats:
    st.header(L['stats_header'])

    df = pd.DataFrame(data)
    if not df.empty:
        st.subheader(L['sender_dist'])
        sender_counts = df['sender_name'].value_counts().reset_index()
        sender_counts.columns = ['sender_name', 'count']
        fig_pie_sender = px.pie(sender_counts, names='sender_name', values='count', title=L['docs_by_sender_title'])
        st.plotly_chart(fig_pie_sender, width='stretch')

        st.markdown("---")

        st.subheader(L['docs_by_addressee'])
        addressee_counts = df['addressee_name'].value_counts().reset_index()
        addressee_counts.columns = [L['addressee_col'], L['doc_count_col']]

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
            st.write(L['no_addressee_data'])

        st.markdown("---")

        st.subheader(L['top_keywords'])
        all_keywords = []
        for kw_list in df['keywords']:
            all_keywords.extend(kw_list)
        if all_keywords:
            keywords_series = pd.Series(all_keywords).value_counts().reset_index()
            keywords_series.columns = [L['keyword_col'], L['mention_col']]

            keywords_table = keywords_series.dropna(subset=[L['keyword_col']])

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
                        selected_keyword = first_row.get(L['keyword_col'], None)
                elif isinstance(selected_rows, pd.DataFrame):
                    if not selected_rows.empty:
                        first_row = selected_rows.iloc[0]
                        selected_keyword = first_row.get(L['keyword_col'], None)

                if selected_keyword:
                    st.markdown(f"### {L['related_docs_hdr'].format(kw=selected_keyword)}")
                    related_docs = df[df['keywords'].apply(lambda kws: selected_keyword in kws)]

                    if not related_docs.empty:
                        related_shelfmarks = related_docs['shelfmark'].dropna().unique().tolist()
                        st.write(f"**{L['found_shelfmarks'].format(n=len(related_shelfmarks))}**")
                        for sm in related_shelfmarks:
                            st.write(f"- {sm}")
                    else:
                        st.write(L['no_docs_keyword'])
                else:
                    st.write(L['select_keyword'])
            else:
                st.write(L['no_keywords_filter'])
        else:
            st.write(L['no_keywords'])
    else:
        st.write(L['no_stats'])

# ---------------------------------------------------------------------------------
# 4) SEARCH TAB
# ---------------------------------------------------------------------------------
with tab_search:
    st.header(L['search_header'])

    all_shelfmarks = sorted({d['shelfmark'] for d in data if d['shelfmark']})
    search_query = st.text_input(L['search_input'], "")

    if search_query:
        filtered_shelfmarks = [sm for sm in all_shelfmarks if search_query.lower() in sm.lower()]
    else:
        filtered_shelfmarks = all_shelfmarks

    selected_shelfmark = st.selectbox(L['select_shelfmark'], [L['none_option']] + filtered_shelfmarks)

    if selected_shelfmark != L['none_option']:
        selected_entry = next((d for d in data if d['shelfmark'] == selected_shelfmark), None)
        if selected_entry:
            st.subheader(f"{L['doc_label']} {selected_entry['shelfmark']}")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### {L['sender_info']}")
                st.write(f"**{L['name']}:** {selected_entry['sender_name']}")
                st.write(f"**{L['location']}:** {selected_entry['sender_place']}")
                st.write(f"**{L['date']}:** {selected_entry['sender_date']}")

            with col2:
                st.markdown(f"### {L['addressee_info']}")
                st.write(f"**{L['name']}:** {selected_entry['addressee_name']}")
                st.write(f"**{L['location']}:** {selected_entry['addressee_place']}")

            st.markdown("---")
            st.markdown(f"### {L['main_topics']}")
            if selected_entry['main_topics']:
                for t in selected_entry['main_topics']:
                    st.write("- " + t)
            else:
                st.write(L['no_data'])

            st.markdown(f"### {L['keywords']}")
            if selected_entry['keywords']:
                for k in selected_entry['keywords']:
                    st.write("- " + k)
            else:
                st.write(L['no_data'])

            st.markdown(f"### {L['other_info']}")
            if selected_entry['other_info']:
                for o in selected_entry['other_info']:
                    st.write("- " + o)
            else:
                st.write(L['no_data'])

            st.markdown(f"### {L['mentioned_places']}")
            places_data = [p for p in selected_entry['mentioned_places'] if p['latitude'] is not None and p['longitude'] is not None]

            if places_data:
                df_places = pd.DataFrame([{"lat": p["latitude"], "lon": p["longitude"]} for p in places_data])
                st.map(df_places)
                st.markdown(f"#### {L['place_details']}")
                for p in places_data:
                    st.write(f"- **{p['name']}**: [{L['more_info']}]({p['ref']}) (lat: {p['latitude']}, lon: {p['longitude']})")
            else:
                if selected_entry['mentioned_places']:
                    st.write(L['no_coords'])
                    for p in selected_entry['mentioned_places']:
                        st.write(f"- **{p['name']}**")
                else:
                    st.write(L['no_places'])

            st.markdown(f"### {L['mentioned_persons']}")
            if selected_entry['mentioned_persons']:
                for person in selected_entry['mentioned_persons']:
                    st.write("- " + person)
            else:
                st.write(L['no_data'])
        else:
            st.write(L['shelfmark_not_found'])
    else:
        st.write(L['select_shelfmark_prompt'])

# ---------------------------------------------------------------------------------
# 5) NETWORK ANALYSIS TAB
# ---------------------------------------------------------------------------------
with tab_network:
    st.header(L['network_header'])
    show_network_analysis(data)

# ---------------------------------------------------------------------------------
# 6) GEOGRAPHICAL NETWORK TAB
# ---------------------------------------------------------------------------------
with tab_geo_network:
    st.header(L['geo_header'])
    show_geographical_network(data)

# ---------------------------------------------------------------------------------
# 7) TOPICS AND KEYWORDS ANALYSIS TAB
# ---------------------------------------------------------------------------------
with tab_topics:
    st.header(L['topics_header'])
    show_topics_keywords_analysis(data)

# ---------------------------------------------------------------------------------
# 8) COMMODITY NETWORK FLOW TAB
# ---------------------------------------------------------------------------------
with tab_commodity:
    st.header(L['commodity_header'])
    show_commodity_network_analysis(data)

# ---------------------------------------------------------------------------------
# 9) TEMPORAL NETWORK ANALYSIS TAB
# ---------------------------------------------------------------------------------
with tab_temporal:
    st.header(L['temporal_header'])
    show_temporal_network_analysis(data)

