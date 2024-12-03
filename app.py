from flask import Flask, request, jsonify, render_template
import random, logging
import pandas as pd

app = Flask(__name__)


class Node:
    def __init__(self, name, heuristic):
        self.name = name
        self.heuristic = heuristic
        self.edges = {}
        self.halte = {}

    def add_edge(self, neighbor, cost):
        self.edges[neighbor] = cost

    def add_halte(self, halte_dict):
        self.halte = halte_dict

def a_star_search(start, goal):
    open_list = {start}
    came_from = {}
    g_score = {start: 0}
    f_score = {start: g_score[start] + nodes[start].heuristic}

    while open_list:
        # Choose the node in open_list with the lowest f_score
        current = min(open_list, key=lambda x: f_score.get(x, float('inf')))

        if current == goal:
            return reconstruct_path(came_from, current)

        open_list.remove(current)

        for neighbor, cost in nodes[current].edges.items():
            tentative_g_score = g_score[current] + cost

            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + nodes[neighbor].heuristic
                open_list.add(neighbor)

    return None

def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]

def get_halte_route(path, start_halte, end_halte, routeStops):
    halte_route = []
    for city in path:
        matching_haltes = [stop["halte"] for stop in routeStops if stop["city"] == city]
        if city == path[0]:  # Start city
            halte_route.append(start_halte if start_halte in matching_haltes else f"No halte for {city}")
        elif city == path[-1]:  # End city
            halte_route.append(end_halte if end_halte in matching_haltes else f"No halte for {city}")
        else:  # Intermediate cities
            halte_route.append(matching_haltes[0] if matching_haltes else f"No halte for {city}")
    return halte_route


# Initialize nodes with heuristic values and edges
df = pd.read_excel('data.xlsx')
df.to_json("data.json", orient="records")
print(df.head())
nodes = {}
for index, row in df.iterrows():
    nodes[row['Tempat']] = Node(row['Tempat'], row['Jarak'])

for index, row in df.iterrows():
    source = row['Source']
    destination = row['Destination']
    distance = row['Distance']

    if source not in nodes:
        nodes[source] = Node(source, distance)  # Assuming heuristic as distance for simplicity
    if destination not in nodes:
        nodes[destination] = Node(destination, distance)
    
    nodes[source].add_edge(destination, distance)
    nodes[destination].add_edge(source, distance)

# nodes['Surabaya'].add_halte({'Halte_Tunjungan', 'Halte_Darmo'})
# nodes['Gresik'].add_halte({'Halte_Gresik', 'Halte_Gresik_Kota_Baru'})
# nodes['Sidoarjo'].add_halte({'Halte_Sidoarjo_Terminal'})
# nodes['Malang'].add_halte({'Halte_Merdeka', 'Halte_Ijen'})
# nodes['Jember'].add_halte({'Halte_Universitas Jember', 'Halte_Kaliwates'})
# nodes['Bondowoso'].add_halte({'Halte_Tonkol'})
# nodes['Probolinggo'].add_halte({'Halte_Banyuangga' , 'Halte_Probolinggo' })
# nodes['Kediri'].add_halte({'Halte_Kediri' })
# nodes['Blitar'].add_halte({'Halte_Blitar' })
# nodes['Madiun'].add_halte({'Halte_Madiun'})
# nodes['Batu'].add_halte({'Halte_Batu'})
# nodes['Mojokerto'].add_halte({'Halte_Mojokerto'})


@app.route('/')
def home():
    return render_template('index.html')

logging.basicConfig(level=logging.DEBUG)

@app.route('/route', methods=['GET'])
def get_route():
    start = request.args.get('start')
    end = request.args.get('end')
    start_halte = request.args.get('start_halte')
    end_halte = request.args.get('end_halte')

    logging.debug(f"Request received: start={start}, end={end}, start_halte={start_halte}, end_halte={end_halte}")

    if start not in nodes or end not in nodes:
        return jsonify({"error": "Invalid start or end location"}), 400
    
    if not start_halte or not end_halte:
        return jsonify({"error": "Start halte and end halte are required"}), 400

    path = a_star_search(start, end)
    if path is None:
        path = a_star_search(end, start)
        if path is not None:
            path = path[::-1]

    if path is None:
        return jsonify({"error": "Route not found"}), 404
    
    routeStops = [
    {
        "city": row["City"],
        "coords": [row["Coords1"], row["Coords2"]],
        "halte": row["Halte"]
    }
    for _, row in df.iterrows()
    ]

    

    halte_route = get_halte_route(path, start_halte, end_halte, routeStops)
    logging.debug(f"Halte route: {halte_route}")
    return jsonify({
        "route": path,
        "halte_route": halte_route
    })


if __name__ == '__main__':
    app.run(debug=True)
