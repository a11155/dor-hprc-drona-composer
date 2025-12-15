---
sidebar_position: 2
---

# Form Components

Documentation for all form components in the Drona Composer system. Components are used in JSON schema files by specifying the appropriate `type` field.

## AutocompleteSelect

A dynamic search-based dropdown component that fetches options as you type. Uses a retriever script to dynamically search for and display matching options based on user input.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `retriever - Path to the script that fetches search results` (string) - 
- `placeholder` (string, optional) - Placeholder text shown in the input field
- `value` (object, optional) - Default/initial selected option (object with value and label)
- `help` (string, optional) - Help text displayed below the input
- `showAddMore=false` (boolean, optional) - Whether to show an add more button

### Example
```json
// Dynamic search dropdown
{
"type": "autocompleteSelect",
"name": "institution",
"label": "AutocompleteSelect",
"retriever": "retrievers/institution_search.sh",
"placeholder": "Search for an institution...",
"help": "Type at least 2 characters to search for institutions"
}
/
```

*Source: `src/schemaRendering/schemaElements/AutocompleteSelect.js`*

---

## Checkbox

A checkbox input component that returns a specified value when checked and an empty string when unchecked. The checkbox value is customizable and defaults to "Yes" if not specified.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value="Yes"` (string, optional) - Value to return when the checkbox is checked (defaults to "Yes")
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Basic checkbox input
{
"type": "checkbox",
"name": "agreeToTerms",
"label": "Checkbox",
"value": "Yes",
"help": "Toggle input that returns a value when checked"
}
/
```

*Source: `src/schemaRendering/schemaElements/Checkbox.js`*

---

## CollapsibleRowContainer

A collapsible container component that organizes form fields in a horizontal row. Features a header with a toggle button to show/hide the content, making complex forms more manageable. Each child element is rendered by the FieldRenderer component in a 100% width layout.

### Properties
- `elements - Object of field configuration objects to be rendered in the container` (Object) - 
- `title="Collapsible Row Container"` (string, optional) - Title displayed in the container header

### Example
```json
// Collapsible container with multiple form elements
{
"type": "collapsibleRowContainer",
"title": "Personal Information",
"elements": {
"firstName": {
"type": "text",
"name": "firstName",
"label": "First Name",
"placeholder": "Enter first name"
},
"lastName": {
"type": "text",
"name": "lastName",
"label": "Last Name",
"placeholder": "Enter last name"
},
"email": {
"type": "text",
"name": "email",
"label": "Email Address",
"placeholder": "Enter email address"
}
}
}
/
```

*Source: `src/schemaRendering/schemaElements/CollapsibleContainer.js`*

---

## DynamicSelect

A dropdown select component that dynamically loads its options from a retriever script. Handles loading states, unavailable options, and provides visual feedback when selected values become invalid. Supports dynamic parameters from form values.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `retriever - Path to the script that retrieves the select options` (string) - 
- `retrieverParams` (Object, optional) - Parameters passed to the script as environment variables, values with $ prefix will be replaced with form values
- `value` (Object, optional) - Default/initial selected option (object with value and label)
- `options` (Array, optional) - Initial options array, may be overridden by retriever
- `help` (string, optional) - Help text displayed below the input
- `showAddMore=false` (boolean, optional) - Whether to show an add more button

### Examples
#### Example 1
```json
// Dynamic select with options loaded from a retriever
{
"type": "dynamicSelect",
"name": "computeNode",
"label": "DynamicSelect",
"retriever": "retrievers/compute_nodes.sh",
"help": "Select a compute node (options loaded dynamically)"
}
```

#### Example 2
```json
// Dynamic select with parameters from form values
{
"type": "dynamicSelect",
"name": "serverList",
"label": "Available Servers",
"retriever": "retrievers/servers_by_region.sh",
"retrieverParams": { "region": "$selectedRegion", "type": "production" },
"help": "Servers will update based on selected region"
}
/
```

*Source: `src/schemaRendering/schemaElements/DynamicSelect.js`*

---

## Hidden

Executes dynamic scripts without any visual output. Takes no space and displays nothing, but can execute retriever scripts in the background for side effects.

### Properties
- `name - Component name (required but not visible)` (string) - 
- `value` (string, optional) - Static value (used when no retriever is specified)
- `retriever` (string, optional) - Path to the script file to execute (for dynamic execution)
- `retrieverParams` (Object, optional) - Parameters passed to the script as environment variables
- `refreshInterval` (number, optional) - Auto-execution interval in seconds
- `setError` (function, optional) - Function to handle errors during script execution

### Examples
#### Example 1
```json
// Execute a script when form values change
{
"type": "hidden",
"name": "backgroundProcess",
"retriever": "retrievers/update_location.sh",
"retrieverParams": { "jobName": "$name" },
"refreshInterval": 5
}
```

#### Example 2
```json
// Static value execution (no dynamic script)
{
"type": "hidden",
"name": "staticAction",
"value": "some_static_value"
}
/
```

*Source: `src/schemaRendering/schemaElements/Hidden.js`*

---

## Module

A module selection component that allows users to search and select software modules from different toolchains. Features autocomplete suggestions from a server, toolchain selection, and visual representation of selected modules as removable badges.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value` (string, optional) - Default/initial value as space-separated list of modules
- `toolchains - Array of toolchain options, each with value and label properties` (Array) - 
- `toolchainName="toolchain"` (string, optional) - Name for the toolchain select input
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Module selection component with multiple toolchains
{
"type": "module",
"name": "moduleList",
"label": "Module",
"value": "gcc/9.3.0 openmpi/4.0.5",
"toolchains": [
{ "value": "modules", "label": "Modules" },
{ "value": "lmod-gcc", "label": "GCC Modules" },
{ "value": "lmod-intel", "label": "Intel Modules" }
],
"toolchainName": "toolchain",
"help": "Search and select software modules for your environment"
}
/
```

*Source: `src/schemaRendering/schemaElements/Module.js`*

---

## Number

A numeric input field component for collecting numerical values. Supports minimum, maximum, and step value constraints.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value` (number, optional) - Default/initial value for the input
- `min` (number, optional) - Minimum allowed value
- `max` (number, optional) - Maximum allowed value
- `step=1` (number, optional) - Step value for incrementing/decrementing
- `placeholder` (string, optional) - Placeholder text shown when the field is empty
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Basic number input
{
"type": "number",
"name": "quantity",
"label": "Number",
"value": 5,
"min": 0,
"max": 100,
"step": 1,
"placeholder": "Enter a number",
"help": "Numeric input with min/max constraints"
}
/
```

*Source: `src/schemaRendering/schemaElements/Number.js`*

---

## Picker

A file and directory picker component that allows users to browse and select files or directories from both local and remote locations. Features a modal browser interface for navigating directory structures.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `localLabel - Label for the local file browser button` (string) - 
- `remoteLabel` (string, optional) - Label for remote file upload button (if omitted, remote upload option isn't shown)
- `showFiles="false"` (string|boolean, optional) - Whether to show files in directory listings ("true" or "false")
- `defaultLocation` (string, optional) - Default path to show in the input field
- `defaultPaths` (Object, optional) - Custom paths to show as quick access buttons (key:label, value:path)
- `useHPCDefaultPaths=true` (boolean, optional) - Whether to use system default paths
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// File/directory picker with both local and remote options
{
"type": "picker",
"name": "outputLocation",
"label": "Picker",
"localLabel": "Browse Directories",
"remoteLabel": "Upload File",
"showFiles": "true",
"defaultLocation": "$HOME",
"defaultPaths": {
"HomeCustom": "$HOME"
},
"useHPCDefaultPaths": true,
"help": "Select a file or directory location"
}
/
```

*Source: `src/schemaRendering/schemaElements/Picker.js`*

---

## RadioGroup

A radio button group component that allows users to select a single option from a list of choices. Displays options horizontally with their labels.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `options - Array of option objects, each with value and label properties` (Array) - 
- `value` (string, optional) - Default/initial selected value
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Radio button group with multiple options
{
"type": "radioGroup",
"name": "priority",
"label": "RadioGroup",
"options": [
{ "value": "low", "label": "Low" },
{ "value": "medium", "label": "Medium" },
{ "value": "high", "label": "High" }
],
"value": "medium",
"help": "Select one option from multiple choices"
}
/
```

*Source: `src/schemaRendering/schemaElements/RadioGroup.js`*

---

## RowContainer

A layout component that organizes form fields in a horizontal row. It wraps multiple form elements in a responsive grid layout, with each child element rendered by the FieldRenderer component in a column format.

### Properties
- `elements - Array of field configuration objects to be rendered in the row` (Array) - 

### Example
```json
// Row with multiple text fields
{
"type": "rowContainer",
"elements": {
"element1": {
"type": "text",
"name": "element1",
"label": "rowContainer1",
"placeholder": "Enter text"
},
"element2": {
"type": "text",
"name": "element1",
"label": "rowContainer1",
"placeholder": "Enter text"
},
"element3": {
"type": "text",
"name": "element1",
"label": "rowContainer1",
"placeholder": "Enter text"
}
}
}
/
```

*Source: `src/schemaRendering/schemaElements/RowContainer.js`*

---

## Select

A dropdown select component based on react-select that provides a customizable selection interface with support for styled options and an optional "add more" button.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `options - Array of option objects, each with value and label properties` (Array) - 
- `value` (Object, optional) - Default/initial selected option (object with value and label)
- `help` (string, optional) - Help text displayed below the input
- `showAddMore=false` (boolean, optional) - Whether to show an add more button

### Example
```json
// Basic dropdown select
{
"type": "select",
"name": "category",
"label": "Select",
"options": [
{ "value": "option1", "label": "Option 1" },
{ "value": "option2", "label": "Option 2" },
{ "value": "option3", "label": "Option 3" }
],
"value": { "value": "option1", "label": "Option 1" },
"help": "Select one option from the dropdown"
}
/
```

*Source: `src/schemaRendering/schemaElements/Select.js`*

---

## StaticText

Displays static or dynamically fetched text content. Can show plain text or HTML content with options for dynamic content retrieval using script files, auto-refreshing, and manual refresh controls.

### Properties
- `name - Input field name` (string) - 
- `label` (string, optional) - Display label for the field
- `labelOnTop=false` (boolean, optional) - Whether to display label above the content
- `help` (string, optional) - Help text displayed below the content
- `value` (string, optional) - Static text content (used when isDynamic is false)
- `isDynamic=false` (boolean, optional) - Whether content should be fetched from a script retriever
- `retriever` (string, optional) - Path to the script file that will generate dynamic content
- `retrieverParams` (Object, optional) - Parameters passed to the script as environment variables, values with $ prefix will be replaced with form values
- `allowHtml=false` (boolean, optional) - Whether to render content as HTML using dangerouslySetInnerHTML
- `showRefreshButton=false` (boolean, optional) - Whether to show a manual refresh button for dynamic content
- `refreshInterval` (number, optional) - Auto-refresh interval in seconds
- `isHeading=false` (boolean, optional) - Whether to style the text as a heading with larger, bold font
- `setError` (function, optional) - Function to handle errors during content fetching

### Examples
#### Example 1
```json
// Basic static text
{
"type": "staticText",
"name": "infoText",
"label": "Information",
"value": "This is some static text",
"help": "Simple static text display"
}
```

#### Example 2
```json
// Dynamic text that fetches from a script retriever
{
"type": "staticText",
"name": "dynamicContent",
"label": "Script Output",
"isDynamic": true,
"retriever": "retrievers/text_retriever.sh",
"retrieverParams": { "id": "$userId" },
"showRefreshButton": true
}
```

#### Example 3
```json
// Dynamic HTML content with auto-refresh
{
"type": "staticText",
"name": "liveHtmlContent",
"label": "Server Status",
"isDynamic": true,
"retriever": "retrievers/server_status.sh",
"allowHtml": true,
"refreshInterval": 30
}
/
```

*Source: `src/schemaRendering/schemaElements/StaticText.js`*

---

## Text

A standard text input field component for collecting single-line text input. Provides form control with label, help text, and placeholder support.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value` (string, optional) - Default/initial value for the input
- `placeholder` (string, optional) - Placeholder text shown when the field is empty
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Basic text input
{
"type": "text",
"name": "userName",
"label": "Text",
"value": "defaultValue",
"placeholder": "Enter your text here",
"help": "Standard single-line text input field"
}
/
```

*Source: `src/schemaRendering/schemaElements/Text.js`*

---

## TextArea

A multi-line text input field component for collecting longer text content. Provides an expandable text area with adjustable number of rows.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value` (string, optional) - Default/initial value for the input
- `rows=4` (number, optional) - Number of visible text rows
- `placeholder` (string, optional) - Placeholder text shown when the field is empty
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Basic textarea input
{
"type": "textarea",
"name": "description",
"label": "TextArea",
"value": "This is a default value with multiple lines of text.\nThis is the second line.",
"rows": 6,
"placeholder": "Enter multi-line text here",
"help": "Multi-line text input for longer content"
}
/
```

*Source: `src/schemaRendering/schemaElements/TextArea.js`*

---

## Time

A time duration input component that allows users to specify time periods using separate days, hours, and minutes fields. The component internally converts these values to a combined "hours:minutes" format.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value` (string, optional) - Default/initial value in format "HH:MM" where HH includes days converted to hours
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Time duration input with separate day/hour/minute fields
{
"type": "time",
"name": "jobDuration",
"label": "Time",
"value": "36:30",
"help": "Specify a time duration in days, hours, and minutes"
}
/
```

*Source: `src/schemaRendering/schemaElements/Time.js`*

---

## Unit

A compound input component that combines a numeric value with a unit selector. Useful for inputs like memory size (GB, MB), time duration (hours, minutes), or any quantity that requires both a number and unit.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value` (string, optional) - Default/initial value in format "numberunit" (e.g., "16GB")
- `units - Array of unit options, each with value and label properties` (Array) - 
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// Memory size input with unit selection
{
"type": "unit",
"name": "memorySize",
"label": "Unit",
"value": "16GB",
"units": [
{ "value": "MB", "label": "MB" },
{ "value": "GB", "label": "GB" },
{ "value": "TB", "label": "TB" }
],
"help": "Select a numeric value with units"
}
/
```

*Source: `src/schemaRendering/schemaElements/Unit.js`*

---

## Uploader

A file and directory uploader component that allows users to select and upload individual files or entire directories. Displays a list of uploaded files and supports removal of files.

### Properties
- `name - Input field name, used for form submission` (string) - 
- `label` (string, optional) - Display label for the field
- `value` (Array|string, optional) - Default/initial value, can be array of file objects or JSON string
- `multiple=false` (boolean, optional) - Whether multiple file selection is allowed
- `acceptedFileTypes` (Array, optional) - Array of MIME types or file extensions to accept
- `help` (string, optional) - Help text displayed below the input

### Example
```json
// File and directory uploader
{
"type": "uploader",
"name": "dataFiles",
"label": "Uploader",
"multiple": true,
"acceptedFileTypes": ["text/*", "application/json", ".csv"],
"help": "Upload files or directories with support for multiple file selection"
}
/
```

*Source: `src/schemaRendering/schemaElements/Uploader.js`*

---


