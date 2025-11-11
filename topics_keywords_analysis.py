import streamlit as st
import itertools
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import numpy as np

def show_topics_keywords_analysis(data):
    """
    Creates and displays topic and keyword co-occurrence network analysis.
    
    Analyzes relationships between main topics and keywords across letters.
    """
    
    st.subheader("Анализ на теми и ключови думи")
    st.markdown("""
    **Анализ:** Мрежа на съвместно срещане на теми и ключови думи в писмата  
    **Възли:** Основни теми и ключови думи  
    **Връзки:** Съвместно споменаване в едно и също писмо  
    **Размер на възела:** Честота на споменаване
    """)
    
    # Extract topics and keywords data
    topics_data, cooccurrence_data = extract_topics_keywords_data(data)
    
    if not topics_data:
        st.warning("Няма достатъчно данни за анализ на теми и ключови думи.")
        return
    
    # Create tabs for different views
    network_tab, frequency_tab, analysis_tab = st.tabs(["🕸️ Мрежа", "📊 Честота", "🔍 Анализ"])
    
    with network_tab:
        show_topics_network(topics_data, cooccurrence_data)
    
    with frequency_tab:
        show_topics_frequency(topics_data)
    
    with analysis_tab:
        show_topics_analysis(topics_data, cooccurrence_data)

def extract_topics_keywords_data(data):
    """
    Extract topics and keywords data from the correspondence data.
    Returns topics data and co-occurrence information.
    """
    letters_topics = []
    all_topics = Counter()
    
    for entry in data:
        topics = set()
        
        # Add main topics
        main_topics = entry.get('main_topics', [])
        for topic in main_topics:
            if topic:
                topic = topic.strip()
                topics.add(topic)
                all_topics[topic] += 1
        
        # Add keywords
        keywords = entry.get('keywords', [])
        for keyword in keywords:
            if keyword:
                keyword = keyword.strip()
                topics.add(keyword)
                all_topics[keyword] += 1
        
        if topics:
            letters_topics.append(topics)
    
    # Build co-occurrence edges
    cooccurrence = Counter()
    for topics in letters_topics:
        for a, b in itertools.combinations(sorted(topics), 2):
            cooccurrence[(a, b)] += 1
    
    return {
        'letters_topics': letters_topics,
        'all_topics': all_topics,
        'topic_frequency': dict(all_topics)
    }, dict(cooccurrence)

def show_topics_network(topics_data, cooccurrence_data):
    """
    Display interactive network of topics and keywords using Plotly.
    """
    st.subheader("Мрежа на теми и ключови думи")
    
    if not cooccurrence_data:
        st.warning("Няма връзки между темите за визуализация.")
        return
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add edges with weights
    for (topic1, topic2), weight in cooccurrence_data.items():
        G.add_edge(topic1, topic2, weight=weight)
    
    # Set node attributes
    topic_freq = topics_data['topic_frequency']
    nx.set_node_attributes(G, topic_freq, 'frequency')
    
    # Control parameters
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Настройки")
        min_cooccurrence = st.slider(
            "Минимално съвместно срещане:", 
            1, 
            max(cooccurrence_data.values()) if cooccurrence_data else 5, 
            1,
            key="topics_min_cooccurrence"
        )
        
        layout_algorithm = st.selectbox(
            "Алгоритъм за подредба:",
            ["spring", "circular", "kamada_kawai"],
            index=0,
            key="topics_layout_algorithm"
        )
    
    with col1:
        # Filter edges by minimum co-occurrence
        filtered_edges = [(a, b) for (a, b), w in cooccurrence_data.items() if w >= min_cooccurrence]
        
        if not filtered_edges:
            st.warning("Няма връзки, които отговарят на критерия.")
            return
        
        # Create filtered graph
        G_filtered = nx.Graph()
        G_filtered.add_edges_from(filtered_edges)
        
        # Calculate layout
        if layout_algorithm == "spring":
            pos = nx.spring_layout(G_filtered, k=1, iterations=50)
        elif layout_algorithm == "circular":
            pos = nx.circular_layout(G_filtered)
        else:  # kamada_kawai
            pos = nx.kamada_kawai_layout(G_filtered)
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add edges
        edge_x = []
        edge_y = []
        for edge in G_filtered.edges():
            if edge[0] in pos and edge[1] in pos:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        ))
        
        # Add nodes
        node_x = []
        node_y = []
        node_text = []
        node_sizes = []
        node_colors = []
        
        for node in G_filtered.nodes():
            if node in pos:
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                frequency = topic_freq.get(node, 1)
                connections = len(list(G_filtered.neighbors(node)))
                
                node_text.append(
                    f"<b>{node}</b><br>"
                    f"Честота: {frequency}<br>"
                    f"Връзки: {connections}"
                )
                
                node_sizes.append(max(20, frequency * 10))
                node_colors.append(frequency)
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            hovertext=node_text,
            text=[node for node in G_filtered.nodes() if node in pos],
            textposition="middle center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Честота"),
                line=dict(width=2, color='black')
            )
        ))
        
        fig.update_layout(
            title='Мрежа на теми и ключови думи',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[dict(
                text=f"Показани {len(G_filtered.nodes())} теми с минимум {min_cooccurrence} съвместни споменавания",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, width='stretch')

def show_topics_frequency(topics_data):
    """
    Display frequency analysis of topics and keywords.
    """
    st.subheader("Честота на теми и ключови думи")
    
    topic_freq = topics_data['topic_frequency']
    
    if not topic_freq:
        st.warning("Няма данни за честота на темите.")
        return
    
    # Create frequency DataFrame
    freq_df = pd.DataFrame(
        list(topic_freq.items()),
        columns=['Тема/Ключова дума', 'Честота']
    ).sort_values('Честота', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Топ 20 най-чести теми")
        top_topics = freq_df.head(20)
        st.dataframe(top_topics, width='stretch')
    
    with col2:
        st.subheader("Разпределение на честотата")
        fig = px.bar(
            top_topics.head(15),
            x='Честота',
            y='Тема/Ключова дума',
            orientation='h',
            title='Най-чести теми и ключови думи'
        )
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, width='stretch')
    
    # Statistics
    st.subheader("Статистики")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Общо теми/думи", len(topic_freq))
    
    with col2:
        st.metric("Средна честота", f"{np.mean(list(topic_freq.values())):.1f}")
    
    with col3:
        st.metric("Най-честа", max(topic_freq.values()))
    
    with col4:
        unique_topics = sum(1 for freq in topic_freq.values() if freq == 1)
        st.metric("Уникални (1x)", unique_topics)

def show_topics_analysis(topics_data, cooccurrence_data):
    """
    Show detailed analysis of topic relationships.
    """
    st.subheader("Детайлен анализ на връзките")
    
    if not cooccurrence_data:
        st.warning("Няма данни за анализ на връзките.")
        return
    
    # Create co-occurrence DataFrame
    cooc_df = pd.DataFrame([
        {
            'Тема 1': topic1,
            'Тема 2': topic2,
            'Съвместни споменавания': weight
        }
        for (topic1, topic2), weight in cooccurrence_data.items()
    ]).sort_values('Съвместни споменавания', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Най-силни връзки")
        st.dataframe(cooc_df.head(15), width='stretch')
    
    with col2:
        st.subheader("Разпределение на силата на връзките")
        fig = px.histogram(
            cooc_df,
            x='Съвместни споменавания',
            nbins=20,
            title='Разпределение на съвместните споменавания'
        )
        st.plotly_chart(fig, width='stretch')
    
    # Network metrics
    if cooccurrence_data:
        st.subheader("Мрежови метрики")
        
        G = nx.Graph()
        for (topic1, topic2), weight in cooccurrence_data.items():
            G.add_edge(topic1, topic2, weight=weight)
        
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        
        # Create centrality DataFrame
        centrality_df = pd.DataFrame({
            'Тема': list(degree_centrality.keys()),
            'Степенна централност': list(degree_centrality.values()),
            'Посредническа централност': list(betweenness_centrality.values()),
            'Близостна централност': list(closeness_centrality.values())
        }).round(3)
        
        # Sort by degree centrality
        centrality_df = centrality_df.sort_values('Степенна централност', ascending=False)
        
        st.subheader("Топ 15 теми по централност")
        st.dataframe(centrality_df.head(15), width='stretch')
        
        # Show network statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Възли в мрежата", G.number_of_nodes())
        
        with col2:
            st.metric("Връзки в мрежата", G.number_of_edges())
        
        with col3:
            density = nx.density(G)
            st.metric("Плътност", f"{density:.3f}")
        
        with col4:
            if nx.is_connected(G):
                avg_path = nx.average_shortest_path_length(G)
                st.metric("Средна дистанция", f"{avg_path:.2f}")
            else:
                st.metric("Компоненти", nx.number_connected_components(G))
