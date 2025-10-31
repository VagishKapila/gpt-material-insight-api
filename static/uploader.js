// ✅ static/uploader.js — Fully integrated drag/drop, compress, preview, zoom, and upload

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('preview-container');
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const statusText = document.getElementById("upload-status");
const zoomModal = document.getElementById("zoom-modal");

let mediaFiles = [];
const MAX_FILES = 20;

// 🌐 Global drag & drop
window.addEventListener("dragover", e => e.preventDefault());
window.addEventListener("drop", e => {
  e.preventDefault();
  if (e.dataTransfer?.files?.length) handleFiles(e.dataTransfer.files);
});

dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", e => handleFiles(e.target.files));

function compressImage(file, callback) {
  const img = new Image();
  const reader = new FileReader();
  reader.onload = e => {
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const maxDim = 1600;
      let width = img.width, height = img.height;
      if (width > height && width > maxDim) {
        height *= maxDim / width;
        width = maxDim;
      } else if (height > maxDim) {
        width *= maxDim / height;
        height = maxDim;
      }
      canvas.width = width;
      canvas.height = height;
      canvas.getContext("2d").drawImage(img, 0, 0, width, height);
      canvas.toBlob(blob => {
        const compressed = new File([blob], file.name, { type: file.type });
        callback(compressed);
      }, file.type, 0.7);
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

function handleFiles(files) {
  if ((mediaFiles.length + files.length) > MAX_FILES) return alert("⚠️ Max 20 files allowed");
  Array.from(files).forEach(file => {
    const isImage = file.type.startsWith("image/");
    const isVideo = file.type.startsWith("video/");
    if (!isImage && !isVideo) return;

    const maxSize = isVideo ? 100 * 1024 * 1024 : 15 * 1024 * 1024;
    if (file.size > maxSize) return alert(`⚠️ ${file.name} too large`);

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
}

function renderPreviews() {
  previewGrid.innerHTML = "";
  mediaFiles.forEach((media, index) => {
    const isVideo = media.file.type.startsWith("video/");
    const item = document.createElement("div");
    item.className = "preview-item";
    item.innerHTML = `
      ${isVideo ? `<video src="${media.url}" class="preview-media" controls></video>` : `<img src="${media.url}" class="preview-media">`}
      <button class="remove-btn" onclick="removeFile(${index})">&times;</button>
    `;
    item.addEventListener("click", e => {
      if (e.target.classList.contains("remove-btn")) return;
      zoomModal.innerHTML = `<${isVideo ? 'video controls autoplay' : 'img'} src="${media.url}" />`;
      zoomModal.style.display = "flex";
    });
    previewGrid.appendChild(item);
  });
}

function removeFile(index) {
  const media = mediaFiles[index];
  if (media.file.type.startsWith("video/")) {
    document.querySelectorAll(`video[src="${media.url}"]`).forEach(v => {
      v.pause(); v.src = ""; v.load();
    });
  }
  URL.revokeObjectURL(media.url);
  mediaFiles.splice(index, 1);
  renderPreviews();
}

zoomModal.addEventListener("click", () => {
  const video = zoomModal.querySelector("video");
  if (video) {
    video.pause();
    video.src = "";
    video.load();
  }
  zoomModal.innerHTML = "";
  zoomModal.style.display = "none";
});

function uploadMedia(callback) {
  if (mediaFiles.length === 0) return alert("No media to upload.");
  const formData = new FormData();
  mediaFiles.forEach(media => formData.append("media_files", media.file));
  progressContainer.style.display = "block";
  progressBar.style.width = "0%";
  statusText.textContent = "";
  progressBar.style.backgroundColor = "#2ecc71";

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload_media_temp", true);

  xhr.upload.addEventListener("progress", e => {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      progressBar.style.width = percent + "%";
    }
  });

  xhr.onload = () => {
    if (xhr.status === 200) {
      const res = JSON.parse(xhr.responseText);
      statusText.textContent = res.message || "✅ Uploaded!";
      callback(res.saved_paths);
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
