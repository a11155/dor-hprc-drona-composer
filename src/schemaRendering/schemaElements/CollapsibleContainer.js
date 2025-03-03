import React, { useState } from "react";
import FieldRenderer from "../FieldRenderer";

function CollapsibleHeader({ title, isCollapsed, onToggle }) {
  return (
    <div style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "1rem",
      paddingBottom: "0.75rem",
      borderBottom: "1px solid #dee2e6"
    }}>
      <span style={{ fontSize: "1.25rem", fontWeight: "600" }}>{title}</span>
      <button
        onClick={onToggle}
        style={{
          padding: "0.5rem 1rem",
          backgroundColor: "#500000",
          color: "white",
          borderRadius: "0.25rem",
          border: "none",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          cursor: "pointer"
        }}
      >
        <span style={{ fontSize: "0.875rem" }}>
          {isCollapsed ? '▼' : '▲'}
        </span>
        <span>{isCollapsed ? 'Show' : 'Hide'} {title}</span>
      </button>
    </div>
  );
}

function CollapsibleRowContainer({
  elements,
  index,
  onChange,
  onFileChange,
  startingIndex,
  onSizeChange,
  currentValues,
  setError,
  title = "Collapsible Row Container",
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  function toggleCollapse(e) {
    e.preventDefault();
    e.stopPropagation();
    setIsCollapsed(prev => !prev);
  }
  
  return (
    <div style={{
      border: "1px solid #dee2e6",
      borderRadius: "0.25rem",
      padding: "1rem",
      marginBottom: "1rem"
    }}>
      <CollapsibleHeader
        title={title}
        isCollapsed={isCollapsed}
        onToggle={toggleCollapse}
      />
      
      <div style={{ display: isCollapsed ? 'none' : 'block' }}>
        <div style={{ marginTop: "1rem" }}>
          <FieldRenderer
            fields={elements}
            handleValueChange={onChange}
            onFileChange={onFileChange}
            labelOnTop
            fieldStyles="width: 100%"
            startingIndex={startingIndex}
            currentValues={currentValues}
            setError={setError}
          />
        </div>
      </div>
    </div>
  );
}

function CollapsibleColContainer({
  elements,
  index,
  onChange,
  onFileChange,
  startingIndex,
  onSizeChange,
  currentValues,
  setError,
  title = "Collapsible Column Container",
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  function toggleCollapse(e) {
    e.preventDefault();
    e.stopPropagation();
    setIsCollapsed(prev => !prev);
  }
  
  return (
    <div style={{
      border: "1px solid #dee2e6",
      borderRadius: "0.25rem",
      padding: "1rem",
      marginBottom: "1rem"
    }}>
      <CollapsibleHeader
        title={title}
        isCollapsed={isCollapsed}
        onToggle={toggleCollapse}
      />
      
      <div style={{ display: isCollapsed ? 'none' : 'block' }}>
        <div style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: "1rem",
          marginTop: "1rem"
        }}>
          <FieldRenderer
            fields={elements}
            handleValueChange={onChange}
            onFileChange={onFileChange}
            labelOnTop
            fieldStyles="width: 100%"
            startingIndex={startingIndex}
            currentValues={currentValues}
            setError={setError}
          />
        </div>
      </div>
    </div>
  );
}

export { CollapsibleRowContainer, CollapsibleColContainer };
