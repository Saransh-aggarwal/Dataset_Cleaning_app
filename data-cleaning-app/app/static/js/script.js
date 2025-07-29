
document.addEventListener('DOMContentLoaded', () => {
    const checkpointSelector = document.getElementById('base_checkpoint');
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const checkpointNameDisplay = document.getElementById('checkpoint-name-display');
    const previewHtmlContainer = document.getElementById('preview-html-container');
    const infoHtmlContainer = document.getElementById('info-html-container');
    const codeBlock = document.getElementById('code-block');
    const newTypeSelector = document.getElementById('new_type');
    const roundingOptionsContainer = document.getElementById('rounding-options-container');
    const typeColumnsListContainer = document.getElementById('type-columns-list');


    const columnListContainers = {
        'drop_columns': document.getElementById('drop-columns-list'),
        'na_columns': document.getElementById('na-columns-list'),
        'type_columns': document.getElementById('type-columns-list'),
        'float_to_int_columns': document.getElementById('float-to-int-columns-list'),
        'str_columns': document.getElementById('str-columns-list'),
        'scale_columns': document.getElementById('scale-columns-list'),
        'date_columns': document.getElementById('date-columns-list'),
        'encode_columns': document.getElementById('encode-columns-list')
    };

    
    const updateUI = (data) => {
        checkpointNameDisplay.innerText = data.name;
        previewHtmlContainer.innerHTML = data.head_html;
        codeBlock.innerText = data.full_code;
        infoHtmlContainer.textContent = data.info_html;

        updateColumnCheckboxes(columnListContainers.drop_columns, data.columns, 'drop_columns');
        updateColumnCheckboxes(columnListContainers.na_columns, data.columns, 'na_columns');
        updateColumnCheckboxes(columnListContainers.type_columns, data.columns, 'type_columns');
        updateColumnCheckboxes(columnListContainers.str_columns, data.categorical_cols, 'str_columns');
        updateColumnCheckboxes(columnListContainers.scale_columns, data.numeric_cols, 'scale_columns');
        updateColumnCheckboxes(columnListContainers.date_columns, data.datetime_cols, 'date_columns');
        updateColumnCheckboxes(columnListContainers.encode_columns, data.categorical_cols, 'encode_columns');
        
        const float_cols = data.numeric_cols.filter(col => {
            const regex = new RegExp(`\\s${col}\\s+.+float64`);
            return regex.test(data.info_html);
        });
        updateColumnCheckboxes(columnListContainers.float_to_int_columns, float_cols, 'float_to_int_columns');
    };

    const updateColumnCheckboxes = (container, columns, name) => {
        if (!container) return; 
        container.innerHTML = '';
        if (!columns || columns.length === 0) {
            container.innerHTML = '<p class="text-muted small">No applicable columns found in this checkpoint.</p>';
            return;
        }
        columns.forEach(col => {
            const safeColId = col.replace(/[^a-zA-Z0-9]/g, '_');
            const div = document.createElement('div');
            div.className = 'form-check';
            div.innerHTML = `
                <input class="form-check-input" type="checkbox" name="${name}" value="${col}" id="${name}_${safeColId}">
                <label class="form-check-label" for="${name}_${safeColId}">${col}</label>
            `;
            container.appendChild(div);
        });
    };

    const fetchCheckpointData = (filename) => {
        loadingSpinner.classList.remove('d-none');
        resultsContainer.classList.add('d-none');

        fetch(`/api/checkpoint_details/${filename}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok (${response.status})`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                updateUI(data);
                loadingSpinner.classList.add('d-none');
                resultsContainer.classList.remove('d-none');
            })
            .catch(error => {
                console.error('Error fetching checkpoint details:', error);
                const mainPanel = document.querySelector('.col-lg-7');
                if(mainPanel) {
                    mainPanel.innerHTML = `<div class="alert alert-danger"><strong>Error:</strong> Failed to load checkpoint data. ${error.message}. Please try selecting another checkpoint or upload a new file.</div>`;
                }
            });
    };

    const toggleRoundingOptions = () => {
        if (!newTypeSelector || !roundingOptionsContainer || !typeColumnsListContainer) return;

        // Get the currently selected new type
        const selectedNewType = newTypeSelector.value;
        
        // Find the FIRST checked checkbox to inspect its original data type
        const firstCheckedCheckbox = typeColumnsListContainer.querySelector('input[type="checkbox"]:checked');
        
        // This is a bit tricky, we need to know the original type. 
        // We'll infer it from the full `df.info` string.
        // This part requires the `info_html` to be available.
        const infoHtml = document.getElementById('info-html-container').textContent;
        
        let isFloatSource = false;
        if (firstCheckedCheckbox) {
            const colName = firstCheckedCheckbox.value;
            const regex = new RegExp(`\\s${colName}\\s+.+float64`);
            if (infoHtml.match(regex)) {
                isFloatSource = true;
            }
        }
        
        // Show the rounding options ONLY if the user wants to convert a float source to an integer
        if (selectedNewType === 'Int64' && isFloatSource) {
            roundingOptionsContainer.classList.remove('d-none');
        } else {
            roundingOptionsContainer.classList.add('d-none');
        }
    };

    if (newTypeSelector && typeColumnsListContainer) {
        // Add event listeners to check whenever the user changes something
        newTypeSelector.addEventListener('change', toggleRoundingOptions);
        typeColumnsListContainer.addEventListener('change', toggleRoundingOptions);
    }


    if (checkpointSelector) {
        checkpointSelector.addEventListener('change', (event) => {
            fetchCheckpointData(event.target.value);
        });
        fetchCheckpointData(checkpointSelector.value);
    }
    document.body.addEventListener('click', function(event) {
        const copyButton = event.target.closest('#copy-btn');
        if (copyButton) {
            const codeToCopy = document.getElementById('code-block').innerText;
            navigator.clipboard.writeText(codeToCopy).then(() => {
                const originalContent = copyButton.innerHTML;
                copyButton.innerHTML = `<i class="bi bi-check-lg"></i> Copied!`;
                setTimeout(() => { copyButton.innerHTML = originalContent; }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                alert("Failed to copy code to clipboard.");
            });
        }
    });
});