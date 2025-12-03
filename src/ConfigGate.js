import React, { useEffect, useState } from "react";
import Picker from "./schemaRendering/schemaElements/Picker";

export default function ConfigGate() {
  const [loading, setLoading] = useState(true);
  const [missing, setMissing] = useState(false);
  const [reason, setReason] = useState("");
  const [currentDir, setCurrentDir] = useState("");

  useEffect(() => {
    (async () => {
      try {
        if (!window.CONFIG_STATUS_URL) {
          console.error("ConfigGate: CONFIG_STATUS_URL is not defined on window");
          setMissing(true);
          setReason("Configuration status URL not defined.");
          setLoading(false);
          return;
        }
        const r = await fetch(window.CONFIG_STATUS_URL, { credentials: "same-origin" });
        const j = await r.json();
        if (j.missing_config) {
          setMissing(true);
          setReason(j.reason || "Configuration not found.");
          setCurrentDir(""); // fall back to $HOME in UI
        } else {
          setMissing(false);
          setCurrentDir(j.drona_dir || "");
        }
      } catch (e) {
        console.error("ConfigGate: status fetch failed:", e);
        setMissing(true);
        setReason("Failed to check configuration status.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleDronaPathChange(_index, selectedPath) {
      if (!selectedPath) { alert("No directory was selected."); return; }
      const resp = await fetch(window.CONFIG_SAVE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ drona_dir: selectedPath }),
      });
      const out = await resp.json().catch(() => ({}));
      if (resp.ok && out.status === "ok") {
        window.location.reload();
      } else {
        alert(out.message || out.error || `Save failed (${resp.status})`);
      }
    }

  if (loading || !missing) return null;

  return (
    <div className="alert alert-warning" style={{ marginBottom: 12 }}>
    <div style={{ fontWeight: 600, marginBottom: 6 }}>Drona directory not set</div>
    <div style={{ marginBottom: 8 }}>{reason}</div>

    <div className="drona-dir-picker">
      <Picker
        name="dronaDirPicker"
        label="Drona working directory"
        localLabel="Browse Directories"
        showFiles={false}
        defaultLocation={""}
        defaultPaths={{ Home: "/home/$USER", Scratch: "/scratch/user/$USER" }}
        useHPCDefaultPaths={true}
        onChange={(_, v) => handleDronaPathChange(_, v)}
        index={0}
      />
    </div>

    <small className="text-muted">
      Pick the folder that will contain your Drona composer data (will create a folder called drona_wfe inside chosen folder).
    </small>
  </div>
);
}
