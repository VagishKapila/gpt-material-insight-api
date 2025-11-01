// ✅ uploader.js — Handles image & video previews with zoom/play modal

// Store preview container and input
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const previewContainer = document.getElementById("preview-container");

let modal = null;

// ✅ Create modal overlay (once)
function createModal() {
  modal = document.createElement("div");
  modal.id = "media-modal";
  modal.innerHTML = `
    <div class="modal-content" id="modal-content"></div>
    <span class="modal-close" onclick="closeModal()">&times;</span>
  `;
  modal.style.display = "none";
  document.body.appendChild(modal);
}

function openModal(innerHtml) {
  const content = document.getElementById("modal-content");
  content.innerHTML = innerHtml;
  modal.style.display = "flex";
}

function closeModal() {
  modal.style.display = "none";
  document.getElementById("modal-content").innerHTML = "";
}

// ✅ Handle file selection
function handleFiles(files) {
  [...files].forEach(file => {
    const ext = file.name.split('.').pop().toLowerCase();
    const reader = new FileReader();

    reader.onload = () => {
      const url = reader.result;
      let el;

      if (["mp4", "mov", "webm"].includes(ext)) {
        el = document.createElement("div");
        el.className = "video-thumb-wrapper";
        el.innerHTML = `
          <div class="play-overlay">▶</div>
          <video class="preview-thumb" src="${url}" muted></video>
        `;
        el.onclick = () => openModal(`<video src='${url}' controls autoplay style='max-width:90vw; max-height:80vh'></video>`);
      } else {
        el = document.createElement("img");
        el.src = url;
        el.className = "preview-thumb";
        el.onclick = () => openModal(`<img src='${url}' style='max-width:90vw; max-height:80vh'/>`);
      }

      previewContainer.appendChild(el);
    };
    reader.readAsDataURL(file);
  });
}

// ✅ Drag & drop behavior
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.style.borderColor = "#007bff";
});
dropzone.addEventListener("dragleave", () => {
  dropzone.style.borderColor = "#aaa";
});
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.style.borderColor = "#aaa";
  handleFiles(e.dataTransfer.files);
  fileInput.files = e.dataTransfer.files; // to preserve submission
});

fileInput.addEventListener("change", () => {
  handleFiles(fileInput.files);
});

// ✅ Initialize modal on load
window.onload = createModal;
