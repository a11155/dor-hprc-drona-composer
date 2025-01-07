import React, { useState, useEffect } from "react";
import FormElementWrapper from "../utils/FormElementWrapper";

function TextArea(props) {
  const [value, setValue] = useState(props.value || "");

  function handleValueChange(event) {
    setValue(event.target.value);
    if (props.onChange) props.onChange(props.index, event.target.value);
    if (props.onNameChange) props.onNameChange(event.target.value);
  }

  useEffect(() => {
    setValue(props.value || "");
  }, [props.value]);

  return (
    <FormElementWrapper
      labelOnTop={props.labelOnTop}
      name={props.name}
      label={props.label}
      help={props.help}
    >
      <textarea
        name={props.name}
        id={props.id}
        value={value}
        placeholder={props.placeholder}
        className="form-control"
        rows={props.rows || 4} // Default to 4 rows if not specified
        onChange={handleValueChange}
      />
    </FormElementWrapper>
  );
}

export default TextArea;
