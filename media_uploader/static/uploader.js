let selectedFiles = [];
const previewContainer = document.getElementById("preview-container");
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const zoomModal = document.getElementById("zoom-modal");
const uploadStatus = document.getElementById("upload-status");
const progressBar = document.getElementById("progress-bar");

document.getElementById("add-more-btn").addEventListener("click", () => fileInput.click());

// ✅ Global drag/drop protection — prevents browser from opening files on drop
window.addEventListener("dragover", (e) => {
  e.preventDefault();
});

window.addEventListener("drop", (e) => {
  e.preventDefault();
});

// ✅ FULL-PAGE DROP HANDLER
document.body.addEventListener("drop", (e) => {
  e.preventDefault();
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener("change", (e) => {
  handleFiles(e.target.files);
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
  for (let file of files) {
    selectedFiles.push(file);
    const previewItem = document.createElement("div");
    previewItem.className = "preview-item";

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.innerText = "❌";
    removeBtn.onclick = () => {
      selectedFiles = selectedFiles.filter(f => f !== file);
      previewItem.remove();
    };

    // 📷 Image preview
    if (file.type.startsWith("image")) {
      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.onclick = () => zoomPreview(img.src, "img");
      previewItem.append(img);

    // 🎥 Video preview
    } else if (file.type.startsWith("video")) {
      const video = document.createElement("video");
      video.src = URL.createObjectURL(file);
      video.controls = true;
      video.onclick = () => zoomPreview(video.src, "video");
      previewItem.append(video);
    }

    previewItem.append(removeBtn);
    previewContainer.append(previewItem);
  }
}

function zoomPreview(src, type) {
  zoomModal.innerHTML = "";
  const media = document.createElement(type);
  media.src = src;
  media.controls = true;
  media.style.maxWidth = "90vw";
  media.style.maxHeight = "90vh";
  if (type === "video") media.autoplay = true;
  zoomModal.append(media);
  zoomModal.style.display = "flex";

  // Click outside to close
  zoomModal.onclick = () => {
    zoomModal.style.display = "none";
  };
}

async function uploadFiles() {
  const formData = new FormData();
  selectedFiles.forEach((file) => {
    formData.append("media_files", file);
  });

  uploadStatus.innerHTML = "⏳ Uploading...";
  uploadStatus.style.color = "black";
  progressBar.style.width = "0%";

  try {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload_media_test");

    // 🔁 Progress event
    xhr.upload.onprogress = function (e) {
      if (e.lengthComputable) {
        const percent = (e.loaded / e.total) * 100;
        progressBar.style.width = percent + "%";
      }
    };

    xhr.onload = function () {
      if (xhr.status === 200) {
        uploadStatus.innerHTML = `✅ Uploaded ${selectedFiles.length} file(s) successfully.`;
        uploadStatus.style.color = "green";
      } else {
        uploadStatus.innerHTML = "❌ Upload failed";
        uploadStatus.style.color = "red";
      }
    };

    xhr.onerror = function () {
      uploadStatus.innerHTML = "❌ Upload failed";
      uploadStatus.style.color = "red";
    };

    xhr.send(formData);
  } catch (err) {
    console.error("[Upload Error]", err);
    uploadStatus.innerHTML = "❌ Upload failed";
    uploadStatus.style.color = "red";
  }
}
