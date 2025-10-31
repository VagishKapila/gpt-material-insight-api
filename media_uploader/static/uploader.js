const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('previewGrid');
const addMore = document.getElementById('add-more-container');

let mediaFiles = [];
const MAX_FILES = 20;

// 🔁 Re-render previews
function renderPreviews() {
  previewGrid.innerHTML = '';
  mediaFiles.forEach((media, index) => {
    const isVideo = media.file.type.startsWith('video/');
    const div = document.createElement('div');
    div.className = 'preview-item';
    div.innerHTML = `
      <${isVideo ? 'video controls' : 'img'} src="${media.url}" />
      <button class="remove-btn" onclick="removeFile(${index})">&times;</button>
    `;
    previewGrid.appendChild(div);
  });
  console.debug('✅ Previews rendered:', mediaFiles.length, 'files');
}

// 🧠 Compress images client-side
function compressImage(file, callback) {
  const img = new Image();
  const reader = new FileReader();
  reader.onload = e => {
    img.onload = () => {
      const canvas = document.createElement('canvas');
      let width = img.width, height = img.height;
      const maxDim = 1600;
      if (width > height && width > maxDim) {
        height *= maxDim / width; width = maxDim;
      } else if (height > maxDim) {
        width *= maxDim / height; height = maxDim;
      }
      canvas.width = width; canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob(blob => {
        const compressed = new File([blob], file.name, { type: file.type });
        callback(compressed);
      }, file.type, 0.7);
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

// 📂 Handle new files
function handleFiles(files) {
  if (mediaFiles.length + files.length > MAX_FILES) {
    alert("⚠️ Max 20 files allowed");
    return;
  }

  Array.from(files).forEach(file => {
    const isImage = file.type.startsWith('image/');
    const isVideo = file.type.startsWith('video/');
    if (!isImage && !isVideo) return;

    const maxSize = isVideo ? 100 * 1024 * 1024 : 15 * 1024 * 1024;
    if (file.size > maxSize) {
      alert(`⚠️ ${file.name} too large.`);
      return;
    }

    if (isImage) {
      compressImage(file, compressed => {
        mediaFiles.push({ file: compressed, url: URL.createObjectURL(compressed) });
        renderPreviews();
      });
    } else {
      mediaFiles.push({ file, url: URL.createObjectURL(file) });
      renderPreviews();
    }
  });

  console.debug('📁 Files handled:', mediaFiles.map(f => f.file.name));
}

// ❌ Remove a file
function removeFile(index) {
  mediaFiles.splice(index, 1);
  renderPreviews();
}

// 🔁 Reset uploader
function resetUploader() {
  mediaFiles = [];
  renderPreviews();
  document.getElementById("progress-container").style.display = "none";
  document.getElementById("progress-bar").style.width = "0%";
  document.getElementById("upload-status").textContent = "";
}

// ⬆️ Upload to server
function uploadMedia() {
  if (mediaFiles.length === 0) return alert("No media to upload.");

  const formData = new FormData();
  mediaFiles.forEach(media => formData.append("media_files", media.file));

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload_media_test", true);

  const progressContainer = document.getElementById("progress-container");
  const progressBar = document.getElementById("progress-bar");
  const statusText = document.getElementById("upload-status");

  progressContainer.style.display = "block";
  progressBar.style.width = "0%";
  statusText.textContent = "";

  xhr.upload.addEventListener("progress", e => {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      progressBar.style.width = percent + "%";
    }
  });

  xhr.onload = () => {
    if (xhr.status === 200) {
      const res = JSON.parse(xhr.responseText);
      statusText.textContent = res.message || "✅ Upload complete!";
      console.log("✅ Server Response:", res);
    } else {
      statusText.textContent = "❌ Upload failed";
      progressBar.style.backgroundColor = "#e74c3c";
    }
  };

  xhr.onerror = () => {
    statusText.textContent = "❌ Upload error";
    progressBar.style.backgroundColor = "#e74c3c";
  };

  xhr.send(formData);
}

// ➕ Add more media (clicking plus sign)
addMore.addEventListener('click', () => fileInput.click());

// Drag events
dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});
dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('dragover');
});
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', e => handleFiles(e.target.files));
