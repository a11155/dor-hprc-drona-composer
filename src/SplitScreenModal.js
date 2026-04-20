// SplitScreenModal.jsx
import React, { useRef, useEffect } from "react";
import { styles } from "./styles/SplitScreenModalStyles";
import { useResizeHandle } from "./hooks/useResizeHandle";
import PreviewPanel from "./PreviewPanel";
import StreamingPanel from "./StreamingPanel";

const ModalHeader = ({ title, isFullscreen, onFullscreen, onClose, onMinimize, styles }) => (
  <div style={styles.header}>
    <h5 style={styles.title}>{title}</h5>
    <div style={{ display: 'flex', gap: '0.5rem' }}>
      <button
        style={styles.minimizeButton}
        onClick={onFullscreen}
        onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
        onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
        title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
      >
        {isFullscreen ? '⤡' : '⤢'}
      </button>
      <button
        style={styles.minimizeButton}
        onClick={onMinimize}
        onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
        onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
        title="Minimize"
      >
        −
      </button>
      <button
        style={styles.closeButton}
        onClick={onClose}
        onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
        onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
        title="Close"
      >
        ×
      </button>
    </div>
  </div>
);

const ResizeHandle = ({ isResizing, onMouseDown, styles }) => (
  <div
    style={isResizing ? styles.resizeHandle.active : styles.resizeHandle.base}
    onMouseDown={onMouseDown}
    onMouseOver={(e) => { if (!isResizing) e.target.style.backgroundColor = '#adb5bd'; }}
    onMouseOut={(e) => { if (!isResizing) e.target.style.backgroundColor = '#dee2e6'; }}
    title="Drag to resize panes"
  >
    <div style={styles.resizeHandle.indicator} />
  </div>
);

const ModalFooter = ({ onClose, styles }) => (
  <div style={styles.footer}>
    <div style={styles.footerTip}>
      <strong>Tip:</strong> Configure your job on the left, then submit to see live output on the right.
      Drag the center divider to resize panes.
    </div>
    <div>
      <button
        type="submit"
        form="slurm-config-form"
        style={styles.button.primary}
        onMouseOver={(e) => e.target.style.backgroundColor = '#500000'}
        onMouseOut={(e) => e.target.style.backgroundColor = 'maroon'}
      >
        Submit Job
      </button>
      <button
        onClick={onClose}
        style={styles.button.secondary}
        onMouseOver={(e) => e.target.style.backgroundColor = '#545b62'}
        onMouseOut={(e) => e.target.style.backgroundColor = '#6c757d'}
      >
        Close
      </button>
    </div>
  </div>
);

const MinimizedModal = ({ onExpand, styles }) => (
  <div
    style={styles.minimizedContainer}
    onClick={onExpand}
    onMouseOver={(e) => e.target.style.transform = 'scale(1.1)'}
    onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
  >
    <div style={styles.minimizedIcon}>
      <span style={styles.minimizedText}>JC</span>
    </div>
  </div>
);

const SplitScreenModal = ({
  isOpen,
  onClose,
  messages,
  multiPaneRef,
  panes,
  setPanes,
  outputLines,
  htmlOutput,
  status,
  onSubmit,
  onMinimize: onMinimizeCallback,
  onExpand: onExpandCallback,
  forceMinimized = null
}) => {
  const contentRef = useRef(null);
  const modalRef = useRef(null);
  const [isMinimized, setIsMinimized] = React.useState(false);
  const [isFullscreen, setIsFullscreen] = React.useState(false);

  useEffect(() => {
    if (forceMinimized !== null) setIsMinimized(forceMinimized);
  }, [forceMinimized]);

  // ESC exits fullscreen (but not the modal itself)
  useEffect(() => {
    if (!isFullscreen) return;
    const onKey = (e) => { if (e.key === 'Escape') setIsFullscreen(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isFullscreen]);

  const { leftWidth, isResizing, handleMouseDown } = useResizeHandle(55);

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [outputLines, htmlOutput]);

  const handleMinimize = () => {
    setIsMinimized(true);
    if (onMinimizeCallback) onMinimizeCallback();
  };

  const handleExpand = () => {
    setIsMinimized(false);
    if (onExpandCallback) onExpandCallback();
  };

  if (!isOpen) return null;
  if (isMinimized) return <MinimizedModal onExpand={handleExpand} styles={styles} />;

  const overlayStyle = isFullscreen
    ? { position: 'fixed', inset: 0, zIndex: 1000 }
    : { ...styles.overlay };

  const modalStyle = isFullscreen
    ? { ...styles.modal, width: '100%', height: '100vh', maxWidth: 'none', maxHeight: '100vh', borderRadius: 0 }
    : styles.modal;

  return (
    <div style={overlayStyle} onClick={isFullscreen ? undefined : handleMinimize}>
      <div
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
        ref={modalRef}
        data-modal-ref
      >
        <ModalHeader
          title="Job Preview"
          isFullscreen={isFullscreen}
          onFullscreen={() => setIsFullscreen(f => !f)}
          onClose={onClose}
          onMinimize={handleMinimize}
          styles={styles}
        />

        <div style={styles.contentContainer}>
          <PreviewPanel
            leftWidth={leftWidth}
            messages={messages}
            multiPaneRef={multiPaneRef}
            panes={panes}
            setPanes={setPanes}
            styles={styles}
          />

          <ResizeHandle
            isResizing={isResizing}
            onMouseDown={handleMouseDown}
            styles={styles}
          />

          <StreamingPanel
            leftWidth={leftWidth}
            status={status}
            htmlOutput={htmlOutput}
            outputLines={outputLines}
            contentRef={contentRef}
            styles={styles}
          />
        </div>

        <ModalFooter onClose={onClose} styles={styles} />
      </div>
    </div>
  );
};

export default SplitScreenModal;
