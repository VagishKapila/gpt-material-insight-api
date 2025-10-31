// =============================
// 🧠 uploader.js — Modular + Debug-Friendly
// =============================

// --- File storage ---
let selectedFiles = [];

// --- DOM Elements ---
const previewContainer = document.getElementById("preview-container");
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const zoomModal = document.getElementById("zoom-modal");
const uploadStatus = document.getElementById("upload-status");

// --- Add More Files button ---
document.getElementById("add-more-btn").addEventListener("click", () => fileInput.click());

// --- File Input Change Event ---
fileInput.addEventListener("change", (e) => {
  console.log("[DEBUG] Files selected via file input:", e.target.files);
  handleFiles(e.target.files);
});

// --- Drag and Drop Handlers ---
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
  console.log("[DEBUG] Files dropped:", e.dataTransfer.files);
  handleFiles(e.dataTransfer.files);
});

// =============================
// 🖼️ Handle Previews (Images + Videos)
// =============================
function handleFiles(files) {
  for (let file of files) {
    selectedFiles.push(file);
    console.log(`[DEBUG] Added file: ${file.name}, type: ${file.type}`);

    const previewItem = document.createElement("div");
    previewItem.className = "preview-item";

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.innerText = "❌";
    removeBtn.onclick = () => {
      selectedFiles = selectedFiles.filter(f => f !== file);
      previewItem.remove();
      console.log(`[DEBUG] Removed file: ${file.name}`);
    };

    // --- Image Preview ---
    if (file.type.startsWith("image")) {
      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.onclick = () => zoomPreview(img.src, "img");
      previewItem.append(img);

    // --- Video Preview ---
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

// =============================
// 🔍 Zoom Modal (Lightbox Effect)
// =============================
function zoomPreview(src, type) {
  zoomModal.innerHTML = "";
  const media = document.createElement(type);
  media.src = src;
  media.controls = true;
  if (type === "video") media.autoplay = true;
  zoomModal.append(media);
  zoomModal.style.display = "flex";
  console.log(`[DEBUG] Zooming ${type}: ${src}`);
}

// =============================
// 🚀 Upload Function (to Flask Server)
// =============================
async function uploadFiles() {
  const formData = new FormData();

  // ✅ Fix: use correct Flask key "media_files"
  selectedFiles.forEach((file) => {
    formData.append("media_files", file);
  });

  uploadStatus.innerHTML = "⏳ Uploading...";
  uploadStatus.style.color = "black";

  try {
    console.log("[DEBUG] Upload started for", selectedFiles.length, "files");

    const res = await fetch("/upload_media_test", {
      method: "POST",
      body: formData
    });

    const result = await res.json();
    console.log("[DEBUG] Server response:", result);

    // ✅ Fix: handle both success and fallback
    if (res.ok) {
      uploadStatus.innerHTML = `✅ Uploaded ${selectedFiles.length} file(s) successfully.`;
      uploadStatus.style.color = "green";
    } else {
      throw new Error("Upload failed");
    }
  } catch (err) {
    console.error("[ERROR] Upload failed:", err);
    uploadStatus.innerHTML = "❌ Upload failed";
    uploadStatus.style.color = "red";
  }
}
