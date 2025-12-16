import React, { useEffect, useContext } from "react";
import FormElementWrapper from "../utils/FormElementWrapper";
import Text from "../schemaElements/Text";
import Picker from "../schemaElements/Picker";
import { FormValuesContext } from "../FormValuesContext";

export default function JobNameLocation(props) {
    const { updateValue } = useContext(FormValuesContext);

    // console.log("jobNameLocation elements:", props.elements);


    // const nameField = props.elements?.jobName;       // should have name: "name"
    // const locationField = props.elements?.jobLocation; // should have name: "location"

    const elementsArr = Array.isArray(props.elements) ? props.elements : [];

    const nameField = elementsArr.find(f => f?.name === "name");
    const locationField = elementsArr.find(f => f?.name === "location");

    const showName = props.showName ?? true;
    const showLocation = props.showLocation ?? true;

    // Use element.value if present, otherwise fall back to customJobName/customJobLocation
    const initialName = (nameField?.value ?? "") || (props.customJobName ?? "");
    const initialLocation = (locationField?.value ?? "") || (props.customJobLocation ?? "");

    // Current values (what we render). If schema doesn't have values yet, show the initial defaults.
    const nameValue = (nameField?.value ?? "") || initialName;
    const locationValue = (locationField?.value ?? "") || initialLocation;

    // Wrapper works whether child calls onChange(value) OR onChange(name, value)
    const setField = (field, ...args) => {
        const v = args.length === 2 ? args[1] : args[0];
        if (!field?.name) return;
        updateValue(field.name, v);
    };

    // On mount: mimic old behavior of initializing from customJobName/customJobLocation
    useEffect(() => {
        if (initialLocation) {
            // keep external runLocation in sync (old behavior)
            props.setRunLocation?.(initialLocation);
            // write into form state so FormData has it even if user doesn't touch it
            if (locationField?.name) updateValue(locationField.name, initialLocation);
        }

        if (initialName) {
            // old behavior: sync_job_name hook
            props.sync_job_name?.(initialName, initialLocation);
            // write into form state
            if (nameField?.name) updateValue(nameField.name, initialName);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <FormElementWrapper
            labelOnTop={props.labelOnTop ?? true}
            name="runDestination"
            label={props.label}
            help={props.help}
        >
            <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
                {showName && (
                    <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
                        <label style={{ whiteSpace: "nowrap" }}>Job Name</label>
                        <Text
                            // If you don't have elements yet, still render with name="name"
                            {...(nameField || {})}
                            name={nameField?.name || "name"}
                            useLabel={false}
                            value={nameValue || ""}              // if no customJobName -> blank
                            placeholder="Name"
                            disableChange={props.disableJobNameChange}
                            onChange={(...args) => {
                                setField({ name: nameField?.name || "name" }, ...args);

                                // preserve old sync hook on change (but no path concatenation)
                                const v = args.length === 2 ? args[1] : args[0];
                                props.sync_job_name?.(v, locationValue);
                            }}
                        />
                    </div>
                )}

                {showLocation && (
                    <div style={{ flex: 1 }}>
                        <Picker
                            {...(locationField || {})}
                            name={locationField?.name || "location"}
                            useLabel={false}
                            localLabel={(locationField && (locationField.pickerLabel || locationField.label)) || props.pickerLabel || "Set Location"}

                            // Old behavior: if no customJobLocation, it used runLocation
                            defaultLocation={locationValue || props.runLocation || ""}
                            disableChange={props.disableJobLocationChange}
                            setBaseRunLocation={props.setBaseRunLocation}
                            onChange={(...args) => {
                                setField({ name: locationField?.name || "location" }, ...args);
                            }}
                        />
                    </div>
                )}
            </div>
        </FormElementWrapper>
    );
}
