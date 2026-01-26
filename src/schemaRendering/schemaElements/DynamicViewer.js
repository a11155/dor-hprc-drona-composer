import React, { useState, useEffect, useRef, useCallback } from "react";
import FormElementWrapper from "../utils/FormElementWrapper";

const SECURITY_CONFIG = {
  MAX_MEMORY_MB: 150,
  MAX_CONSOLE_CALLS: 2000,

  APPROVED_SOURCES: [
    'cdn.jsdelivr.net',
    'unpkg.com',
    'cdnjs.cloudflare.com',
    '3dmol.csb.pitt.edu',
    'cdn.plot.ly',
    'files.rcsb.org',
    'd3js.org',
    'alphafold.ebi.ac.uk',
    'pubchem.ncbi.nlm.nih.gov',
    'rest.uniprot.org',
    'www.rcsb.org',
    'www.ebi.ac.uk',
  ],
};

// Validate CDN libraries before component mounts
function validateCDNs(cdnLibraries) {
  let libs = cdnLibraries || [];
  if (!Array.isArray(libs)) libs = [libs];

  if (libs.length === 0) return { valid: [], blocked: [] };

  const validLibs = [];
  const blockedLibs = [];

  libs.forEach(url => {
    try {
      const u = new URL(url);
      if (u.protocol !== 'https:') {
        blockedLibs.push({ url, reason: 'Non-HTTPS protocol not allowed' });
        return;
      }

      const isApproved = SECURITY_CONFIG.APPROVED_SOURCES.some(d =>
        u.hostname === d || u.hostname.endsWith('.' + d)
      );

      if (!isApproved) {
        blockedLibs.push({ url, reason: 'CDN domain not in approved list' });
        return;
      }

      validLibs.push(url);
    } catch (e) {
      blockedLibs.push({ url, reason: 'Invalid URL format' });
    }
  });

  return { valid: validLibs, blocked: blockedLibs };
}

function DynamicViewer(props) {
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState(null);
  const [securityBlock, setSecurityBlock] = useState(null);
  const iframeRef = useRef(null);
  const initializedRef = useRef(false);

  const config = props.value ?
    (typeof props.value === 'string' ? JSON.parse(props.value) : props.value) : {};

  // Validate CDNs immediately
  const cdnValidation = validateCDNs(config.cdnLibraries);
  const hasBlockedCDNs = cdnValidation.blocked.length > 0;

  useEffect(() => {
    // If CDNs were blocked, set blocked status immediately
    if (hasBlockedCDNs) {
      const reasons = cdnValidation.blocked.map(b => `${b.url}\n  → ${b.reason}`).join('\n\n');
      setSecurityBlock(`The following CDN libraries were blocked for security:\n\n${reasons}`);
      setStatus('blocked');
      return;
    }

    const handleMessage = (event) => {
      if (event.origin !== 'null' && event.origin !== window.location.origin) return;

      if (event.data.type === 'viewer-ready') {
        setStatus('ready');
      } else if (event.data.type === 'viewer-error') {
        setError(event.data.message);
        setStatus('error');
      } else if (event.data.type === 'security-block') {
        setSecurityBlock(event.data.reason);
        setStatus('blocked');
      }
    };

    window.addEventListener('message', handleMessage);

    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [hasBlockedCDNs, cdnValidation.blocked]);

  const setIframeRef = useCallback((node) => {
    if (node && !initializedRef.current && !hasBlockedCDNs) {
      iframeRef.current = node;
      initializedRef.current = true;
      setTimeout(() => initViewer(), 50);
    }
  }, [hasBlockedCDNs]);

  const initViewer = () => {
    if (!iframeRef.current) return;

    const html = generateHTML(config, cdnValidation.valid);
    if (!html) {
      setError('Failed to generate viewer HTML');
      setStatus('error');
      return;
    }

    iframeRef.current.srcdoc = html;
  };

  const generateHTML = (cfg, validLibs) => {
    const origins = [...new Set(validLibs.map(u => new URL(u).origin))].join(' ');
    const dataOrigins = SECURITY_CONFIG.APPROVED_SOURCES.map(d => `https://${d}`).join(' ');

    // Content Security Policy
    const csp = [
      "default-src 'none'",
      validLibs.length > 0 ? `script-src ${origins} 'unsafe-inline' 'unsafe-eval'` : "script-src 'unsafe-inline'",
      "style-src 'unsafe-inline'",
      `connect-src ${dataOrigins}`,
      `img-src data: blob: ${dataOrigins}`,
    ].join('; ');

    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <style>
    body { margin: 0; padding: 0; width: 100%; height: 100vh; overflow: hidden; }
    #viewer-container { width: 100%; height: 100%; }
    .security-block {
      color: #721c24;
      background: #f8d7da;
      border: 2px solid #f5c6cb;
      border-radius: 4px;
      padding: 20px;
      margin: 20px;
    }
  </style>
</head>
<body>
  <div id="viewer-container"></div>
  ${validLibs.map(u => `<script src="${u}"></script>`).join('\n  ')}
  <script>
    (function() {
      'use strict';
      const LIMITS = {
        maxConsole: ${SECURITY_CONFIG.MAX_CONSOLE_CALLS},
        maxMemMB: ${SECURITY_CONFIG.MAX_MEMORY_MB},
      };

      const state = { consoleCount: 0 };

      // Console rate limiting
      ['log','warn','error','info','debug'].forEach(m => {
        const orig = console[m];
        console[m] = function(...args) {
          state.consoleCount++;
          if (state.consoleCount === LIMITS.maxConsole + 1) {
            console.warn('Console rate limit reached (' + LIMITS.maxConsole + ' calls)');
          }
          if (state.consoleCount > LIMITS.maxConsole) return;
          orig.apply(console, args);
        };
      });

      // Memory monitoring
      let memoryWarningShown = false;
      setInterval(() => {
        if (performance.memory && !memoryWarningShown) {
          const mb = performance.memory.usedJSHeapSize / 1048576;
          if (mb > LIMITS.maxMemMB) {
            memoryWarningShown = true;
            console.warn('High memory usage: ' + mb.toFixed(0) + 'MB');
          }
        }
      }, 5000);

      const container = document.getElementById('viewer-container');
      const data = ${JSON.stringify(cfg.data || {})};
      const instanceRef = { current: null };

      // Basic error handling
      window.addEventListener('error', e => {
        const msg = e.message || 'Unknown error';
        if (!msg.includes('Script error')) {
          window.parent.postMessage({ type: 'viewer-error', message: msg }, '*');
        }
      });

      window.addEventListener('unhandledrejection', e => {
        const reason = e.reason?.message || String(e.reason);
        window.parent.postMessage({ type: 'viewer-error', message: reason }, '*');
      });

      (async function() {
        try {
          if (document.readyState === 'loading') {
            await new Promise(r => document.addEventListener('DOMContentLoaded', r));
          }
          await new Promise(r => setTimeout(r, 200));

          // Helper function for long-running operations to yield control
          window.yieldControl = async () => {
            await new Promise(r => setTimeout(r, 0));
          };

          ${cfg.initCode || 'console.log("No init code")'}

          window.parent.postMessage({ type: 'viewer-ready' }, '*');
        } catch (err) {
          const msg = err.message || 'Unknown error';
          container.innerHTML = '<div class="security-block"><strong>Error</strong><p>' + msg + '</p></div>';
          window.parent.postMessage({ type: 'viewer-error', message: err.message }, '*');
        }
      })();
    })();
  </script>
</body>
</html>`;
  };

  return (
    <FormElementWrapper {...props}>
      <div className="card">
        {config.title && (
          <div className="card-header bg-light">
            <h5 className="mb-0">{config.title}</h5>
            {config.description && <small className="text-muted d-block mt-1">{config.description}</small>}
          </div>
        )}

        <div className="card-body p-0" style={{ position: 'relative' }}>
          {status === 'loading' && (
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              backgroundColor: 'white', zIndex: 10
            }}>
              <div className="text-center">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <p className="mt-2 text-muted">Loading viewer...</p>
              </div>
            </div>
          )}

          {status === 'blocked' && (
            <div className="alert alert-warning m-3" role="alert">
              <h5 className="alert-heading">
                <i className="bi bi-shield-exclamation"></i> Security Block
              </h5>
              <hr />
              <pre className="mb-0" style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.9em' }}>
                {securityBlock}
              </pre>
            </div>
          )}

          {status === 'error' && (
            <div className="alert alert-danger m-3">
              <strong>Error:</strong> {error}
            </div>
          )}

          {!hasBlockedCDNs && (
            <iframe
              ref={setIframeRef}
              sandbox="allow-scripts"
              style={{
                width: "100%",
                height: config.height || "600px",
                border: "none",
                display: "block",
              }}
              title={config.title || "Dynamic Viewer"}
            />
          )}
        </div>

        {config.footer && (
          <div className="card-footer text-muted small">{config.footer}</div>
        )}

        <div className="card-footer bg-light border-top">
          <small className="text-muted d-flex align-items-center">
            <i className="bi bi-shield-check text-success me-2"></i>
	      <span>
      <strong>Warning:</strong> Do not enter passwords, credentials, or sensitive information here.</span>
          </small>
        </div>
      </div>
    </FormElementWrapper>
  );
}

export default DynamicViewer;
