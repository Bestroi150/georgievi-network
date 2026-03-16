# Historical Correspondence Network Analysis

A Streamlit application for the analysis and visualization of **historical correspondence networks** based on TEI XML–encoded data.

The application provides interactive tools for exploring **communication patterns, geographic relationships, temporal dynamics, and thematic connections** within collections of historical letters.

It is designed primarily for **digital humanities research**, enabling historians to examine correspondence networks through multiple analytical perspectives.

---

# Overview

This application transforms historical correspondence datasets (encoded in **TEI XML**) into **interactive network visualizations and analytical dashboards**.

It enables researchers to explore:

* communication networks between correspondents
* geographic patterns of correspondence
* temporal development of communication networks
* thematic relationships between letters
* trade and commodity networks referenced in the corpus

The application was developed to analyze merchant correspondence datasets such as the **Georgievi Brothers trade letters (1847–1863)**.

The TEI XML dataset used in the application is available in the following repository:

[https://github.com/Bestroi150/georgievi-correspondence](https://github.com/Bestroi150/georgievi-correspondence)

---

# Analytical Modules

The application includes **nine analytical modules**, each focusing on a different aspect of correspondence network analysis.

## 1. Statistical Overview

*(Статистически данни)*

Provides a general overview of the dataset, including:

* number of letters
* distribution by year
* most frequent correspondents
* summary metrics for the corpus

Interactive tables allow filtering and export for further analysis.

---

## 2. Correspondence Network

*(Мрежов анализ на кореспонденциите)*

Visualizes the **network of senders and addressees**.

Features include:

* interactive network graphs
* node size based on number of connections
* multiple layout algorithms
* centrality measures (degree, betweenness, closeness)
* edge weights representing correspondence frequency

---

## 3. Geographic Network

*(Географски мрежов анализ)*

Displays correspondence connections between places using interactive maps.

Capabilities include:

* mapping communication routes
* visualization of geographic clusters
* adjustable connection thresholds
* integration with OpenStreetMap and satellite imagery

---

## 4. Topics and Keywords Network

*(Анализ на теми и ключови думи)*

Analyzes thematic relationships between letters through **co-occurrence networks of topics and keywords**.

This module enables:

* identification of thematic clusters
* analysis of concept centrality
* exploration of relationships between subjects mentioned in the correspondence.

---

## 5. Commodity Network Analysis

*(Анализ на стокови мрежи)*

Examines the relationships between **commodities and places** referenced in the letters.

This module visualizes:

* commodity-place networks
* trade routes
* patterns of economic exchange across regions.

---

## 6. Temporal Network Analysis

*(Темпорален мрежов анализ)*

Analyzes the **development of correspondence networks over time**.

Features include:

* temporal filtering
* visualization of network evolution
* chronological patterns in communication activity.

---

## 7. Search and Filtering

*(Търсене и филтриране)*

Advanced search tools allow filtering the dataset according to:

* correspondents
* locations
* dates
* keywords and thematic categories.

Filtered results can be exported for further research.

---

## 8. Letters List

*(Списък на писмата)*

Provides a complete inventory of the letters in the dataset, including:

* detailed metadata
* sortable tables
* search functionality
* individual letter inspection.

---

## 9. Map of Mentioned Places

*(Карта на всички споменати места)*

Displays a geographic overview of all places referenced in the corpus.

The interactive map allows users to:

* explore geographic distribution
* identify clusters of correspondence activity
* examine regional communication patterns.

---

# Technology Stack

## Interface

* **Streamlit** — web application framework for interactive data applications
* **Custom CSS** — styling and layout
* **Bulgarian-language interface**

---

## Visualization Libraries

* **PyVis** — interactive network graphs
* **Plotly** — statistical and exploratory charts
* **Folium** — interactive geographic maps
* **NetworkX** — network analysis algorithms

---

## Data Processing

* **Pandas** — dataset management and analysis
* **lxml** — TEI XML parsing
* **NumPy** — numerical computation

---

# Installation

### Requirements

* Python 3.8 or higher
* pip package manager

---

### Setup

```bash
git clone https://github.com/Bestroi150/georgievi-network.git
cd georgievi-network

pip install -r requirements.txt

streamlit run app.py
```

---

# Data

The application processes historical correspondence data encoded in **TEI XML**.

The dataset used by the application is available here:

[https://github.com/Bestroi150/georgievi-correspondence](https://github.com/Bestroi150/georgievi-correspondence)

Typical elements include:

```xml
<letter>
  <sender>Sender Name</sender>
  <addressee>Addressee Name</addressee>
  <date>YYYY-MM-DD</date>
  <place>Location</place>
</letter>
```

From these elements the application constructs:

* person-to-person correspondence networks
* geographic communication networks
* temporal networks
* thematic networks
* commodity exchange networks.

---

# Research Applications

The application is intended for use in:

* **digital humanities research**
* **historical network analysis**
* **economic and social history**
* **correspondence studies**
* **historical geography**

It supports the exploration of archival letter collections and the reconstruction of historical communication and trade networks.

---

# License

Creative Commons Attribution 4.0 International License (CC-BY 4.0)

[https://github.com/Bestroi150/georgievi-network/blob/main/LICENSE](https://github.com/Bestroi150/georgievi-network/blob/main/LICENSE)

---

# Acknowledgment

This tool was developed to support the analysis of historical correspondence datasets and digital humanities research.

---
