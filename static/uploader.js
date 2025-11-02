const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const previewContainer = document.getElementById("preview-container");

function openModalContent(type, src) {
  const modal = document.getElementById("mediaModal");
  const img = document.getElementById("modalImage");
  const vid = document.getElementById("modalVideo");

  if (type === 'image') {
    img.src = src;
    img.style.display = "block";
    vid.style.display = "none";
    vid.pause();
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

// Process file previews
function handleFiles(files) {
  [...files].forEach(file => {
    const ext = file.name.split('.').pop().toLowerCase();
    const reader = new FileReader();

    reader.onload = () => {
      const url = reader.result;

      if (["mp4", "mov", "webm"].includes(ext)) {
        const wrapper = document.createElement("div");
        wrapper.className = "video-thumb-wrapper";
        wrapper.innerHTML = `
          <video class="preview-thumb" src="${url}" muted></video>
          <div class="play-overlay">▶</div>
        `;
        wrapper.onclick = () => openModalContent("video", url);
        previewContainer.appendChild(wrapper);
      } else {
        const img = document.createElement("img");
        img.src = url;
        img.className = "preview-thumb";
        img.onclick = () => openModalContent("image", url);
        previewContainer.appendChild(img);
      }
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

fileInput.addEventListener("change", () => handleFiles(fileInput.files));
