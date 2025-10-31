const dropzone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const zoomModal = document.getElementById('zoom-modal');
const uploadStatus = document.getElementById('upload-status');

let mediaFiles = [];
const MAX_FILES = 20;

// ✅ Global drag & drop (entire window)
document.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

document.addEventListener("dragleave", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
});

document.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer?.files?.length) {
    handleFiles(e.dataTransfer.files);
  }
});

// 📦 Compress images client-side before upload
function compressImage(file, callback) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const maxDim = 1600;
      let { width, height } = img;

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

      canvas.toBlob((blob) => {
        const compressed = new File([blob], file.name, { type: file.type });
        callback(compressed);
      }, file.type, 0.7);
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

// 📁 Handle image & video files
function handleFiles(files) {
  if (mediaFiles.length + files.length > MAX_FILES) {
    alert("⚠️ Max 20 files allowed.");
    return;
  }

  Array.from(files).forEach((file) => {
    const isImage = file.type.startsWith("image/");
    const isVideo = file.type.startsWith("video/");
    if (!isImage && !isVideo) return;

    const maxSize = isVideo ? 100 * 1024 * 1024 : 15 * 1024 * 1024;
    if (file.size > maxSize) {
      alert(`⚠️ ${file.name} too large. Max allowed: ${maxSize / 1024 / 1024} MB`);
      return;
    }

    const addMedia = (f) => {
      mediaFiles.push({ file: f, url: URL.createObjectURL(f) });
      renderPreviews();
    };

    if (isImage) {
      compressImage(file, addMedia);
    } else {
      addMedia(file);
    }
  });
}

// 🖼️ Render preview grid
function renderPreviews() {
  previewContainer.innerHTML = "";
  mediaFiles.forEach((media, index) => {
    const isVideo = media.file.type.startsWith("video/");
    const item = document.createElement("div");
    item.className = "preview-item";

    item.innerHTML = `
      <${isVideo ? 'video controls' : 'img'} src="${media.url}" />
      <button class="remove-btn" onclick="removeFile(${index})">❌</button>
    `;

    item.querySelector(isVideo ? 'video' : 'img').onclick = () => {
      zoomPreview(media.url, isVideo ? "video" : "img");
    };

    previewContainer.appendChild(item);
  });
}

// 🔍 Zoom modal
function zoomPreview(src, type) {
  zoomModal.innerHTML = "";
  const el = document.createElement(type);
  el.src = src;
  el.controls = true;
  if (type === "video") el.autoplay = true;
  el.style.maxWidth = "90%";
  el.style.maxHeight = "80%";
  zoomModal.appendChild(el);
  zoomModal.style.display = "flex";
}

// ❌ Remove file from queue
function removeFile(index) {
  mediaFiles.splice(index, 1);
  renderPreviews();
}

// ⬆️ Upload logic
function uploadFiles() {
  if (!mediaFiles.length) return alert("No media selected.");

  const formData = new FormData();
  mediaFiles.forEach((media) => formData.append("media_files", media.file));

  uploadStatus.textContent = "⏳ Uploading...";
  uploadStatus.style.color = "#333";

  fetch("/upload_media_test", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      uploadStatus.textContent = data.message || "✅ Upload complete!";
      uploadStatus.style.color = "green";
    })
    .catch((err) => {
      console.error(err);
      uploadStatus.textContent = "❌ Upload failed.";
      uploadStatus.style.color = "red";
    });
}

// ➕ Button to add more
document.getElementById("add-more-btn").onclick = () => fileInput.click();
fileInput.addEventListener("change", (e) => handleFiles(e.target.files));

// 🧼 Zoom modal close on click outside
zoomModal.onclick = () => {
  zoomModal.style.display = "none";
};
