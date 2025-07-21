from django import template
import json

register = template.Library()

@register.filter
def format_changes(changes):
    try:
        changes_dict = json.loads(changes)
        if not isinstance(changes_dict, dict):
            return changes
        
        formatted_changes = []
        for key, value in changes_dict.items():
            if key == 'csrfmiddlewaretoken':
                continue
            
            old_value, new_value = value
            
            # Handle cases where values might be lists
            if isinstance(old_value, list):
                old_value = ', '.join(map(str, old_value))
            if isinstance(new_value, list):
                new_value = ', '.join(map(str, new_value))

            # Improve readability for specific fields
            key_display = key.replace('_', ' ').title()

            if old_value is None or old_value == '':
                formatted_changes.append(f"Set {key_display} to '{new_value}'")
            else:
                formatted_changes.append(f"Changed {key_display} from '{old_value}' to '{new_value}'")
                
        return "\n".join(formatted_changes)
    except (json.JSONDecodeError, TypeError, ValueError):
        return changes
