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
        
        const r = await fetch(window.CONFIG_STATUS_URL, { credentials: "same-origin" });
        const j = await r.json();
        console.log("ConfigGate: status payload =", j);
        if (j.missing_config) {
          setMissing(true);
          setReason(j.reason || "Configuration not found.");
          setCurrentDir("");
        } else {
          setMissing(false);
          setCurrentDir(j.drona_dir || "");
        }
      } catch {
        setMissing(true);
        setReason("Failed to check configuration status.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleDronaPathChange(_index, selectedPath) {
    try {
      const resp = await fetch(window.CONFIG_SAVE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ drona_dir: selectedPath }),
      });
      const out = await resp.json();
      console.log("OUT:", out);
      if (resp.ok && out.status === "ok") {
          window.location.reload();
        }
    } catch (e) {
      alert(e.message || "Failed to save Drona directory.");
    }
  }

  if (loading || !missing) return null;
  // renders a small banner + opens your existing Picker modal
  return (
    <div className="alert alert-warning" style={{ marginBottom: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>Drona directory not set</div>
      <div style={{ marginBottom: 8 }}>{reason}</div>

      <Picker
        name="dronaDirPicker"
        label="Drona working directory"
        localLabel="Browse Directories"
        showFiles={false}
        defaultLocation={currentDir || "$HOME"}
        defaultPaths={{ Home: "$HOME", Scratch: "/scratch/user/$USER" }}
        useHPCDefaultPaths={true}
        onChange={() => {
            handleDronaPathChange(i, v);
        }}
        index={0}
      />
      <small className="text-muted">
        Pick the folder that will contain your Drona composer data (will create a folder called drona_composer inside chosen folder).
      </small>
    </div>
  );
}