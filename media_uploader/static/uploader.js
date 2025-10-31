const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('previewGrid');
const moreBtn = document.getElementById('more-btn');
const resetBtn = document.getElementById('upload-reset');

let mediaFiles = [];
let showAll = false;
const MAX_FILES = 20;

function toggleMore() {
  showAll = !showAll;
  renderPreviews();
}

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
  const filesToShow = showAll ? mediaFiles : mediaFiles.slice(0, 6);
  filesToShow.forEach((media, index) => {
    const item = document.createElement("div");
    item.className = "preview-item";
    const isVideo = media.file.type.startsWith("video/");
    item.innerHTML = `
      <${isVideo ? 'video controls' : 'img'} src="${media.url}" />
      <button class="remove-btn" onclick="removeFile(${index})">&times;</button>
    `;
    previewGrid.appendChild(item);
  });
  moreBtn.style.display = mediaFiles.length > 6 ? "block" : "none";
  moreBtn.textContent = showAll ? "− Hide Extra Media" : "+ Show More Media";
}

function removeFile(index) {
  mediaFiles.splice(index, 1);
  renderPreviews();
}

function resetUploader() {
  mediaFiles = [];
  showAll = false;
  renderPreviews();
  document.getElementById("progress-container").style.display = "none";
  document.getElementById("progress-bar").style.width = "0%";
  document.getElementById("upload-status").textContent = "";
  resetBtn.style.display = "none";
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
      resetBtn.style.display = "block";
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
