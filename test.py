import json
import os

def Bot_response(data, template_type):
    def load_templates(template_type):
        template_file = f"{template_type}_templates.json"
        template_path = os.path.join('template', template_file)
        try:
            with open(template_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Template file {template_file} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {template_file}.")
            return {}
    
    template_data = load_templates(template_type)
    templates = template_data.get('templates', {})
    keys = template_data.get('keys', [])
    
    responses = []
    for key in keys:
        if key in data and data[key] is not None:
            response_template = templates.get(key, f"{key.capitalize()}: {{{key}}}")
            value = data[key]
            if isinstance(value, list):  # Handle list by joining its elements
                value = ", ".join(value)
            response = response_template.format(**{key: value})  # Use unpacking to pass key dynamically
            responses.append(response)

    return " ".join(responses) if responses else "No details are available."

if __name__ == "__main__":
    response_data = {
        "brief": "Dinner",
        "time": "5 PM",
        "place": "Grand Central Cafe",
        "people": ["David", "Lixi"],
        "date": "today"
    }
    formatted_response = Bot_response(response_data, 'meal')
    print(formatted_response)
