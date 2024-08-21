import json
import data
import uuid
import os
import requests
from chatterbot import ChatBot
from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement

class AWSLambdaAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        self.action = kwargs.get('action', "predict")
        self.event_id = kwargs.get('event_id', str(uuid.uuid4()))
        self.api_url = self.get_api_url()
        self.user_id = self.get_user_id()
        self.json_content = {}

    def can_process(self, statement):
        return True
    
    def get_user_id(self):
        with open('data/user_id.json', 'r') as file:
            data = json.load(file)
            return data['user_id']
        
    def get_api_url(self):
        with open('data/api_url.json', 'r') as file:
            data = json.load(file)
            return data['api_url']
        
    def get_json_content(self):
        event_id = self.event_id
        local_folder_path = 'local_data'
        file_path = os.path.join(local_folder_path, f"{event_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        else:
            return {}
        
    def save_content_locally(self, content, filename):
        local_folder_path = 'local_data'
        if not os.path.exists(local_folder_path):
            os.makedirs(local_folder_path)
        with open(os.path.join(local_folder_path, filename), 'w') as file:
            json.dump(content, file, indent=4)

    def process(self, input_statement, additional_response_selection_parameters):
        if self.action == 'update': self.json_content = self.get_json_content()
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
            try:
                content = self.process_json(api_response)
            except Exception as e:
                content = api_response
            
            if not content:
                raise ValueError("API response does not contain expected content")
            
            if self.action == 'predict':
                filename = f"{self.event_id}.json"
                self.save_content_locally(content, filename)
            
            elif self.action == 'update':
                self.json_content = self.update_json(self.json_content, content)
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
            parsed_json = json.loads(content)
            return parsed_json
        except (ValueError, json.JSONDecodeError, IndexError) as e:
            raise RuntimeError(f"Error processing JSON: {str(e)}")

    def update_json(self, original, updates):
        if updates.get('add'):
            for key, value in updates['add'].items():
                if key in original and isinstance(original[key], list):
                    if isinstance(value, list):
                        original[key].extend(value)
                    else:
                        original[key].append(value)
                else:
                    original[key] = value

        if updates.get('delete'):
            for key, value in updates['delete'].items():
                if isinstance(original.get(key), list):
                    original[key] = [item for item in original[key] if item not in value]
                    if not original[key]:
                        original[key] = None
                elif key in original:
                    if key not in updates.get('add', {}):
                        original[key] = None

        return original

def mode_switch(event_id):
    """Determine whether to predict or update based on the file's existence and content."""
    local_folder_path = 'local_data'
    file_path = os.path.join(local_folder_path, f"{event_id}.json")
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
                if bool(data) and data != {}:
                    return "update"
        return "predict"
    except json.JSONDecodeError:
        return "predict"

if __name__ == "__main__":
    event_id = '1e026504-b625-4738-9e5d-e472c41510e4'
    action = mode_switch(event_id)
    chatbot = ChatBot(
        'TodoBot',
        logic_adapters=[
            {
                'import_path': __name__ + '.AWSLambdaAdapter',
                'action': action,
                'event_id': event_id,
                "json_content": None
            }
        ]
    )

    print("Chat with the bot (type 'quit' to exit):")
    while True:
        user_input = input("You: ")
        adapter = chatbot.logic_adapters[0]
        if user_input.lower() == 'quit':
            if isinstance(adapter, AWSLambdaAdapter):
                adapter.save_content_locally(adapter.json_content, f"{adapter.event_id}.json")
            break
        
        response = chatbot.get_response(user_input)
        print(f"Bot: {response}")

        new_action = mode_switch(event_id)
        if new_action != adapter.action:
            adapter.action = new_action