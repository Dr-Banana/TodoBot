import json

if __name__ == "__main__":
    def process_json(llama_output):
        try:
            content = llama_output[0]['generation']['content']
            
            # 过滤出JSON部分
            json_start = content.index('{')
            json_content = content[json_start:]
            
            # 解析JSON
            parsed_json = json.loads(json_content)
            return parsed_json
        except (ValueError, json.JSONDecodeError, IndexError) as e:
            raise RuntimeError(f"Error processing JSON: {str(e)}")
    
    def update_json(original, updates):
        if updates.get('modify'):
            for key, value in updates['modify'].items():
                original[key] = value

        # 处理添加操作，确保'add'键存在且不为None
        if updates.get('add'):
            for key, value in updates['add'].items():
                if key in original:
                    # 如果原来的值不是列表，则首先转换为列表
                    if not isinstance(original[key], list):
                        original[key] = [original[key]]
                    # 如果添加的值是列表，我们需要扩展原有的列表
                    if isinstance(value, list):
                        original[key].extend(value)
                    else:
                        # 如果不是列表，则直接添加
                        original[key].append(value)
                else:
                    # 如果键不存在于原始数据中，直接添加
                    original[key] = value

        # 处理删除操作，确保'delete'键存在且不为None
        if updates.get('delete'):
            for key in updates['delete']:
                if key in original:
                    # 将指定键的值设置为None
                    original[key] = None

        return original
    
    original = {'brief': 'Dinner at KFC', 'time': None, 'place': 'KFC', 'people': 'I', 'date': 'today'}
    updates = {'modify': {'time': '7 PM', 'date': 'today', 'brief' : 'Important Dinner tonight'}, 'add': {'people': ['Lixi', 'Xuanzhi'], 'time': '9PM'}, 'delete': ['place']}
    print(update_json(original, updates))
    