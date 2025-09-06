# Activity Description Feature Documentation

## Overview

The Activity Description Feature enhances the readability and usefulness of the Recent Activities section in the admin and staff dashboards by providing more detailed, human-readable descriptions of user actions instead of generic "Create/Update/Delete" messages.

## Implementation Details

### Template Filter

A new template filter called `format_activity_description` has been added to `settingsdb/templatetags/log_filters.py`. This filter takes a `TransactionLog` object and returns a formatted HTML description of the activity based on the model type and action performed.

```python
@register.filter
def format_activity_description(log):
    """Provides a more detailed and user-friendly description of the activity."""
    # Implementation details...
```

### Supported Models

The filter provides detailed descriptions for the following models:

1. **Student**
   - Create: "Created new student [Name] with ID [ID]"
   - Update: "Updated student [Name]"
   - Delete: "Deleted student [Name]"

2. **Payment**
   - Create: "Created new payment record with ID [ID], initial amount: ₹[Amount]"
   - Update: "Received EMI [Number] payment of ₹[Amount]" or "Updated payment record [ID]"

3. **Batch**
   - Create: "Created new batch [Name] with code [Code]"
   - Update: "Updated batch [Name]"
   - Delete: "Deleted batch [Name]"

4. **Placement**
   - Create: "Created new placement record with [Company]"
   - Update: "Updated placement status to [Status]" or "Updated placement record"

### Template Changes

The admin and staff dashboard templates have been updated to use the new filter:

```html
{% load log_filters %}
<span class="activity-description">{{ log|format_activity_description }}</span>
```

### CSS Styling

New CSS classes have been added to style the activity descriptions:

```css
.activity-description {
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.4;
}

.activity-description strong {
    color: var(--primary-blue-new);
}
```

## Usage

No additional configuration is needed. The feature automatically works with the existing `TransactionLog` model and data.

## Extending

To add support for additional models:

1. Open `settingsdb/templatetags/log_filters.py`
2. Locate the `format_activity_description` function
3. Add a new condition for your model type
4. Implement the formatting logic based on the model's fields and action type

Example:

```python
elif table_name == 'YourModel':
    # Extract relevant fields
    field1 = changes_dict.get('field1', '')
    field2 = changes_dict.get('field2', '')
    
    if action == 'Create':
        description = f"Created new YourModel with {field1}"
    elif action == 'Update':
        description = f"Updated YourModel {field1}"
    elif action == 'Delete':
        description = f"Deleted YourModel {field1}"
```