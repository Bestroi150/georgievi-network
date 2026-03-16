import streamlit as st
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter, defaultdict
import numpy as np
from datetime import datetime
import plotly.colors as colors
from labels import get_labels

def show_temporal_network_analysis(data):
    """
    Creates and displays temporal network analysis of correspondence.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ta_subheader'])
    st.markdown(L['ta_desc'])
    
    # Extract temporal data
    temporal_data = extract_temporal_data(data)
    
    if not temporal_data['letters']:
        st.warning(L['ta_no_data'])
        return
    
    # Create tabs for different views
    timeline_tab, network_tab, analysis_tab = st.tabs([L['ta_inner_timeline'], L['ta_inner_network'], L['ta_inner_analysis']])
    
    with timeline_tab:
        show_temporal_timeline(temporal_data)
    
    with network_tab:
        show_temporal_network(temporal_data)
    
    with analysis_tab:
        show_temporal_analysis(temporal_data)

def extract_temporal_data(data):
    """
    Extract temporal data from the correspondence data.
    Returns letters with dates and temporal statistics.
    """
    letters = []
    date_formats = ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    
    for entry in data:
        sender = entry.get('sender_name')
        addressee = entry.get('addressee_name')
        date_str = entry.get('sender_date')
        
        if sender and addressee and date_str:
            date_obj = None
            # Try different date formats
            for date_format in date_formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), date_format)
                    break
                except ValueError:
                    continue
            
            if date_obj:
                letters.append({
                    'sender': sender.strip(),
                    'addressee': addressee.strip(),
                    'date': date_obj,
                    'date_str': date_str.strip(),
                    'year': date_obj.year,
                    'month': date_obj.month,
                    'shelfmark': entry.get('shelfmark', ''),
                    'main_topics': entry.get('main_topics', []),
                    'keywords': entry.get('keywords', [])
                })
    
    # Sort by date
    letters.sort(key=lambda x: x['date'])
    
    # Calculate temporal statistics
    if letters:
        date_range = {
            'start': min(letter['date'] for letter in letters),
            'end': max(letter['date'] for letter in letters),
            'span_days': (max(letter['date'] for letter in letters) - 
                         min(letter['date'] for letter in letters)).days
        }
    else:
        date_range = None
    
    return {
        'letters': letters,
        'date_range': date_range,
        'total_letters': len(letters)
    }

def show_temporal_timeline(temporal_data):
    """
    Display timeline view of correspondence.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ta_timeline_header'])
    
    letters = temporal_data['letters']
    
    if not letters:
        st.warning(L['ta_no_dates'])
        return
    
    # Create timeline DataFrame
    timeline_df = pd.DataFrame(letters)
    timeline_df['year_month'] = timeline_df['date'].dt.to_period('M')
    
    # Controls
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader(L['ta_settings'])
        
        min_date = timeline_df['date'].min().date()
        max_date = timeline_df['date'].max().date()
        
        selected_range = st.date_input(
            L['ta_period'],
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        group_by = st.selectbox(
            L['ta_groupby'],
            ["month", "year", "day"],
            index=0,
            key="temporal_group_by"
        )
        
        all_senders = sorted(set(letter['sender'] for letter in letters))
        selected_senders = st.multiselect(
            L['ta_senders'],
            all_senders,
            default=all_senders
        )
    
    with col1:
        # Filter data
        if len(selected_range) == 2:
            start_date, end_date = selected_range
            filtered_df = timeline_df[
                (timeline_df['date'].dt.date >= start_date) & 
                (timeline_df['date'].dt.date <= end_date) &
                (timeline_df['sender'].isin(selected_senders))
            ]
        else:
            filtered_df = timeline_df[timeline_df['sender'].isin(selected_senders)]
        
        if filtered_df.empty:
            st.warning(L['ta_no_period'])
            return
        
        # Create timeline chart
        if group_by == "day":
            grouped = filtered_df.groupby(filtered_df['date'].dt.date).size()
            x_values = [str(date) for date in grouped.index]
            x_title = L['ta_date_label']
        elif group_by == "month":
            grouped = filtered_df.groupby(filtered_df['date'].dt.to_period('M')).size()
            x_values = [str(period) for period in grouped.index]
            x_title = L['ta_month_label']
        else:  # year
            grouped = filtered_df.groupby(filtered_df['date'].dt.year).size()
            x_values = list(grouped.index)
            x_title = L['ta_year_label']
        
        fig = px.line(
            x=x_values,
            y=grouped.values,
            title=L['ta_letters_over_time'].format(g=group_by),
            markers=True
        )
        fig.update_xaxes(title=x_title)
        fig.update_yaxes(title=L['ta_letters_y'])
        st.plotly_chart(fig, width='stretch')
        
        if group_by == "month" and len(filtered_df) > 5:
            st.subheader(L['ta_heatmap_header'])
            
            filtered_df['month_name'] = filtered_df['date'].dt.strftime('%m')
            filtered_df['year'] = filtered_df['date'].dt.year
            
            heatmap_data = filtered_df.groupby(['year', 'month_name']).size().unstack(fill_value=0)
            
            if not heatmap_data.empty:
                fig = px.imshow(
                    heatmap_data.values,
                    labels=dict(x=L['ta_month'], y=L['ta_year_str'], color=L['ta_color']),
                    x=[str(col) for col in heatmap_data.columns],
                    y=[str(idx) for idx in heatmap_data.index],
                    aspect="auto",
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig, width='stretch')

def show_temporal_network(temporal_data):
    """
    Display temporal network evolution.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ta_net_header'])
    
    letters = temporal_data['letters']
    
    if not letters:
        st.warning(L['ta_no_net'])
        return
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader(L['ta_settings'])
        
        window_size = st.slider(
            L['ta_window_size'],
            30, 365, 90, 30,
            key="temporal_window_size"
        )
        
        show_animation = st.checkbox(L['ta_animation'], False, key="temporal_show_animation")
        
        layout_algorithm = st.selectbox(
            L['ta_layout'],
            ["spring", "circular", "kamada_kawai"],
            index=0,
            key="temporal_layout_algorithm"
        )
    
    with col1:
        if show_animation:
            show_temporal_animation(letters, window_size, layout_algorithm)
        else:
            show_static_temporal_network(letters, window_size, layout_algorithm)

def show_static_temporal_network(letters, window_size, layout_algorithm):
    """
    Show static temporal network for a selected time window.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    min_date = min(letter['date'] for letter in letters)
    max_date = max(letter['date'] for letter in letters)
    
    selected_date = st.date_input(
        L['ta_select_date'],
        value=min_date.date(),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
    
    # Convert to datetime
    center_date = datetime.combine(selected_date, datetime.min.time())
    
    # Filter letters within window
    window_start = center_date - pd.Timedelta(days=window_size//2)
    window_end = center_date + pd.Timedelta(days=window_size//2)
    
    windowed_letters = [
        letter for letter in letters
        if window_start <= letter['date'] <= window_end
    ]
    
    if not windowed_letters:
        st.warning(L['ta_no_window'].format(s=window_start.strftime('%Y-%m-%d'), e=window_end.strftime('%Y-%m-%d')))
        return
    
    # Create network
    G = nx.DiGraph()
    edge_counts = Counter()
    
    for letter in windowed_letters:
        sender = letter['sender']
        addressee = letter['addressee']
        edge_counts[(sender, addressee)] += 1
    
    # Add edges with weights
    for (sender, addressee), count in edge_counts.items():
        G.add_edge(sender, addressee, weight=count)
    
    # Calculate layout
    if layout_algorithm == "spring":
        pos = nx.spring_layout(G, k=1, iterations=50)
    elif layout_algorithm == "circular":
        pos = nx.circular_layout(G)
    else:  # kamada_kawai
        pos = nx.kamada_kawai_layout(G)
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Add edges
    edge_x = []
    edge_y = []
    edge_colors = []
    
    # Color edges by date (within window)
    edge_dates = []
    for sender, addressee, data in G.edges(data=True):
        # Find the average date for this edge
        edge_letters = [l for l in windowed_letters if l['sender'] == sender and l['addressee'] == addressee]
        if edge_letters:
            avg_date = sum([(l['date'] - min_date).days for l in edge_letters]) / len(edge_letters)
            edge_dates.append(avg_date)
        else:
            edge_dates.append(0)
    
    # Normalize edge dates for coloring
    if edge_dates:
        min_edge_date, max_edge_date = min(edge_dates), max(edge_dates)
        if min_edge_date != max_edge_date:
            norm_dates = [(d - min_edge_date) / (max_edge_date - min_edge_date) for d in edge_dates]
        else:
            norm_dates = [0.5] * len(edge_dates)
    else:
        norm_dates = []
    
    for i, (sender, addressee, data) in enumerate(G.edges(data=True)):
        if sender in pos and addressee in pos:
            x0, y0 = pos[sender]
            x1, y1 = pos[addressee]
            
            # Add arrow
            fig.add_annotation(
                x=x1, y=y1,
                ax=x0, ay=y0,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=colors.sequential.Viridis[int(norm_dates[i] * 9)] if norm_dates else 'blue'
            )
    
    # Add nodes
    node_x = []
    node_y = []
    node_text = []
    node_sizes = []
    
    # Calculate node frequencies in this window
    node_freq = Counter()
    for letter in windowed_letters:
        node_freq[letter['sender']] += 1
        node_freq[letter['addressee']] += 1
    
    for node in G.nodes():
        if node in pos:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            freq = node_freq.get(node, 0)
            in_degree = G.in_degree(node)
            out_degree = G.out_degree(node)
            
            node_text.append(
                f"<b>{node}</b><br>"
                f"{L['ta_sent_label'].format(n=out_degree)}<br>"
                f"{L['ta_received_label'].format(n=in_degree)}<br>"
                f"{L['ta_activity_label'].format(n=freq)}"
            )
            
            node_sizes.append(max(20, freq * 10))
    
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_text,
        text=[node for node in G.nodes() if node in pos],
        textposition="middle center",
        marker=dict(
            size=node_sizes,
            color='lightblue',
            line=dict(width=2, color='black')
        )
    ))
    
    fig.update_layout(
        title=L['ta_net_title'].format(s=window_start.strftime("%Y-%m-%d"), e=window_end.strftime("%Y-%m-%d"), n=len(windowed_letters)),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=60),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    st.plotly_chart(fig, width='stretch')
    
    st.subheader(L['ta_period_stats'])
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(L['ta_letters_metric'], len(windowed_letters))
    
    with col2:
        st.metric(L['ta_participants_metric'], len(G.nodes()))
    
    with col3:
        st.metric(L['ta_links_metric'], len(G.edges()))
    
    with col4:
        density = nx.density(G) if len(G.nodes()) > 1 else 0
        st.metric(L['ta_density_metric'], f"{density:.3f}")

def show_temporal_analysis(temporal_data):
    """
    Show detailed temporal analysis.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ta_analysis_header'])
    
    letters = temporal_data['letters']
    
    if not letters:
        st.warning(L['ta_no_analysis'])
        return
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(letters)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(L['ta_activity_header'])
        
        sender_activity = df.groupby(['sender', df['date'].dt.to_period('M')]).size().unstack(fill_value=0)
        
        if not sender_activity.empty:
            fig = px.imshow(
                sender_activity.values,
                labels=dict(x=L['ta_month'], y=L['ta_sender_y'], color=L['ta_color']),
                x=[str(col) for col in sender_activity.columns],
                y=[str(idx) for idx in sender_activity.index],
                aspect="auto",
                color_continuous_scale="Blues"
            )
            fig.update_layout(title=L['ta_activity_title'])
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader(L['ta_patterns'])
        
        communication_pairs = df.groupby(['sender', 'addressee']).size().reset_index(name='count')
        communication_pairs = communication_pairs.sort_values('count', ascending=False)
        
        st.subheader(L['ta_top_links'])
        st.dataframe(communication_pairs.head(10), width='stretch')
        
        fig = px.histogram(
            df,
            x='date',
            nbins=20,
            title=L['ta_letters_dist']
        )
        st.plotly_chart(fig, width='stretch')
    
    st.subheader(L['ta_evolution_header'])
    
    # Calculate metrics for different time windows
    time_windows = []
    metrics = []
    
    # Create monthly windows
    df['year_month'] = df['date'].dt.to_period('M')
    
    for period in sorted(df['year_month'].unique()):
        period_letters = df[df['year_month'] == period]
        
        # Create network for this period
        G = nx.DiGraph()
        for _, letter in period_letters.iterrows():
            G.add_edge(letter['sender'], letter['addressee'])
        
        if len(G.nodes()) > 0:
            time_windows.append(str(period))
            metrics.append({
                'period': str(period),
                'nodes': len(G.nodes()),
                'edges': len(G.edges()),
                'density': nx.density(G),
                'letters': len(period_letters)
            })
    
    if metrics:
        metrics_df = pd.DataFrame(metrics)
        
        # Plot network evolution
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=metrics_df['period'],
            y=metrics_df['nodes'],
            mode='lines+markers',
            name=L['ta_participants_trace'],
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=metrics_df['period'],
            y=metrics_df['letters'],
            mode='lines+markers',
            name=L['ta_letters_trace'],
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=L['ta_evolution_title'],
            xaxis=dict(title=L['ta_period_axis']),
            yaxis=dict(title=L['ta_participants_axis'], side='left'),
            yaxis2=dict(title=L['ta_letters_axis'], side='right', overlaying='y'),
            legend=dict(x=0.7, y=1)
        )
        
        st.plotly_chart(fig, width='stretch')
        
        st.subheader(L['ta_detail_periods'])
        st.dataframe(metrics_df, width='stretch')

def show_temporal_animation(letters, window_size, layout_algorithm):
    """
    Show animated temporal network (placeholder for now).
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)
    st.info(L['ta_anim_info'])
    
    # For now, show the static version
    show_static_temporal_network(letters, window_size, layout_algorithm)
