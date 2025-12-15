/**
 * @name JobNameLocation
 * @description A composite form component that combines job name input and location picker
 * in a single row layout. Manages both the job name (text input) and working directory location
 * (file picker) with synchronized state. Commonly used in HPC job submission forms.
 *
 * @example
 * // Basic job name and location picker
 * {
 *   "type": "jobNameLocation",
 *   "label": "Job Configuration",
 *   "showName": true,
 *   "showLocation": true,
 *   "pickerLabel": "Browse",
 *   "help": "Enter job name and select working directory"
 * }
 *
 * @example
 * // With custom defaults and disabled fields
 * {
 *   "type": "jobNameLocation",
 *   "label": "Job Settings",
 *   "customJobName": "MyJob",
 *   "customJobLocation": "$HOME/jobs",
 *   "disableJobNameChange": true,
 *   "showLocation": true,
 *   "help": "Job name is fixed, but you can change the location"
 * }
 *
 * @property {boolean} [showName=true] - Whether to display the job name input field
 * @property {boolean} [showLocation=true] - Whether to display the location picker
 * @property {boolean} [disableJobNameChange=false] - Makes the job name field read-only
 * @property {boolean} [disableJobLocationChange=false] - Makes the location picker read-only
 * @property {string} [customJobName] - Pre-filled job name value
 * @property {string} [customJobLocation] - Pre-filled location path
 * @property {string} [label] - Display label for the entire component
 * @property {string} [pickerLabel="Change"] - Label for the location picker button
 * @property {string} [help] - Help text displayed below the component
 * @property {boolean} [labelOnTop=true] - Whether to position label above the fields
 */

import React, { useEffect } from "react";
import FormElementWrapper from "../utils/FormElementWrapper";
import Text from "../schemaElements/Text";
import Picker from "../schemaElements/Picker";

export default function JobNameLocation({
    // schema-configurable
    showName = true,
    showLocation = true,
    disableJobNameChange,
    disableJobLocationChange,
    help,
    labelOnTop = true,
    customJobName,
    customJobLocation,
    label,
    pickerLabel = "Change",

    // pass-through from Composer/FieldRenderer
    sync_job_name,          // e.g., props.sync_job_name
    runLocation,       // e.g., props.runLocation
    setRunLocation,
    setBaseRunLocation,
    onChange,              // forwarded from FieldRenderer (handleValueChange wrapper)
    ...rest
}) {


    useEffect(() => {
        if (customJobLocation) {
            setRunLocation?.(customJobLocation);
            // onChange?.("location", customJobLocation);
        }
        if (customJobName) {
            sync_job_name?.(customJobName, customJobLocation);
            // onChange?.("name", customJobName);
        }
    }, []);

    return (
        <FormElementWrapper
            labelOnTop={labelOnTop}
            name={"name_location"}
            label={label}
            help={help}
        >
            <div className="form-group">
                <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                    {showName && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                            <label htmlFor="job-name" style={{ whiteSpace: 'nowrap' }}>Job Name</label>
                            <Text
                                name={"name"}
                                id={"job-name"}
                                label=""
                                value={customJobName || ""}
                                useLabel={false}              // suppress inner label; we render our own
                                onNameChange={sync_job_name}   // mirrors previous inline behavior
                                onChange={onChange}
                                placeholder="Drona ID"
                                disableChange={disableJobNameChange}

                            />
                        </div>
                    )}

                    {showLocation && (
                        <div style={{ display: 'flex', flexGrow: 1, gap: '1.5rem' }}>

                            <div style={{ flex: 1 }}>
                                <Picker
                                    name={"location"}
                                    useLabel={false}
                                    localLabel={pickerLabel}
                                    defaultLocation={runLocation}
                                    onChange={onChange}          // keep renderer state/hooks consistent
                                    setBaseRunLocation={setBaseRunLocation}
                                    style={{ width: "100%", alignItems: "flex" }}
                                    disableChange={disableJobLocationChange}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </FormElementWrapper>
    );
}
