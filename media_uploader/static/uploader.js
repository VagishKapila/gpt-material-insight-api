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
document.addEventListener("dragover", e => e.preventDefault());
document.addEventListener("drop", e => {
  e.preventDefault();
  if (e.dataTransfer && e.dataTransfer.files.length) {
    handleFiles(e.dataTransfer.files);
  }
});

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
      const ctx = canvas.getContext("2d");
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

function handleFiles(files) {
  const totalCount = mediaFiles.length + files.length;
  if (totalCount > MAX_FILES) return alert("⚠️ Max 20 files allowed");

  Array.from(files).forEach(file => {
    const isImage = file.type.startsWith("image/");
    const isVideo = file.type.startsWith("video/");
    if (!isImage && !isVideo) return;

    const maxSize = isVideo ? 100 * 1024 * 1024 : 15 * 1024 * 1024;
    if (file.size > maxSize) {
      const readable = isVideo ? "100 MB (video)" : "15 MB (image)";
      alert(`⚠️ ${file.name} too large. Max allowed: ${readable}`);
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
}

function renderPreviews() {
  previewGrid.innerHTML = "";
  mediaFiles.forEach((media, index) => {
    const isVideo = media.file.type.startsWith("video/");
    const item = document.createElement("div");
    item.className = "preview-item";

    item.innerHTML = `
  ${isVideo 
    ? `<video src="${media.url}" class="preview-media" controls></video>` 
    : `<img src="${media.url}" class="preview-media" />`
  }
  <button class="remove-btn" onclick="removeFile(${index})">&times;</button>
  `;

    item.addEventListener('click', (e) => {
  // Prevent zoom if ❌ was clicked
  if (e.target.classList.contains("remove-btn")) return;

  zoomModal.innerHTML = `<${isVideo ? 'video controls autoplay' : 'img'} src="${media.url}" />`;
  zoomModal.style.display = "flex";
  });

    previewGrid.appendChild(item);
  });
}

// 🧹 Updated removeFile() — Stops videos + Frees memory
function removeFile(index) {
  const media = mediaFiles[index];

  // 🛑 Stop video playback before removing
  if (media && media.file.type.startsWith("video/")) {
    const videos = document.querySelectorAll(`video[src="${media.url}"]`);
    videos.forEach(v => {
      v.pause();
      v.src = "";
      v.load();
    });
  }

  // 🧠 Free up memory for all types
  if (media && media.url) {
    URL.revokeObjectURL(media.url);
  }

  mediaFiles.splice(index, 1);
  renderPreviews();
}

function uploadMedia() {
  if (mediaFiles.length === 0) return alert("No media to upload.");

  const formData = new FormData();
  mediaFiles.forEach(media => formData.append("media_files", media.file));

  progressContainer.style.display = "block";
  progressBar.style.width = "0%";
  statusText.textContent = "";
  progressBar.style.backgroundColor = "#2ecc71";

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload_media_test", true);

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

// 🖱️ Button trigger
dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => handleFiles(e.target.files));

// 🚫 Stop video & close zoom when modal is clicked
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
