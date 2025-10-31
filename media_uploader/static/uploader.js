const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('previewGrid');

let mediaFiles = [];

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

function compressImage(file, callback) {
  const img = new Image();
  const reader = new FileReader();
  reader.onload = e => {
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const maxDim = 1600;
      let width = img.width;
      let height = img.height;
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
    const wrapper = document.createElement("div");
    wrapper.className = "preview-item";

    if (isVideo) {
      wrapper.innerHTML = `
        <video src="${media.url}" muted></video>
        <button class="remove-btn" onclick="removeFile(${index})">&times;</button>
        <div class="play-overlay">▶️</div>
      `;
      wrapper.querySelector("video").addEventListener("click", () => openZoomVideo(media.url));
    } else {
      wrapper.innerHTML = `
        <img src="${media.url}" />
        <button class="remove-btn" onclick="removeFile(${index})">&times;</button>
      `;
      wrapper.querySelector("img").addEventListener("click", () => openZoomImage(media.url));
    }

    previewGrid.appendChild(wrapper);
  });
}

function removeFile(index) {
  mediaFiles.splice(index, 1);
  renderPreviews();
}

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

/* ---------- ZOOM MODAL ---------- */
function openZoomImage(url) {
  document.getElementById("zoomImage").src = url;
  document.getElementById("zoomImage").style.display = "block";
  document.getElementById("zoomVideo").style.display = "none";
  document.getElementById("zoomModal").style.display = "flex";
}

function openZoomVideo(url) {
  const video = document.getElementById("zoomVideo");
  video.src = url;
  video.style.display = "block";
  document.getElementById("zoomImage").style.display = "none";
  document.getElementById("zoomModal").style.display = "flex";
}

function closeZoom() {
  document.getElementById("zoomModal").style.display = "none";
  document.getElementById("zoomImage").src = "";
  document.getElementById("zoomVideo").pause();
  document.getElementById("zoomVideo").src = "";
}
