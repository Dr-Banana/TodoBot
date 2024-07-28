import json
import uuid
import os
import requests
from chatterbot import ChatBot
from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement

class AWSLambdaAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        self.api_url = kwargs.get('api_url')
        self.action = kwargs.get('action', "predict")
        self.user_id = kwargs.get('user_id', str(uuid.uuid4()))
        self.event_id = kwargs.get('event_id', str(uuid.uuid4()))
        self.json_content = kwargs.get('json_content', {})

    def can_process(self, statement):
        return True

    def process(self, input_statement, additional_response_selection_parameters):
        request_data = {
            "action": self.action,
            "Input_text": input_statement.text,
            "UserID": self.user_id,
            "EventID": self.event_id,
            "Json_content": json.dumps(self.json_content)
        }

        try:
            response = requests.post(self.api_url, data=json.dumps(request_data))
            response.raise_for_status()
            api_response = response.json()
            print(api_response)
            try:
                content = self.process_json(api_response)
            except Exception as e:
                content = api_response
            
            if not content:
                raise ValueError("API response does not contain expected content")
            
            if self.action == 'update':
                print(content)
                self.json_content.update(content)
                content = json.dumps(self.json_content)

            confidence = 1

            return Statement(text=content, confidence=confidence)

        except requests.RequestException as e:
            print(f"Error calling API: {e}")
            return Statement(text="I'm sorry, I'm having trouble processing your request right now.", confidence=0)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing API response: {e}")
            return Statement(text="I'm sorry, I received an unexpected response. Please try again later.", confidence=0)

    def process_json(self, llama_output):
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

    def update_json(self, original, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and "add" in value:
                original[key] = original.get(key, []) + value["add"]
            elif isinstance(value, dict) and "modify" in value:
                # 处理部分修改的逻辑
                pass
            else:
                original[key] = value
        return original


# 创建ChatBot实例
json_file = {"brief": "Tonight shopping", "time": None, "place": "Ralphs", "people": "Me", "date": "today", "items": ["potato", "green onions"]}
chatbot = ChatBot(
    'MyAWSBot',
    logic_adapters=[
        {
            'import_path': __name__ + '.AWSLambdaAdapter',
            'api_url': 'https://6inctbtbvk.execute-api.us-east-1.amazonaws.com/dev/UserDataProcessingFunction',
            'action': "update",
            'user_id': '1e026504-b625-4738-9e5d-e472c41510e4',
            'event_id': '1e026504-b625-4738-9e5d-e472c41510e4',
            "json_content": json_file
        }
    ]
)

# 主交互循环
print("Chat with the bot (type 'quit' to exit):")
while True:
    user_input = input("You: ")
    if user_input.lower() == 'quit':
        break
    
    response = chatbot.get_response(user_input)
    print(f"Bot: {response}")