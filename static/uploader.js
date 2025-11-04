// ✅ uploader.js — handles previews, modal zoom, delete buttons

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const previewContainer = document.getElementById("preview-container");

  function createThumb(file, url) {
    const ext = file.name.split(".").pop().toLowerCase();
    const wrapper = document.createElement("div");
    wrapper.className = "thumb-wrapper";

    const closeBtn = document.createElement("span");
    closeBtn.className = "thumb-close";
    closeBtn.innerHTML = "&times;";
    closeBtn.onclick = () => wrapper.remove();

    if (["mp4", "mov", "webm"].includes(ext)) {
      wrapper.innerHTML += `
        <div class="video-thumb">
          <video src="${url}" muted></video>
          <div class="play-overlay">▶</div>
        </div>
      `;
      wrapper.querySelector(".video-thumb").onclick = () => openModal(`<video src='${url}' controls autoplay></video>`);
    } else {
      const img = document.createElement("img");
      img.src = url;
      img.className = "preview-thumb";
      img.onclick = () => openModal(`<img src='${url}'/>`);
      wrapper.appendChild(img);
    }
    wrapper.appendChild(closeBtn);
    previewContainer.appendChild(wrapper);
  }

  function handleFiles(files) {
    [...files].forEach(file => {
      const reader = new FileReader();
      reader.onload = () => createThumb(file, reader.result);
      reader.readAsDataURL(file);
    });
  }

  dropzone.onclick = () => fileInput.click();
  dropzone.ondragover = e => {
    e.preventDefault();
    dropzone.classList.add("drag-over");
  };
  dropzone.ondragleave = () => dropzone.classList.remove("drag-over");
  dropzone.ondrop = e => {
    e.preventDefault();
    dropzone.classList.remove("drag-over");
    handleFiles(e.dataTransfer.files);
  };

  fileInput.addEventListener("change", () => handleFiles(fileInput.files));

  // Modal logic
  const modal = document.getElementById("mediaModal");
  const modalImg = document.getElementById("modalImage");
  const modalVideo = document.getElementById("modalVideo");
  const close = document.querySelector(".close");

  window.openModal = (html) => {
    if (html.includes("video")) {
      modalVideo.src = html.match(/src='(.*?)'/)[1];
      modalVideo.style.display = "block";
      modalImg.style.display = "none";
    } else {
      modalImg.src = html.match(/src='(.*?)'/)[1];
      modalImg.style.display = "block";
      modalVideo.pause();
      modalVideo.style.display = "none";
    }
    modal.style.display = "block";
  };

  window.closeModal = () => {
    modal.style.display = "none";
    modalImg.src = "";
    modalVideo.pause();
    modalVideo.src = "";
  };
});
