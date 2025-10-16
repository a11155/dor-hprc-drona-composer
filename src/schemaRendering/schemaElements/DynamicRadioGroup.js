import React, {
    useState,
    useEffect,
    useRef,
    useContext,
    useCallback,
    useMemo,
} from "react";
import FormElementWrapper from "../utils/FormElementWrapper";
import { FormValuesContext } from "../FormValuesContext";
import { getFieldValue } from "../utils/fieldUtils";
import RadioGroup from "./RadioGroup";
import config from "@config";

function DynamicRadioGroup(props) {
    const [options, setOptions] = useState(props.options || []);
    const [value, setValue] = useState(props.value || "");
    const [isLoading, setIsLoading] = useState(false);
    const [isEvaluated, setIsEvaluated] = useState(false);
    const [isValueInvalid, setIsValueInvalid] = useState(false);

    const { values: formValues } = useContext(FormValuesContext);
    const formValuesRef = useRef(formValues);

    const isShown = props.isShown ?? true;



    // --- LOG: initial props
    useEffect(() => {
        console.log("[DRG] mount props =", {
            name: props.name,
            label: props.label,
            retriever: props.retriever,
            retrieverPath: props.retrieverPath,
            retrieverParams: props.retrieverParams,
            isShown: props.isShown,
            defaultValue: props.value,
            initialOptions: props.options,
        });
    }, []); // mount only

    useEffect(() => {
        formValuesRef.current = formValues;
    }, [formValues]);

    useEffect(() => {
        setValue(props.value || "");
    }, [props.value]);

    const relevantFieldNames = useMemo(() => {
        if (!props.retrieverParams) return [];
        return Object.values(props.retrieverParams)
            .filter((v) => typeof v === "string" && v.startsWith("$"))
            .map((v) => v.substring(1));
    }, [props.retrieverParams]);

    const devUrl = config.development.dashboard_url;
    const prodUrl = config.production.dashboard_url;
    const curUrl = process.env.NODE_ENV === "development" ? devUrl : prodUrl;

    const fetchOptions = useCallback(async () => {
        const retrieverPath = props.retrieverPath || props.retriever;

        console.log("[DRG] fetchOptions start", {
            retrieverPath,
            isShown,
            curUrl,
        });

        if (!retrieverPath) {
            props.setError?.({
                message: "Retriever path is not set",
                status_code: 400,
                details: "",
            });
            return;
        }

        setIsLoading(true);
        const currentFormValues = formValuesRef.current;

        try {
            const params = new URLSearchParams();
            if (props.retrieverParams && typeof props.retrieverParams === 'object') {
                Object.entries(props.retrieverParams).forEach(([key, rawVal]) => {
                    const resolved = (typeof rawVal === 'string' && rawVal.startsWith('$'))
                        ? getFieldValue(currentFormValues, rawVal.substring(1))
                        : rawVal;

                    if (resolved === undefined || resolved === null) return;

                    if (typeof resolved === 'string' || typeof resolved === 'number' || typeof resolved === 'boolean') {
                        params.append(key, String(resolved));               // no quotes for primitives
                    } else {
                        params.append(key, JSON.stringify(resolved));       // JSON for objects/arrays
                    }
                });
            }

            const queryString = params.toString();
            const requestUrl = `${curUrl}/jobs/composer/evaluate_dynamic_text?retriever_path=${encodeURIComponent(
                retrieverPath
            )}${queryString ? `&${queryString}` : ""}`;

            const response = await fetch(requestUrl);
            if (!response.ok) {
                let errorData = {};
                try { errorData = await response.json(); } catch { }
                props.setError?.({
                    message: errorData.message || "Failed to retrieve radio options",
                    status_code: response.status,
                    details: errorData.details || errorData,
                });
                return;
            }

            const data = await response.json();
            setOptions(Array.isArray(data) ? data : []);
            setIsEvaluated(true);

            // Mark currently selected value as invalid if not present
            setIsValueInvalid(!!value && !data.some((o) => o.value === value));
        } catch (error) {
            props.setError?.(error);
        } finally {
            setIsLoading(false);
        }
    }, [props.retrieverPath, props.retriever, props.retrieverParams, props.setError, curUrl, value]);

    // Debounced version (define it BEFORE the effect that uses it)
    const debouncedFetchOptions = useCallback(() => {
        let timeout;
        return () => {
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(() => {
                fetchOptions();
                timeout = null;
            }, 300);
        };
    }, [fetchOptions])();

    // Initial fetch when component is shown
    useEffect(() => {
        if (isShown && !isEvaluated) {
            fetchOptions();
        }
    }, [isShown, isEvaluated, fetchOptions]);

    // Track changes to relevant form values and refetch options
    const prevRelevantValuesRef = useRef({});
    useEffect(() => {
        if (!isShown || !props.retrieverParams || relevantFieldNames.length === 0) {
            return;
        }

        let hasRelevantValueChanged = false;

        for (const fieldName of relevantFieldNames) {
            const currentValue = getFieldValue(formValues, fieldName);
            const previousValue = prevRelevantValuesRef.current[fieldName];
            if (currentValue !== previousValue) {
                console.log("[DRG] retriever param changed", { fieldName, previousValue, currentValue });
                hasRelevantValueChanged = true;
                prevRelevantValuesRef.current[fieldName] = currentValue;
            }
        }

        if (hasRelevantValueChanged && isEvaluated) {
            setIsEvaluated(false);
            setOptions([]);
            debouncedFetchOptions();
        }
    }, [formValues, isShown, props.retrieverParams, relevantFieldNames, debouncedFetchOptions, isEvaluated]);

    const handleValueChange = (event) => {
        const newValue = event.target.value;
        console.log("[DRG] radio change:", { name: props.name, newValue });
        setValue(newValue);
        setIsValueInvalid(false);
        props.onChange?.(props.index, newValue);
    };


    return (
        <FormElementWrapper
            labelOnTop={props.labelOnTop}
            name={props.name}
            label={props.label}
            help={props.help}
        >
            {isLoading ? (
                <div>Loading options...</div>
            ) : options.length === 0 && isEvaluated ? (
                <div>No options available</div>
            ) : (

                options.map((option) => {
                    const id = `${props.name}-${option.value}`;
                    return (
                        <div className="form-check form-check-inline" key={option.value}>
                            <input
                                id={id}
                                type="radio"
                                className="form-check-input"
                                value={option.value}
                                name={props.name}
                                checked={value === option.value}
                                onChange={handleValueChange}
                                disabled={option.isDeprecated}
                            />
                            <label
                                className={`form-check-label ${option.isDeprecated ? "text-danger fst-italic" : ""}`}
                                htmlFor={id}
                            >
                                {option.label}
                            </label>
                        </div>
                    );
                })
            )}
            {isValueInvalid && (
                <div className="text-danger" style={{ fontSize: "0.875em", marginTop: "0.25rem" }}>
                    The previously selected option is no longer available
                </div>
            )}
        </FormElementWrapper>
    );
}

export default DynamicRadioGroup;
