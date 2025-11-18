# 📬 Historical Correspondence Network Analysis

A comprehensive Streamlit application for analyzing historical correspondence data through multiple network analysis perspectives. This tool provides deep insights into communication patterns, geographical relationships, temporal evolution, and thematic connections in historical letter collections.

## 🌟 Overview

This application transforms historical correspondence data (in TEI XML format) into interactive network visualizations, offering researchers and historians powerful analytical tools to explore communication networks, trade relationships, and social connections across time and space.

## 🚀 Features

### 📊 **9 Analysis Modules:**

#### 1. **📈 Статистически данни** (Statistical Data)
- Comprehensive data overview and metrics
- Letter frequency analysis by year, sender, and addressee
- Interactive data tables with filtering capabilities
- Export functionality for further analysis

#### 2. **📬 Мрежов анализ на кореспонденциите** (Correspondence Network)
- Interactive sender-addressee relationship networks
- Node sizing based on connection degree
- Multiple layout algorithms (ForceAtlas2, Repulsion, Hierarchical)
- Centrality measures (betweenness, closeness, degree)
- Edge weight visualization showing letter frequency

#### 3. **🗺️ Географски мрежов анализ** (Geographical Network)
- **Full-screen interactive maps** with place connections
- Arc visualization showing communication routes
- Clustered markers for geographic regions
- Connection threshold filtering
- Integration with OpenStreetMap and satellite imagery

#### 4. **🏷️ Анализ на теми и ключови думи** (Topics & Keywords Analysis)
- Co-occurrence network analysis of themes and keywords
- Topic clustering and relationship mapping
- Centrality analysis of key concepts
- Interactive network exploration with adjustable parameters

#### 5. **📦 Анализ на стокови мрежи** (Commodity Network Analysis)
- Bipartite network analysis of commodity-place relationships
- Trade route visualization and analysis
- Economic relationship mapping
- Commodity flow patterns across regions

#### 6. **⏰ Темпорален мрежов анализ** (Temporal Network Analysis)
- Time-based evolution of communication networks
- Temporal filtering and animation capabilities
- Chronological pattern analysis
- Network dynamics over time periods

#### 7. **🔍 Търсене и филтриране** (Search & Filtering)
- Advanced search functionality across all correspondence
- Multi-criteria filtering (date, location, participants)
- Full-text search capabilities
- Export filtered results

#### 8. **📋 Списък на писмата** (Letters List)
- Comprehensive letter inventory
- Detailed metadata display
- Sortable and searchable interface
- Individual letter inspection

#### 9. **📍 Карта на всички споменати места** (Map of All Mentioned Places)
- **Full-screen geographical overview**
- All locations mentioned in correspondence
- Interactive place exploration
- Geographic distribution analysis

### 🎨 **Enhanced User Experience:**
- **Professional Bulgarian interface** with intuitive navigation
- **Tab-based organization** for easy module switching
- **Responsive design** adapting to different screen sizes
- **Custom styling** with professional gradients and shadows
- **Interactive controls** on main pages (no sidebar dependency)
- **Real-time filtering** and dynamic visualizations

### 🔧 **Technical Features:**
- **Cached data loading** for optimal performance
- **Error handling** and user-friendly feedback
- **Memory-optimized** network computations
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Export capabilities** for data and visualizations

## 🛠️ Technology Stack

### **Frontend & UI:**
- **Streamlit** - Interactive web application framework
- **Custom CSS** - Professional styling and responsive design
- **Bulgarian localization** - Native language interface

### **Data Visualization:**
- **PyVis** - Interactive network visualizations
- **Plotly** - Dynamic charts and statistical plots
- **Folium** - Full-screen geographical mapping
- **NetworkX** - Network analysis and graph algorithms

### **Data Processing:**
- **Pandas** - Data manipulation and analysis
- **XML parsing** - TEI format correspondence processing
- **NumPy** - Numerical computations (version <2.0 for compatibility)

### **Network Analysis:**
- **Centrality algorithms** - Betweenness, closeness, degree calculations
- **Community detection** - Network clustering and grouping
- **Temporal analysis** - Time-series network evolution
- **Bipartite networks** - Two-mode network analysis

## 📋 Installation & Usage

### **Prerequisites:**
```bash
Python 3.8+
pip package manager
```

### **Local Development:**
```bash
# Clone the repository
git clone https://github.com/Bestroi150/georgievi-network.git
cd georgievi-network

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### **Dependencies:**
- `streamlit>=1.41.1` - Main application framework
- `pandas>=1.5.0` - Data manipulation
- `folium==0.19.2` - Interactive mapping
- `streamlit_folium==0.23.2` - Streamlit-Folium integration
- `plotly>=5.0.0` - Interactive plotting
- `networkx==3.4.2` - Network analysis
- `pyvis==0.3.2` - Network visualization
- `numpy<2.0` - Numerical operations
- `lxml>=4.6.0` - XML parsing

## 📊 Data Format

The application processes historical correspondence data in **TEI XML format**. Required elements include:

```xml
<letter>
    <sender>Sender Name</sender>
    <addressee>Addressee Name</addressee>
    <date>YYYY-MM-DD</date>
    <place>Location</place>
    <content>Letter content with topics and commodities</content>
</letter>
```

### **Supported Analysis Types:**
- **Person-to-person networks** from sender/addressee relationships
- **Geographical networks** from place mentions and coordinates
- **Temporal networks** from date information and chronological patterns
- **Thematic networks** from content analysis and keyword extraction
- **Economic networks** from commodity and trade relationship mentions

## 🎯 Use Cases

### **For Historians:**
- Analyze communication patterns in historical periods
- Trace information flow and social connections
- Map geographical extent of correspondence networks
- Study temporal evolution of relationships

### **For Digital Humanities Researchers:**
- Network analysis of literary correspondences
- Social network reconstruction from archival sources
- Comparative analysis of communication patterns
- Temporal and spatial visualization of historical data

### **For Data Scientists:**
- Network analysis methodology demonstration
- Historical data visualization techniques
- Multi-modal network analysis examples
- Interactive dashboard development patterns

## 📈 Performance

- **Startup time:** ~10-30 seconds (data loading)
- **Memory usage:** 500MB-1GB (depending on dataset size)
- **Concurrent users:** Optimized for educational/research use
- **Data capacity:** Handles thousands of letters efficiently

## 🤝 Contributing

This is a research tool developed for historical correspondence analysis. Contributions welcome for:
- Additional network analysis algorithms
- Enhanced visualization options
- Performance optimizations
- Documentation improvements

## 📄 License

[Creative Commons Attribution 4.0 International License (CC-BY-4.0)](https://github.com/Bestroi150/georgievi-network/blob/main/LICENSE)

## 📞 Support

For questions about usage, data formats, or technical issues:
- Review the technical documentation
- Consult Streamlit documentation for framework-specific questions

---

**Built with ❤️ for Digital Humanities Research**

*Transforming historical correspondence into interactive network insights*



