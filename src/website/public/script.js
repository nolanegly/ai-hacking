class PersonalDataViewer {
    constructor() {
        this.data = null;
        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.createAllDropdowns();
        } catch (error) {
            console.error('Error initializing PersonalDataViewer:', error);
            this.showError('Failed to load personal data');
        }
    }

    async loadData() {
        const response = await fetch('/data/personal_data_aggregation.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        this.data = await response.json();
    }

    createAllDropdowns() {
        if (!this.data || !this.data.aggregated_personal_data) {
            this.showError('No personal data available');
            return;
        }

        const personalData = this.data.aggregated_personal_data;
        const mainContainer = document.getElementById('dropdowns-container');

        if (!mainContainer) {
            console.error('dropdowns-container not found');
            return;
        }

        // Clear existing content
        mainContainer.innerHTML = '';

        // Create dropdowns for each attribute
        Object.keys(personalData).forEach(fieldName => {
            this.createDropdownForField(fieldName, personalData[fieldName], mainContainer);
        });
    }

    createDropdownForField(fieldName, fieldData, container) {
        const sortedData = this.sortByOccurrencesThenAlphabetically(fieldData);

        // Create wrapper div for each field
        const fieldWrapper = document.createElement('div');
        fieldWrapper.className = 'field-wrapper';

        // Create label
        const label = document.createElement('label');
        label.textContent = `${this.formatFieldName(fieldName)} (sorted by occurrence):`;
        label.className = 'field-label';

        // Create select dropdown
        const select = document.createElement('select');
        select.id = `${fieldName}-dropdown`;
        select.className = 'form-select';
        select.dataset.field = fieldName;

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = `Select ${this.formatFieldName(fieldName).toLowerCase()}...`;
        select.appendChild(defaultOption);

        // Add sorted options
        sortedData.forEach(item => {
            const option = document.createElement('option');
            option.value = item.value;
            const occurrenceText = item.occurrences === 1 ? 'occurrence' : 'occurrences';
            option.textContent = `${item.value} (${item.occurrences} ${occurrenceText})`;
            select.appendChild(option);
        });

        // Add event listener
        select.addEventListener('change', (e) => {
            this.handleSelection(fieldName, e.target.value);
        });

        fieldWrapper.appendChild(label);
        fieldWrapper.appendChild(select);
        container.appendChild(fieldWrapper);
    }

    formatFieldName(fieldName) {
        // Convert camelCase to readable format
        return fieldName.replace(/([A-Z])/g, ' $1')
                       .replace(/^./, str => str.toUpperCase());
    }

    sortByOccurrencesThenAlphabetically(data) {
        return data.slice().sort((a, b) => {
            // First sort by occurrences (descending)
            if (b.occurrences !== a.occurrences) {
                return b.occurrences - a.occurrences;
            }

            // If occurrences are equal, check if values are numeric
            const aIsNumeric = this.isNumericValue(a.value);
            const bIsNumeric = this.isNumericValue(b.value);

            // If both are numeric, sort by numeric value (descending)
            if (aIsNumeric && bIsNumeric) {
                const aNum = this.extractNumericValue(a.value);
                const bNum = this.extractNumericValue(b.value);
                return bNum - aNum;
            }

            // If occurrences are equal and not both numeric, sort alphabetically (ascending)
            return a.value.localeCompare(b.value);
        });
    }

    isNumericValue(value) {
        // Check for currency values like $1,500.00 or $95,000
        if (value.match(/^\$[\d,]+(\.\d{2})?$/)) {
            return true;
        }

        // Check for plain numbers
        const numericValue = parseFloat(value.replace(/[,$]/g, ''));
        return !isNaN(numericValue) && isFinite(numericValue);
    }

    extractNumericValue(value) {
        // Remove currency symbols, commas, and extract numeric value
        const cleanValue = value.replace(/[,$]/g, '');
        return parseFloat(cleanValue);
    }

    handleSelection(fieldName, selectedValue) {
        if (!selectedValue) {
            this.clearSelectionInfo();
            return;
        }

        const fieldData = this.data.aggregated_personal_data[fieldName];
        const selectedItem = fieldData.find(item => item.value === selectedValue);

        if (selectedItem) {
            this.displaySelectionInfo(selectedItem, fieldName);
        }
    }

    displaySelectionInfo(item, fieldName) {
        const infoContainer = document.getElementById('selection-info');
        if (!infoContainer) return;

        const fileList = item.instances.map(instance =>
            `<li>${instance.file} (confidence: ${instance.confidence})</li>`
        ).join('');

        const occurrenceText = item.occurrences === 1 ? 'Occurrence' : 'Occurrences';

        infoContainer.innerHTML = `
            <div class="selection-details">
                <h4>Selected ${this.formatFieldName(fieldName)}: ${item.value}</h4>
                <p><strong>${occurrenceText}:</strong> ${item.occurrences}</p>
                <p><strong>Weighted Score:</strong> ${item.weightedScore}</p>
                <p><strong>Found in files:</strong></p>
                <ul>${fileList}</ul>
            </div>
        `;
    }

    clearSelectionInfo() {
        const infoContainer = document.getElementById('selection-info');
        if (infoContainer) {
            infoContainer.innerHTML = '';
        }
    }

    showError(message) {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<div class="error">${message}</div>`;
        } else {
            console.error(message);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PersonalDataViewer();
});