import React, { useState } from 'react';
import axios from 'axios';
import Dropzone from 'react-dropzone';
import imageCompression from 'browser-image-compression';

export default function DailyLogUploader() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [pdfUrl, setPdfUrl] = useState("");

  const compressFiles = async (incoming: File[]) => {
    const compressed: File[] = [];
    for (const file of incoming) {
      if (file.type.startsWith('image/')) {
        const compressedFile = await imageCompression(file, {
          maxSizeMB: 1,
          maxWidthOrHeight: 1024,
          useWebWorker: true,
        });
        compressed.push(compressedFile as File);
      } else {
        compressed.push(file);
      }
    }
    return compressed;
  };

  const handleUpload = async () => {
    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append("project_name", "Upper Oaks San Rafael");
    formData.append("client_name", "Sample Client");
    formData.append("location", "San Rafael, CA");
    formData.append("date", new Date().toISOString().split("T")[0]);
    formData.append("weather", "Sunny 75°F");
    formData.append("work_done", "Demo, trenching, concrete slab");
    formData.append("safety_notes", "Tailgate complete, no incidents");
    formData.append("enable_ai", "on");

    const compressed = await compressFiles(files);
    compressed.forEach(file => {
      if (file.name.match(/\.(png|jpe?g)$/i)) {
        formData.append("images", file);
      } else if (file.name.includes("scope")) {
        formData.append("scope_doc", file);
      } else if (file.name.includes("safety")) {
        formData.append("safety_sheet", file);
      } else if (file.name.includes("logo")) {
        formData.append("logo", file);
      }
    });

    try {
      const res = await axios.post("/generate_form", formData, {
        onUploadProgress: (e) => {
          const percent = Math.round((e.loaded * 100) / (e.total || 1));
          setProgress(percent);
        }
      });

      setPdfUrl(res.data.pdf_url);
    } catch (err) {
      alert("Upload failed. Please check the console.");
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-12 p-6 border rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">🛠 Daily Log Drag & Drop</h2>

      <Dropzone onDrop={(accepted) => setFiles(accepted)}>
        {({ getRootProps, getInputProps }) => (
          <div
            {...getRootProps()}
            className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer bg-gray-50 hover:bg-gray-100"
          >
            <input {...getInputProps()} />
            <p className="text-gray-500">
              Drag & drop your photos, scope file, safety sheet, and logo here.
            </p>
            {files.length > 0 && (
              <ul className="mt-2 text-sm text-left">
                {files.map((f, i) => (
                  <li key={i}>📎 {f.name}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </Dropzone>

      <button
        onClick={handleUpload}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        disabled={uploading || files.length === 0}
      >
        {uploading ? `Uploading... ${progress}%` : "Submit Log"}
      </button>

      {pdfUrl && (
        <div className="mt-4">
          <p className="text-green-700 font-semibold">✅ PDF generated!</p>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline"
          >
            View PDF
          </a>
        </div>
      )}
    </div>
  );
}
