// ✅ uploader.js — handles image + video previews with X and modal

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const previewContainer = document.getElementById("preview-container");

dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("highlight");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("highlight");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("highlight");
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener("change", () => {
  handleFiles(fileInput.files);
});

function handleFiles(files) {
  [...files].forEach((file) => {
    const ext = file.name.split(".").pop().toLowerCase();
    const reader = new FileReader();

    reader.onload = () => {
      const url = reader.result;
      const wrapper = document.createElement("div");
      wrapper.className = "media-wrapper";

      const x = document.createElement("span");
      x.className = "delete-x";
      x.innerHTML = "&times;";
      x.onclick = () => wrapper.remove();

      if (["mp4", "mov", "webm"].includes(ext)) {
        wrapper.innerHTML += `
          <div class="video-thumb-wrapper">
            <img src="/static/video_placeholder.png" class="media-thumb" />
            <div class="play-overlay">▶</div>
          </div>
        `;
        wrapper.onclick = () =>
          openModal(`<video src='${url}' controls autoplay style='max-width:90vw; max-height:80vh'></video>`);
      } else {
        const img = document.createElement("img");
        img.src = url;
        img.className = "media-thumb";
        img.onclick = () =>
          openModal(`<img src='${url}' style='max-width:90vw; max-height:80vh' />`);
        wrapper.appendChild(img);
      }

      wrapper.appendChild(x);
      previewContainer.appendChild(wrapper);
    };

    reader.readAsDataURL(file);
  });
}

// Modal logic
function openModal(content) {
  const modal = document.getElementById("mediaModal");
  const modalImg = document.getElementById("modalImage");
  const modalVid = document.getElementById("modalVideo");

  if (content.includes("<video")) {
    modalVid.src = content.match(/src='(.*?)'/)[1];
    modalVid.style.display = "block";
    modalImg.style.display = "none";
  } else {
    modalImg.src = content.match(/src='(.*?)'/)[1];
    modalImg.style.display = "block";
    modalVid.style.display = "none";
  }

  modal.style.display = "block";
}

function closeModal() {
  const modal = document.getElementById("mediaModal");
  const modalVid = document.getElementById("modalVideo");
  modalVid.pause();
  modal.style.display = "none";
}
