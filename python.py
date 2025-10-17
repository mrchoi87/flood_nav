import json

# 파이썬 리스트
original_list = [{'id': 1, 'name': 'A'}, {'id': 2, 'name': 'B'}]

# 1. json.dumps()를 사용해 리스트를 '문자열'로 변환
json_string = json.dumps(original_list)
print(f"변환된 값의 타입: {type(json_string)}")
print(f"결과: {json_string}")

print("---")

# 2. json.loads()를 사용해 문자열을 다시 '리스트'로 변환
loaded_list = json.loads(json_string)
print(f"변환된 값의 타입: {type(loaded_list)}")
print(f"결과: {loaded_list}")