// uploader.js — Handles preview + delete + zoom for images & videos

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const previewContainer = document.getElementById("preview-container");

function openModal(src, type) {
  const modal = document.getElementById("mediaModal");
  const img = document.getElementById("modalImage");
  const vid = document.getElementById("modalVideo");

  if (type === 'image') {
    img.src = src;
    img.style.display = "block";
    vid.pause();
    vid.style.display = "none";
  } else {
    vid.src = src;
    vid.style.display = "block";
    img.style.display = "none";
  }
  modal.style.display = "block";
}

function closeModal() {
  const modal = document.getElementById("mediaModal");
  const vid = document.getElementById("modalVideo");
  vid.pause();
  modal.style.display = "none";
}

function handleFiles(files) {
  [...files].forEach(file => {
    const ext = file.name.split('.').pop().toLowerCase();
    const reader = new FileReader();

    reader.onload = () => {
      const url = reader.result;
      const wrapper = document.createElement("div");
      wrapper.className = "media-wrapper";

      const deleteBtn = document.createElement("span");
      deleteBtn.className = "delete-button";
      deleteBtn.innerHTML = "&times;";
      deleteBtn.onclick = () => wrapper.remove();

      if (["mp4", "mov", "webm"].includes(ext)) {
        const thumb = document.createElement("div");
        thumb.className = "video-thumb-wrapper";
        thumb.innerHTML = `
          <div class="play-overlay">▶</div>
          <video class="preview-thumb" src="${url}" muted></video>
        `;
        thumb.onclick = () => openModal(url, 'video');
        wrapper.appendChild(deleteBtn);
        wrapper.appendChild(thumb);
      } else {
        const img = document.createElement("img");
        img.src = url;
        img.className = "preview-thumb";
        img.onclick = () => openModal(url, 'image');
        wrapper.appendChild(deleteBtn);
        wrapper.appendChild(img);
      }

      previewContainer.appendChild(wrapper);
    };

    reader.readAsDataURL(file);
  });
}

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
  fileInput.files = e.dataTransfer.files;
});

fileInput.addEventListener("change", () => {
  handleFiles(fileInput.files);
});
