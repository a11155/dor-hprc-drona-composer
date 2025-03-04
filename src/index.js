import React, { useState, useEffect, useRef, createContext } from "react";
import ReactDOM from "react-dom";
import JobComposer from "./JobComposer";
import RerunPromptModal from "./RerunPromptModal";

export const GlobalFilesContext = createContext();


function App() {
  const [globalFiles, setGlobalFiles] = useState([]);
  const [environment, setEnvironment] = useState({ env: "", src: "" });
  const [fields, setFields] = useState({});
  const [jobScript, setJobScript] = useState("");
  const [warningMessages, setWarningMessages] = useState([]);

  const [panes, setPanes] = useState([{ title: "", name: "", content: "" }]);
  const [jobStatus, setJobStatus] = useState("new"); // new | rerun
  const [rerunInfo, setRerunInfo] = useState({});
  const [rerunOriginalName, setRerunOriginalName] = useState("");
 
  const [isRerunPromptOpen, setIsRerunPromptOpen] = useState(false);
  const [pendingRerunRow, setPendingRerunRow] = useState(null);
  const [showRerunModal, setShowRerunModal] = useState(false);

  const rerunPromptModalRef = useRef(null);

  const composerRef = useRef(null);
 

  const [fieldsLoadedResolver, setFieldsLoadedResolver] = useState(null);

  const formRef = useRef(null);
  const previewRef = useRef(null);
  const envModalRef = useRef(null);
  const multiPaneRef = useRef(null);

  const defaultRunLocation = "/scratch/user/" + document.user + "/drona_composer/runs";
  const [runLocation, setRunLocation] = useState(
	  defaultRunLocation
  );



  const [environments, setEnvironments] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(document.dashboard_url + "/jobs/composer/environments")
      .then((response) => response.json())
      .then((data) => {
        setEnvironments(
          data.map((env) => ({
            value: env.env,
            label: env.env,
            src: env.src,
            styles: { color: env.is_user_env ? "#3B71CA" : "" },
          }))
        );
      })
      .catch((error) => {
        console.error("Error fetching JSON data");
      });
  }, []);

  function sync_job_name(name) {
    setRunLocation(
      defaultRunLocation + "/" + name
    );
  }

useEffect(() => {
  if (!environment.env || !environment.src) return;

  const fetchSchema = async () => {
    try {
      const response = await fetch(
        `${document.dashboard_url}/jobs/composer/schema/${environment.env}?src=${environment.src}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw {
          message: errorData.message || 'Failed to load schema',
          status_code: response.status,
          details: errorData.details || errorData
        };
      }

      const data = await response.json();
     setFields(data);
      
      // Resolve the promise if there's a resolver
      if (fieldsLoadedResolver) {
        fieldsLoadedResolver(data);
        setFieldsLoadedResolver(null);
      }
    } catch (error) {
      setError(error);
    }
  };

  fetchSchema();
}, [environment, fieldsLoadedResolver]);

function handleEnvChange(key, option) {
  setEnvironment({ env: option.value, src: option.src });
}

function handleRerunCancel() {
	setShowRerunModal(false);
}
async function processRerun(promptData) {
  
    setJobStatus("rerun");
    setShowRerunModal(false);
    try {
    const response = await fetch(`${document.dashboard_url}/jobs/composer/history/${pendingRerunRow.job_id}`, {
      method: 'GET'
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.statusText}`);
    }

    const jobScript = await response.json();
    
    const modal = new bootstrap.Modal(previewRef.current);
    modal.show();

    setJobScript(jobScript["script"]);

    const panes = [
      {
        preview_name: "template.txt",
        content: jobScript["script"],
        name: "run_command",
        order: -3
      },
      {
        preview_name: "driver.sh",
        content: jobScript["driver"],
        name: "driver",
        order: -2
      },
    ];

    for (const [fname, file] of Object.entries(jobScript["additional_files"])) {
      panes.push({ 
        preview_name: file["preview_name"] || fname, 
        content: file["content"] || file, 
        name: fname, 
        order: file["preview_order"]
      });
    }

    setPanes(panes);
    setWarningMessages([]);
    setRerunInfo({
      ...pendingRerunRow,
      name: promptData.jobName,
      location: promptData.location
    });
    setPendingRerunRow(null);

  } catch (error) {
    console.error('Failed to generate preview:', error);
    alert('Failed to generate preview: ' + error.message);
  }
}

async function handleRerun(row) {
  setRerunOriginalName(row.name);
  setPendingRerunRow(row);
  setShowRerunModal(true);
}  
async function handleForm(row) {
  const fieldsPromise = new Promise(resolve => {
    setFieldsLoadedResolver(() => resolve);
  });

  await setEnvironment({env: row.runtime, src: row.env_dir});
  const updatedFields = await fieldsPromise;

  if (composerRef.current) {
    composerRef.current.setValues(row.form_data);
  }
}


  function handleUploadedFiles(files, globalFiles) {
    let combinedFiles = Array.from(new Set([...globalFiles, ...files]));
    setGlobalFiles(combinedFiles);
  }

  function preview_job(action, formData, callback) {
    var request = new XMLHttpRequest();

    request.responseType = "json";
    formData.append("env_dir", environment.src);

    request.open("POST", action, true);

    request.onload = function (event) {
      if (request.status == 200) {
        var jobScript = request.response;
        callback(null, jobScript); // Pass the result to the callback
      } else {
        callback(`Error ${request.status}. Try again!`); // Pass the error to the callback
      }
    };
    request.onerror = function (event) {
      callback("An error has occurred. Please try again!"); // Pass the error to the callback
    };

    request.send(formData);
  }

  function handlePreview() {
    setJobStatus("new")
    const formData = new FormData(formRef.current);

    if (!formData.has("runtime")) {
      alert("Environment is required.");
      return;
    }

    const modal = new bootstrap.Modal(previewRef.current);
    modal.toggle();
    const action = document.dashboard_url + "/jobs/composer/preview";
    preview_job(action, formData, function (error, jobScript) {
      if (error) {
        alert(error);
      } else {
        setJobScript(jobScript["script"]);

	// Template and driver panes will be displayed on the left of everything else
        const panes = [
          {
            preview_name: "template.txt",
            content: jobScript["script"],
            name: "run_command",
            order: -3
          },
          {
	    preview_name: "driver.sh",
	    content: jobScript["driver"],
	    name: "driver",
	    order: -2
	  },
        ];

        for (const [fname, file] of Object.entries(
          jobScript["additional_files"]
        )) {
          panes.push({ preview_name: file["preview_name"], content: file["content"], name: fname, order: file["preview_order"]});
        }

        setPanes(panes);

        setWarningMessages(jobScript["warnings"]);
      }
    });
  }

  function handleAddEnv() {
    // fetch system environments
    fetch(document.dashboard_url + "/jobs/composer/get_more_envs_info")
      .then((response) => response.json())
      .then((data) => {
        // Select the modal body where the table will be appended
        const envModalBody = document.querySelector(
          "#env-add-modal .modal-body"
        );

        // Create the table structure
        envModalBody.innerHTML = `
          <table class="table table-striped table-bordered">
            <thead>
              <tr>
                <th>Environment</th>
                <th>Description</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="env-table-body">
            </tbody>
          </table>
        `;

        const envTableBody = document.querySelector("#env-table-body");

        // Iterate through each environment and append a row to the table
        data.forEach((env) => {
          // Create table row
          const envRow = document.createElement("tr");

          // Create cells for environment and source
          const envCell = document.createElement("td");
          envCell.textContent = env.env;

          const descriptionCell = document.createElement("td");
          descriptionCell.textContent = env.description;

          // Create the "Add" button
          const actionCell = document.createElement("td");
          const envButton = document.createElement("button");
          envButton.className = "btn btn-primary";
          envButton.innerHTML = "Add";
          envButton.addEventListener("click", function () {
            // Send post request to add environment
            const formData = new FormData();
            formData.append("env", env.env);
            formData.append("src", env.src);
            fetch(document.dashboard_url + "/jobs/composer/add_environment", {
              method: "POST",
              body: formData,
            })
              .then((response) => response.json())
              .then((data) => {
                if (data.status === "Success") {
                  alert("Environment added successfully");
                  const newEnv = {
                    value: env.env,
                    label: env.env,
                    src: env.src,
                    styles: { color: "#3B71CA" },
                  };
                  setEnvironments((prevEnvironments) => [
                    ...prevEnvironments,
                    newEnv,
                  ]);
                } else {
                  alert("Error adding environment");
                }
              })
              .catch((error) => {
                console.log(error);
                console.error("Error fetching JSON data");
              });
          });

          // Append button to the action cell
          actionCell.appendChild(envButton);

          // Append all cells to the row
          envRow.appendChild(envCell);
          envRow.appendChild(descriptionCell);
          envRow.appendChild(actionCell);

          // Append the row to the table body
          envTableBody.appendChild(envRow);
        });

        // Initialize and show the Bootstrap modal
        const modal = new bootstrap.Modal(envModalRef.current);
        modal.toggle();
      })
      .catch((error) => {
        console.log(error);
        console.error("Error fetching environment data");
      });
  }

  function add_submission_loading_indicator() {
    var submission_section = document.getElementById(
      "job-submit-button-section"
    );
    if (submission_section == null) {
      return;
    }

    var spinner = document.createElement("span");
    spinner.id = "submission-loading-spinner";
    spinner.className = "spinner-border text-primary";

    submission_section.appendChild(spinner);
  }

  function remove_submission_loading_indicator() {
    var spinner = document.getElementById("submission-loading-spinner");
    if (spinner == null) {
      return;
    }

    spinner.remove();
  }

  function submit_job(action, formData) {
    var request = new XMLHttpRequest();

    add_submission_loading_indicator();
    request.open("POST", action, true);
    request.onload = function (event) {
      remove_submission_loading_indicator();
      if (request.status == 200) {
        alert(request.responseText);
        window.location.reload();
      } else {
        alert(`Error ${request.status}. Try again!`);
        window.location.reload();
      }
    };
    request.onerror = function (event) {
      remove_submission_loading_indicator();
      alert("An error has occured. Please try again!");
      window.location.reload();
    };

    request.send(formData);
  }

  function handleRerunSubmit(event) {
    event.preventDefault();
    const data = rerunInfo;
    const paneRefs = multiPaneRef.current.getPaneRefs();
    const additionalFiles = {};

    paneRefs.forEach((ref) => {
      if (!ref.current) return;

      const current = ref.current;
      const name = current.getAttribute("name");

      if (name === "driver" || name === "run_command") {
        data[name] = current.value;
      } else {
        additionalFiles[name] = current.value;
      }
    });

    data["additional_files"] = JSON.stringify(additionalFiles);

    if (globalFiles && globalFiles.length) {
      data["files"] = globalFiles;
    }  

    const action = formRef.current.getAttribute("action");

    // Convert dictionary to formData 
    const formData = new FormData();

    for (const [key, value] of Object.entries(data)) {
      if (value instanceof File) {
        formData.append(key, value);
      } else if (Array.isArray(value)) {
        value.forEach((item, index) => {
          formData.append(`${key}[]`, item);
        });
      } else if (value !== null && value !== undefined) {
        formData.append(key, String(value));
      }
    }
    submit_job(action, formData);
  }
  function handleSubmit(event) {
    event.preventDefault();

    const formData = new FormData(formRef.current);

    if (formData.get("name") === "") {
      alert("Job name is required.");
      return;
    }
    const paneRefs = multiPaneRef.current.getPaneRefs();
    const additional_files = {};
    paneRefs.forEach((ref) => {
      if (ref.current) {
        const current = ref.current;

        const name = current.getAttribute("name");
        if (name === "driver" || name === "run_command") {
          formData.append(current.getAttribute("name"), current.value);
        } else {
          additional_files[name] = current.value;
        }
      }
    });
    formData.append("additional_files", JSON.stringify(additional_files));

    globalFiles.forEach((file) => {
      formData.append("files[]", file);
    });
       
    formData.append("env_dir", environment.src);
    const action = formRef.current.getAttribute("action");
    submit_job(action, formData);
  }

  const handleJobScriptChange = (event) => {
    setJobScript(event.target.value);
  };

return (
  <GlobalFilesContext.Provider value={{ globalFiles, setGlobalFiles }}>
    <>
    <JobComposer
      error={error}
      setError={setError}
      environment={environment}
      environments={environments}
      fields={fields}
      runLocation={runLocation}
      warningMessages={warningMessages}
      panes={panes}
      setPanes={setPanes}
      handleSubmit={(jobStatus == "new") ? handleSubmit : handleRerunSubmit}
      handlePreview={handlePreview}
      handleEnvChange={handleEnvChange}
      handleAddEnv={handleAddEnv}
      handleUploadedFiles={handleUploadedFiles}
      sync_job_name={sync_job_name}
      formRef={formRef}
      previewRef={previewRef}
      envModalRef={envModalRef}
      multiPaneRef={multiPaneRef}
      handleRerun={handleRerun}
      handleForm={handleForm}
      composerRef={composerRef}
    />
    {showRerunModal && (
      <RerunPromptModal
        modalRef={rerunPromptModalRef}
        originalName={rerunOriginalName}
        defaultLocation={defaultRunLocation}
        onConfirm={processRerun}
        onCancel={handleRerunCancel}
      />
    )}
    </>
  </GlobalFilesContext.Provider>
);
}

// Render the parent component into the root DOM node
ReactDOM.render(<App />, document.getElementById("root"));
