const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'Vacation Builder'
    });

    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function startPythonBackend() {
    // Check if we're running in development with concurrently
    // In that case, the backend is already started by npm run backend
    if (process.env.npm_lifecycle_event === 'start') {
        console.log('Backend is managed by npm run dev - skipping Electron spawn');
        return Promise.resolve();
    }

    // Use venv Python for standalone execution
    const pythonPath = path.join(__dirname, '..', 'backend', 'venv', 'bin', 'python');
    const backendPath = path.join(__dirname, '..', 'backend', 'main.py');

    console.log('Starting Python backend...');

    pythonProcess = spawn(pythonPath, [backendPath], {
        cwd: path.join(__dirname, '..', 'backend')
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
        if (mainWindow) {
            mainWindow.webContents.send('backend-log', data.toString());
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });

    // Give backend time to start
    return new Promise(resolve => setTimeout(resolve, 3000));
}

// IPC Handlers
ipcMain.handle('open-pdf', async (event, pdfPath) => {
    await shell.openPath(pdfPath);
    return { success: true };
});

ipcMain.handle('save-pdf-dialog', async () => {
    const result = await dialog.showSaveDialog(mainWindow, {
        title: 'Save Vacation Itinerary PDF',
        defaultPath: 'vacation-itinerary.pdf',
        filters: [
            { name: 'PDF Files', extensions: ['pdf'] }
        ]
    });
    return result;
});

ipcMain.handle('get-backend-url', () => {
    return 'http://127.0.0.1:8000';
});

// App lifecycle
app.whenReady().then(async () => {
    await startPythonBackend();
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
