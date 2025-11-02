
// ✅ uploader.js — Handles image & video previews with delete + play overlay

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const previewContainer = document.getElementById("preview-container");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", e => {
  e.preventDefault();
  dropzone.style.borderColor = "#007bff";
});
dropzone.addEventListener("dragleave", () => {
  dropzone.style.borderColor = "#aaa";
});
dropzone.addEventListener("drop", e => {
  e.preventDefault();
  dropzone.style.borderColor = "#aaa";
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener("change", () => handleFiles(fileInput.files));

function handleFiles(files) {
  [...files].forEach(file => {
    const ext = file.name.split('.').pop().toLowerCase();
    const reader = new FileReader();
    reader.onload = () => {
      let wrapper = document.createElement("div");
      wrapper.className = ext === "mp4" ? "video-thumb-wrapper" : "preview-thumb";
      
      let closeBtn = document.createElement("div");
      closeBtn.className = "preview-x";
      closeBtn.textContent = "×";
      closeBtn.onclick = () => wrapper.remove();

      if (["mp4", "mov", "webm"].includes(ext)) {
        wrapper.innerHTML = `
          <video muted preload="metadata" style="background:#000;">
            <source src="${reader.result}">
          </video>
          <div class="play-overlay">▶</div>
        `;
      } else {
        let img = document.createElement("img");
        img.src = reader.result;
        wrapper.appendChild(img);
      }
      wrapper.appendChild(closeBtn);
      previewContainer.appendChild(wrapper);
    };
    reader.readAsDataURL(file);
  });
}
