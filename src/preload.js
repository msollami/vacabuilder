const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    openPDF: (pdfPath) => ipcRenderer.invoke('open-pdf', pdfPath),
    savePDFDialog: () => ipcRenderer.invoke('save-pdf-dialog'),
    getBackendURL: () => ipcRenderer.invoke('get-backend-url'),
    onBackendLog: (callback) => ipcRenderer.on('backend-log', callback)
});
