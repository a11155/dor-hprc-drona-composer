import React, { useState } from 'react';
import MultiPaneTextArea from './MultiPaneTextArea';
import { usePaneManagement } from './hooks/usePaneManagement';
import { useEditorSplits } from './hooks/useEditorSplits';

const AlertBlock = ({ messages, type, styles }) => {
  const [isVisible, setIsVisible] = useState(true);
  const filteredMessages = messages?.filter(msg => msg.type === type) || [];

  if (!isVisible || filteredMessages.length === 0) return null;

  const alertTypes = {
    error: { className: 'alert alert-danger', title: 'Errors:' },
    warning: { className: 'alert alert-warning', title: 'Warnings:' },
    note: { className: 'alert alert-info', title: 'Notes:' }
  };

  const config = alertTypes[type];
  if (!config) return null;

  return (
    <div className={config.className} style={styles.messageAlert}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <h6 className="alert-heading" style={styles.alertTitle}>{config.title}</h6>
        <button
          onClick={() => setIsVisible(false)}
          style={{ background: 'none', border: 'none', fontSize: '18px', fontWeight: 'bold', cursor: 'pointer', padding: '0', marginLeft: '10px', opacity: 0.6, lineHeight: 1 }}
          onMouseOver={(e) => e.target.style.opacity = 1}
          onMouseOut={(e) => e.target.style.opacity = 0.6}
        >×</button>
      </div>
      <ul style={styles.alertList}>
        {filteredMessages.map((message, index) => (
          <li key={message.id || index} style={styles.alertItem}>{message.text}</li>
        ))}
      </ul>
    </div>
  );
};

const columnHeaderStyle = {
  display: 'flex',
  alignItems: 'center',
  backgroundColor: '#f0f0f0',
  borderBottom: '1px solid #dee2e6',
  padding: '0 6px',
  height: '36px',
  gap: '3px',
  flexShrink: 0,
  overflow: 'hidden',
};

const makeTabStyle = (isActive) => ({
  padding: '3px 10px',
  fontSize: '12px',
  fontWeight: isActive ? '600' : '400',
  color: isActive ? '#500000' : '#6c757d',
  backgroundColor: isActive ? 'white' : 'transparent',
  border: `1px solid ${isActive ? '#dee2e6' : 'transparent'}`,
  borderRadius: '3px',
  cursor: 'pointer',
  whiteSpace: 'nowrap',
  flexShrink: 0,
  lineHeight: '1.2',
});

const actionBtnStyle = {
  padding: '2px 7px',
  fontSize: '13px',
  color: '#6c757d',
  backgroundColor: 'transparent',
  border: '1px solid transparent',
  borderRadius: '3px',
  cursor: 'pointer',
  flexShrink: 0,
  lineHeight: 1,
};

const SplitColumnHeader = ({ split, splits, sortedPanes, onSetActivePane, onAddSplit, onRemoveSplit, splitIndex }) => (
  <div style={columnHeaderStyle}>
    <div style={{ display: 'flex', gap: '3px', overflowX: 'auto', flex: 1, alignItems: 'center', scrollbarWidth: 'none' }}>
      {sortedPanes.map((pane, idx) => (
        <button
          key={idx}
          style={makeTabStyle(split.activePaneIndex === idx)}
          onClick={() => onSetActivePane(split.id, idx)}
        >
          {pane.preview_name}
        </button>
      ))}
    </div>
    <button
      style={actionBtnStyle}
      onClick={() => onAddSplit(splitIndex, split.activePaneIndex)}
      title="Split editor right"
      onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#e2e2e2'}
      onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
    >
      ⊞
    </button>
    {splits.length > 1 && (
      <button
        style={actionBtnStyle}
        onClick={() => onRemoveSplit(split.id)}
        title="Close split"
        onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#fee'; e.currentTarget.style.color = '#c00'; }}
        onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#6c757d'; }}
      >
        ✕
      </button>
    )}
  </div>
);

const SplitResizeHandle = ({ index, isResizing, onMouseDown }) => (
  <div
    style={{
      width: '4px',
      cursor: 'ew-resize',
      backgroundColor: isResizing ? '#500000' : '#dee2e6',
      flexShrink: 0,
      transition: 'background-color 0.15s',
    }}
    onMouseDown={(e) => onMouseDown(index, e)}
    onMouseOver={(e) => { if (!isResizing) e.currentTarget.style.backgroundColor = '#adb5bd'; }}
    onMouseOut={(e) => { if (!isResizing) e.currentTarget.style.backgroundColor = isResizing ? '#500000' : '#dee2e6'; }}
  />
);

const PreviewPanel = ({
  leftWidth,
  messages,
  multiPaneRef,
  panes,
  setPanes,
  styles,
}) => {
  const { sortedPanes } = usePaneManagement(panes);
  const { splits, widths, resizingHandle, containerRef, addSplit, removeSplit, setActivePaneForSplit, handleResizeStart } = useEditorSplits();

  const hasMessages = messages?.some(m => ['error', 'warning', 'note'].includes(m.type));

  return (
    <div style={{ ...styles.leftPane, width: `${leftWidth}%`, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {hasMessages && (
        <div style={{ padding: '0.5rem 1rem', flexShrink: 0 }}>
          <AlertBlock messages={messages} type="error" styles={styles} />
          <AlertBlock messages={messages} type="warning" styles={styles} />
          <AlertBlock messages={messages} type="note" styles={styles} />
        </div>
      )}

      <div ref={containerRef} style={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {splits.map((split, splitIndex) => (
          <React.Fragment key={split.id}>
            <div style={{ display: 'flex', flexDirection: 'column', width: `${widths[splitIndex]}%`, overflow: 'hidden', minWidth: '150px' }}>
              <SplitColumnHeader
                split={split}
                splits={splits}
                sortedPanes={sortedPanes}
                onSetActivePane={setActivePaneForSplit}
                onAddSplit={addSplit}
                onRemoveSplit={removeSplit}
                splitIndex={splitIndex}
              />
              <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <MultiPaneTextArea
                  ref={splitIndex === 0 ? multiPaneRef : undefined}
                  panes={panes}
                  setPanes={setPanes}
                  isDisplayed={true}
                  activePane={split.activePaneIndex}
                  integrated={true}
                />
              </div>
            </div>
            {splitIndex < splits.length - 1 && (
              <SplitResizeHandle
                index={splitIndex}
                isResizing={resizingHandle === splitIndex}
                onMouseDown={handleResizeStart}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default PreviewPanel;
