const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('preview-container');
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const statusText = document.getElementById("upload-status");
const zoomModal = document.getElementById("zoom-modal");

let mediaFiles = [];
const MAX_FILES = 20;

// 🌐 Global drag & drop support
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
      if (e.target.classList.contains("remove-btn")) return;
      zoomModal.innerHTML = `<${isVideo ? 'video controls autoplay' : 'img'} src="${media.url}" />`;
      zoomModal.style.display = "flex";
    });

    previewGrid.appendChild(item);
  });
}

function removeFile(index) {
  const media = mediaFiles[index];
  if (media && media.file.type.startsWith("video/")) {
    const videos = document.querySelectorAll(`video[src="${media.url}"]`);
    videos.forEach(v => {
      v.pause();
      v.src = "";
      v.load();
    });
  }

  if (media && media.url) {
    URL.revokeObjectURL(media.url);
  }

  mediaFiles.splice(index, 1);
  renderPreviews();
}

// 🛑 Stop video if modal is clicked
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

// Trigger input
dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => handleFiles(e.target.files));
