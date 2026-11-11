import json

data = {"name": "张三", "age": 25}
print(type(data), data)
json_str = json.dumps(data, ensure_ascii=False)

print(type(json_str), json_str)

print(len(json_str))
print(json_str[0])
print(json_str.upper())