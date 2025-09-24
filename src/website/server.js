const express = require('express');
const path = require('path');
const { exec } = require('child_process');
const fs = require('fs');

const app = express();
const PORT = 3000;

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/data/personal_data_aggregation.json', (req, res) => {
    res.sendFile(path.join(__dirname, 'data', 'personal_data_aggregation.json'));
});

app.post('/open-file', (req, res) => {
    const { filePath } = req.body;

    if (!filePath) {
        return res.status(400).json({ success: false, error: 'No file path provided' });
    }

    // Construct the full path to the file
    const fullPath = path.resolve(__dirname, '..', '..', filePath);

    // Check if file exists
    if (!fs.existsSync(fullPath)) {
        return res.status(404).json({ success: false, error: 'File not found' });
    }

    // Open file with default application based on OS
    let command;
    switch (process.platform) {
        case 'darwin': // macOS
            command = `open "${fullPath}"`;
            break;
        case 'win32': // Windows
            command = `start "" "${fullPath}"`;
            break;
        case 'linux': // Linux
            command = `xdg-open "${fullPath}"`;
            break;
        default:
            return res.status(500).json({ success: false, error: 'Unsupported operating system' });
    }

    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error('Error opening file:', error);
            return res.status(500).json({ success: false, error: error.message });
        }

        res.json({ success: true, message: `File opened: ${path.basename(fullPath)}` });
    });
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
    console.log('Press Ctrl+C to stop the server');
});