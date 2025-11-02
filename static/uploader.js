const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const previewContainer = document.getElementById("preview-container");

function createMediaThumb(url, type) {
  const wrapper = document.createElement("div");
  wrapper.className = "media-wrapper";

  if (type === "video") {
    const placeholder = document.createElement("div");
    placeholder.className = "media-thumb";
    placeholder.style.background = "#000";
    placeholder.innerHTML = "<div class='play-overlay'>▶️</div>";
    wrapper.appendChild(placeholder);

    wrapper.onclick = () => openModal(url, 'video');
  } else {
    const img = document.createElement("img");
    img.src = url;
    img.className = "media-thumb";
    img.onclick = () => openModal(url, 'image');
    wrapper.appendChild(img);
  }

  // Add X button
  const closeBtn = document.createElement("span");
  closeBtn.className = "close-btn";
  closeBtn.innerHTML = "&times;";
  closeBtn.onclick = () => previewContainer.removeChild(wrapper);
  wrapper.appendChild(closeBtn);

  previewContainer.appendChild(wrapper);
}

function handleFiles(files) {
  [...files].forEach(file => {
    const reader = new FileReader();
    reader.onload = () => {
      const ext = file.name.split('.').pop().toLowerCase();
      const url = reader.result;
      const type = ["mp4", "mov", "webm"].includes(ext) ? "video" : "image";
      createMediaThumb(url, type);
    };
    reader.readAsDataURL(file);
  });
}

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("active"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("active"));
dropzone.addEventListener("drop", e => {
  e.preventDefault();
  dropzone.classList.remove("active");
  const files = e.dataTransfer.files;
  fileInput.files = files;
  handleFiles(files);
});

fileInput.addEventListener("change", () => handleFiles(fileInput.files));

function openModal(src, type) {
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
  modal.style.display = "none";
  vid.pause();
}
