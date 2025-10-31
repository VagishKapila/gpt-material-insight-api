// ✅ DOM references
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('previewGrid');
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const statusText = document.getElementById("upload-status");

let mediaFiles = [];
const MAX_FILES = 20;

// ✅ GLOBAL drag-and-drop protection (prevents browser hijack)
document.addEventListener("dragover", (e) => {
  e.preventDefault();
  e.stopPropagation();
});
document.addEventListener("drop", (e) => {
  e.preventDefault();
  e.stopPropagation();
  if (e.dataTransfer && e.dataTransfer.files.length) {
    handleFiles(e.dataTransfer.files);
  }
});

// ✅ Dropzone-specific styling
dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});
dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('dragover');
});
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});

// ✅ Manual file picker
dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => handleFiles(e.target.files)); hated
