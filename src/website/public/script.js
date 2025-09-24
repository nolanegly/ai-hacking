class PersonalDataViewer {
    constructor() {
        this.data = null;
        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.createFirstNameDropdown();
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

    createFirstNameDropdown() {
        if (!this.data || !this.data.aggregated_personal_data || !this.data.aggregated_personal_data.firstName) {
            this.showError('No firstName data available');
            return;
        }

        const firstNameData = this.data.aggregated_personal_data.firstName;
        const sortedData = this.sortByOccurrencesThenAlphabetically(firstNameData);

        const dropdownContainer = document.getElementById('firstName-dropdown-container');
        if (!dropdownContainer) {
            console.error('firstName-dropdown-container not found');
            return;
        }

        const select = document.createElement('select');
        select.id = 'firstName-dropdown';
        select.className = 'form-select';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a first name...';
        select.appendChild(defaultOption);

        // Add sorted options
        sortedData.forEach(item => {
            const option = document.createElement('option');
            option.value = item.value;
            option.textContent = `${item.value} (${item.occurrences} occurrences)`;
            select.appendChild(option);
        });

        // Add event listener
        select.addEventListener('change', (e) => {
            this.handleFirstNameSelection(e.target.value);
        });

        dropdownContainer.appendChild(select);
    }

    sortByOccurrencesThenAlphabetically(data) {
        return data.slice().sort((a, b) => {
            // First sort by occurrences (descending)
            if (b.occurrences !== a.occurrences) {
                return b.occurrences - a.occurrences;
            }
            // If occurrences are equal, sort alphabetically (ascending)
            return a.value.localeCompare(b.value);
        });
    }

    handleFirstNameSelection(selectedValue) {
        if (!selectedValue) {
            this.clearSelectionInfo();
            return;
        }

        const firstNameData = this.data.aggregated_personal_data.firstName;
        const selectedItem = firstNameData.find(item => item.value === selectedValue);

        if (selectedItem) {
            this.displaySelectionInfo(selectedItem);
        }
    }

    displaySelectionInfo(item) {
        const infoContainer = document.getElementById('selection-info');
        if (!infoContainer) return;

        const fileList = item.instances.map(instance =>
            `<li>${instance.file} (confidence: ${instance.confidence})</li>`
        ).join('');

        infoContainer.innerHTML = `
            <div class="selection-details">
                <h4>Selected: ${item.value}</h4>
                <p><strong>Occurrences:</strong> ${item.occurrences}</p>
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