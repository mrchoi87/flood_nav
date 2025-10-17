from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
from shapely.geometry import Polygon, Point
import json

app = Flask(__name__)

# 지도와 도로망 설정
place = "종로구, 서울특별시, 대한민국"
G = ox.graph_from_place(place, network_type="drive")
nodes = list(G.nodes(data=True))

# 파이어베이스 초기화
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time

cred = credentials.Certificate('floodnavi-f4f2e-firebase-adminsdk-fbsvc-1475fb449d.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://floodnavi-f4f2e-default-rtdb.firebaseio.com/'
})
locations_ref = db.reference('locations')

current_data = locations_ref.get()
# locations_ref.update( {2 : [37, 127] } )
if current_data is None:       
    locations_ref.set({})

# 침수 노드 확인 및 DB업데이트 함수
def fnodes_update(flood_polygons):    
    # 1. 침수 폴리곤에서 침수 노드 확인
    flooded_nodes = []
    for node_id, node_data in G.nodes(data=True):
        pt = Point(node_data['x'], node_data['y'])  # (lon, lat)
        # print(node_data['x'], node_data['y'])
        # for poly in flood_polygons:
        #     if pt.within(poly):        
        #         flooded_nodes.append( [node_id, node_data['x'], node_data['y']] )
        #         break
        if pt.within(flood_polygons):
            flooded_nodes.append( [node_id, node_data['y'], node_data['x']] )

    # 2. 침수 노드 파이어베이스 업데이트
    # # 현재 데이터(값) 읽기
    # current_data = locations_ref.get()
    # current_node_ids = list(current_data.keys())    
    # # id가 포함되지 않았다면 추가하기
    # for id, x, y in flooded_nodes:
    #     if id not in current_node_ids:
    #         locations_ref.update( {id : {x, y}} )
   
    for id, y, x in flooded_nodes:    
        locations_ref.update( {id : [y, x] } )

# # 침수지역 저장
# flood_polygons = []

@app.route('/')
def index():
    nodes_json = json.dumps([(node_data['y'], node_data['x']) for node_id, node_data in nodes])

    current_data = locations_ref.get()
    fnodes_json = json.dumps(list(current_data.values()))
    #db에서 {x,y}를 가져오기
    #json.dumps : dict 객체 -> stirng  

    return render_template("index.html", nodes_json=json.loads(nodes_json), fnodes_json=json.loads(fnodes_json) )

@app.route('/add_flood', methods=['POST'])
def add_flood():
    data = request.get_json()
    poly_coords = [(pt[1], pt[0]) for pt in data]
    poly = Polygon(poly_coords)
    
    # flood_polygons.append(poly) #침수 폴리곤

    fnodes_update(poly)

    return jsonify(success=True)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    start = tuple(data['start'])
    end = tuple(data['end'])

    # G에서 노드 선택
    start_node = ox.distance.nearest_nodes(G, start[1], start[0])
    end_node = ox.distance.nearest_nodes(G, end[1], end[0])

    # # ✅ 침수지역에 포함된 노드 제거
    # flooded_nodes = []
    # for node_id, node_data in G.nodes(data=True):
    #     pt = Point(node_data['x'], node_data['y'])  # (lon, lat)
    #     # print(node_data['x'], node_data['y'])
    #     for poly in flood_polygons:
    #         if pt.within(poly):        
    #             flooded_nodes.append(node_id)
    #             break
    # # print(flooded_nodes)

    current_data = locations_ref.get()
    current_node_ids = list(map(int, current_data.keys()) )   
    print(current_node_ids)
    G_temp = G.copy()
    G_temp.remove_nodes_from(current_node_ids)

    # ✅ 경로 계산
    try:
        route = nx.shortest_path(G_temp, start_node, end_node, weight='length')
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
        return jsonify(route=route_coords)
    except nx.NetworkXNoPath:
        return jsonify(error="경로 없음"), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
