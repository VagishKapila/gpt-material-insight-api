const dropzone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const uploadStatus = document.getElementById('upload-status');
const addMoreBtn = document.getElementById("add-more-btn");

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

addMoreBtn.addEventListener("click", () => fileInput.click());
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
  previewContainer.innerHTML = "";
  mediaFiles.forEach((media, index) => {
    const isVideo = media.file.type.startsWith("video/");
    const item = document.createElement("div");
    item.className = "preview-item";

    const mediaTag = document.createElement(isVideo ? "video" : "img");
    mediaTag.src = media.url;
    mediaTag.className = "preview-media";
    if (isVideo) mediaTag.controls = true;

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.innerHTML = "❌";
    removeBtn.onclick = (e) => {
      e.stopPropagation(); // don’t open zoom
      mediaFiles.splice(index, 1);
      renderPreviews();
    };

    item.appendChild(mediaTag);
    item.appendChild(removeBtn);

    item.addEventListener("click", () => zoomPreview(media.url, isVideo ? "video" : "img"));
    previewContainer.appendChild(item);
  });
}

function zoomPreview(src, type) {
  const modal = document.getElementById("zoom-modal");
  modal.innerHTML = "";
  const media = document.createElement(type);
  media.src = src;
  media.controls = true;
  media.style.maxWidth = "90%";
  media.style.maxHeight = "90%";
  modal.appendChild(media);
  modal.style.display = "flex";
}

function uploadFiles() {
  if (mediaFiles.length === 0) return alert("No media to upload.");

  const formData = new FormData();
  mediaFiles.forEach(media => formData.append("media_files", media.file));

  uploadStatus.textContent = "⏳ Uploading...";
  uploadStatus.style.color = "black";

  fetch("/upload_media_test", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      uploadStatus.textContent = data.message || "✅ Upload complete!";
      uploadStatus.style.color = "green";
    })
    .catch(err => {
      console.error(err);
      uploadStatus.textContent = "❌ Upload error";
      uploadStatus.style.color = "red";
    });
}
