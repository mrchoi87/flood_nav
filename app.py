from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
from shapely.geometry import Polygon, Point
import json
import os 

app = Flask(__name__)

# 지도와 도로망 설정
place = "용인시, 대한민국"
G = ox.graph_from_place(place, network_type="drive")
nodes = list(G.nodes(data=True))

# 파이어베이스 초기화
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time

# 파이어베이스 인증키 - 프로젝트에 포함됨
# cred = credentials.Certificate('floodnavi-f4f2e-firebase-adminsdk-fbsvc-1475fb449d.json')
# # 프로그램과 파이어베이스 db 연결
# firebase_admin.initialize_app(cred, {
#     'databaseURL': 'https://floodnavi-f4f2e-default-rtdb.firebaseio.com/'   # db 경로
# })

# # 연결된 db를 참조하는 객체 생성 locations_ref로 db를 사용
# locations_ref = db.reference('locations')   
# # db 데이터 모두 가져오기
# current_data = locations_ref.get()
# if current_data is None:       
#     locations_ref.set({})

# render 서버 업로드 시 활성화하는 코드입니다. 건들지 마시오.
cred_json_str = os.environ.get('FIREBASE_CREDENTIALS_JSON')

if cred_json_str:
    # 2. JSON 문자열을 딕셔너리로 로드
    cred_dict = json.loads(cred_json_str)
    
    # 3. 딕셔너리를 사용하여 인증 정보 객체 생성
    cred = credentials.Certificate(cred_dict) 

    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://floodnavi-f4f2e-default-rtdb.firebaseio.com/'
    })
    
    locations_ref = db.reference('locations')
    # 최초 실행 시 데이터 초기화 로직 유지
    if locations_ref.get() is None:
        locations_ref.set({})
    
else:
    # 배포 환경에서 키가 없으면 앱을 실행할 수 없습니다.
    raise EnvironmentError("FIREBASE_CREDENTIALS_JSON 환경 변수를 찾을 수 없습니다. (보안 키)")



# 침수 노드 확인 및 DB업데이트 함수
def fnodes_delete(flood_polygons):    
    # 선택된 폴리곤에서 노드 확인
    flooded_nodes = []
    for node_id, node_data in G.nodes(data=True):
        pt = Point(node_data['x'], node_data['y'])  # (lon, lat)
        if pt.within(flood_polygons):
            flooded_nodes.append( [node_id, node_data['y'], node_data['x']] )

    # print(flooded_nodes)

    # 파이어베이스에서 key값이 노드 아이디인 데이터 삭제
    for id, y, x in flooded_nodes:
        locations_ref.child(str(id)).delete()    

# 침수 노드 DB 등록 함수
def fnodes_update(flood_polygons):    
    # 선택된 폴리곤에서 노드 확인
    flooded_nodes = []
    for node_id, node_data in G.nodes(data=True):
        pt = Point(node_data['x'], node_data['y'])  # (lon, lat)
        if pt.within(flood_polygons):
            flooded_nodes.append( [node_id, node_data['y'], node_data['x']] )
    
    # 파이어베이스에 등록 json 구조 { key : value } -> { 노드 id : [위도, 경도] }
    for id, y, x in flooded_nodes:    
        locations_ref.update( {id : [y, x] } )


@app.route('/')
def index():
    # 전체 노드 정보 담기
    nodes_json = json.dumps([(node_data['y'], node_data['x']) for node_id, node_data in nodes])

    # 파이어베이스에서 침수 노드 정보 가져오기
    current_data = locations_ref.get()
    fnodes_json = json.dumps(list(current_data.values()))
    #db에서 {x,y}를 가져오기
    #json.dumps : dict 객체 -> stirng  

    # 브라우저 전연객체로 전달 nodes_json : 전체 노드 , fnode_json : 침수 노드
    return render_template("index.html", nodes_json=json.loads(nodes_json), fnodes_json=json.loads(fnodes_json) )

@app.route('/add_flood', methods=['POST'])
def add_flood():
    data = request.get_json()
    poly_coords = [(pt[1], pt[0]) for pt in data]
    poly = Polygon(poly_coords)
    
    # flood_polygons.append(poly) #침수 폴리곤

    fnodes_update(poly)

    return jsonify(success=True)

@app.route('/del_flood', methods=['POST'])
def del_flood():
    data = request.get_json()
    poly_coords = [(pt[1], pt[0]) for pt in data]
    poly = Polygon(poly_coords)

    fnodes_delete(poly)

    return jsonify(success=True)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    start = tuple(data['start'])
    end = tuple(data['end'])

    # G에서 노드 선택
    start_node = ox.distance.nearest_nodes(G, start[1], start[0])
    end_node = ox.distance.nearest_nodes(G, end[1], end[0])

    # # 침수지역에 포함된 노드 제거
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
