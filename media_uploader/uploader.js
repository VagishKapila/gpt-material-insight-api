const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');

dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', e => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', () => {
  handleFiles(fileInput.files);
});

function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) return;

    compressAndPreview(file);
  });
}

function compressAndPreview(file) {
  const isImage = file.type.startsWith('image/');
  const isVideo = file.type.startsWith('video/');

  const reader = new FileReader();
  reader.onload = function (e) {
    const previewBox = document.createElement('div');
    previewBox.classList.add('preview-item');

    const media = document.createElement(isImage ? 'img' : 'video');
    media.src = e.target.result;
    if (isVideo) {
      media.controls = true;
    }

    const removeBtn = document.createElement('button');
    removeBtn.textContent = '×';
    removeBtn.classList.add('remove-btn');
    removeBtn.onclick = () => previewContainer.removeChild(previewBox);

    previewBox.appendChild(media);
    previewBox.appendChild(removeBtn);
    previewContainer.appendChild(previewBox);
  };

  if (isImage) {
    const imgReader = new Image();
    reader.onload = function (e) {
      imgReader.src = e.target.result;
      imgReader.onload = function () {
        const canvas = document.createElement('canvas');
        const scale = Math.min(800 / imgReader.width, 800 / imgReader.height);
        canvas.width = imgReader.width * scale;
        canvas.height = imgReader.height * scale;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(imgReader, 0, 0, canvas.width, canvas.height);
        const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.7);
        reader.onload = null;
        reader.result = compressedDataUrl;
        reader.onload({ target: { result: compressedDataUrl } });
      };
    };
  }

  reader.readAsDataURL(file);
}
function uploadMedia() {
  if (mediaFiles.length === 0) {
    return alert("No media to upload.");
  }

  const formData = new FormData();
  mediaFiles.forEach((media, i) => {
    formData.append("media_files", media.file);
  });

  fetch("/upload_media_test", {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById("upload-status").textContent = data.message || "✅ Uploaded!";
  })
  .catch(err => {
    console.error("Upload error:", err);
    document.getElementById("upload-status").textContent = "❌ Upload failed";
  });
}
