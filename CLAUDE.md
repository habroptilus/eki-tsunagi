# CLAUDE.md

必ず日本語で回答してください。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "駅つなぎ" (Eki-tsunagi) - a Japanese train station connection game built with Streamlit. Players navigate between train stations in Japan's major metropolitan areas by connecting adjacent stations, trying to reach a destination with the fewest stops.

## Core Architecture

### Data Pipeline

- **CSV Data Source**: Raw station/line data in `data/v2/` (company.csv, join.csv, line.csv, pref.csv, station.csv)
- **Graph Generation**: `build_graph.py` converts CSV data into JSON graph structures using area-specific configs
- **Configuration**: Area configs in `config/` define valid lines, station name normalization, and walking connections

### Application Structure

- **Main App**: `main.py` - Streamlit frontend with game state management
- **Game Logic**: `utils.py` - pathfinding, scoring, hint generation, and game mechanics
- **Graph Processing**: `graph.py` - legacy graph generation (use `build_graph.py` instead)

### Key Components

- **Graph Structure**: JSON files with stations as nodes, edges containing connected stations with line info
- **Walking Connections**: Special "徒歩" (walking) connections between nearby stations
- **Area System**: Players choose from different regions (中心部, 西部・南部, 北部・東部, 全域)
- **Scoring**: Based on path efficiency, lives lost, and hints used

## Development Commands

### Graph Generation

```bash
# Generate graph for specific area
python build_graph.py --config config/tokyo.json --base_output output/graph_tokyo.json --walking_output output/graph_tokyo_walking.json

# Generate for all areas
python build_graph.py --config config/nagoya.json --base_output output/graph_nagoya.json --walking_output output/graph_nagoya_walking.json
python build_graph.py --config config/osaka.json --base_output output/graph_osaka.json --walking_output output/graph_osaka_walking.json
```

### Running the Application

```bash
# Install dependencies
poetry install
# or
pip install -r requirements.txt

# Run Streamlit app
streamlit run main.py
```

### Development Tools

```bash
# Check graph structure
python check.py

# Generate similar stations analysis
python similar_stations.py

# Add walking connections (legacy)
python add_walking.py
```

## Configuration Files

### Area Configs (`config/*.json`)

- `lines`: Maps line codes to display names
- `normalize_name_map`: Station name standardization
- `valid_pref_cds`: Prefecture codes to include
- `walking_pairs`: Station pairs with walking connections

### Graph Files

- `graph_with_pos.json`: Base graph with coordinates
- `graph_with_pos_walking.json`: Graph with walking connections
- `area.json`: Area-specific start/goal station definitions
- `output/graph_*`: Area-specific generated graphs

## Game Flow

1. **Area Selection**: Player chooses geographic region
2. **Round Setup**: Game selects 3 random starting stations and 1 goal station
3. **Gameplay**: Player inputs station names to build path to goal
4. **Scoring**: Points based on path efficiency (20 max per round, 5 rounds total)
5. **Result**: Final score with area-specific title and social sharing

## Data Management

- Use `build_graph.py` for all graph generation (replaces legacy `graph.py`)
- Walking connections are defined in config files, not hardcoded
- Station name normalization handled via config to resolve variations
- Area boundaries defined by prefecture codes in config files

## Key Dependencies

- `streamlit`: Web application framework
- `pandas`: CSV data processing
- `pydantic`: Data validation for Edge model
- `poetry`: Dependency management

## Performance Considerations

- Graph data is cached using `@st.cache_data`
- BFS pathfinding for shortest path calculations
- Hint generation optimized to find closest stations to goal
