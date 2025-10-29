import React, { useEffect } from "react";
import FormElementWrapper from "../utils/FormElementWrapper";
import Text from "../schemaElements/Text";
import Picker from "../schemaElements/Picker";

/**
 * JobNameLocation: composite control for job "name" + "location"
 * Writes to engine keys: "name" and "location"
 */
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
