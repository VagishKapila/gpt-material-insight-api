let selectedFiles = [];
const previewContainer = document.getElementById("preview-container");
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const zoomModal = document.getElementById("zoom-modal");
const uploadStatus = document.getElementById("upload-status");

document.getElementById("add-more-btn").addEventListener("click", () => fileInput.click());

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

    if (file.type.startsWith("image")) {
      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.onclick = () => zoomPreview(img.src, "img");
      previewItem.append(img);
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
  if (type === "video") media.autoplay = true;
  zoomModal.append(media);
  zoomModal.style.display = "flex";
}

async function uploadFiles() {
  const formData = new FormData();
  selectedFiles.forEach((file) => {
    formData.append("files", file);
  });

  uploadStatus.innerHTML = "⏳ Uploading...";
  uploadStatus.style.color = "black";

  try {
    const res = await fetch("/upload_media_test", {
      method: "POST",
      body: formData
    });
    const result = await res.json();

    if (result.success) {
      uploadStatus.innerHTML = `✅ Uploaded ${selectedFiles.length} file(s) successfully.`;
      uploadStatus.style.color = "green";
    } else {
      throw new Error("Upload failed");
    }
  } catch (err) {
    console.error(err);
    uploadStatus.innerHTML = "❌ Upload failed";
    uploadStatus.style.color = "red";
  }
}
