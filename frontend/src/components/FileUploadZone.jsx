import { useRef, useState } from "react";

export default function FileUploadZone({ onUpload, uploading }) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleFiles = (fileList) => {
    const files = Array.from(fileList);
    if (files.length > 0) setSelectedFiles(files);
  };

  const handleRemove = (index, e) => {
    e.stopPropagation();
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadClick = async () => {
    if (selectedFiles.length === 0) return;
    await onUpload(selectedFiles);
    setSelectedFiles([]);
  };

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`border-2 border-dashed rounded px-3 py-2 cursor-pointer transition-colors ${
          dragActive ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {selectedFiles.length === 0 ? (
          <span className="block text-xs text-gray-500 text-center py-1">
            ファイルをドラッグ＆ドロップ、またはクリックして選択
          </span>
        ) : (
          <ul className="text-xs text-gray-600 space-y-1">
            {selectedFiles.map((f, i) => (
              <li key={i} className="flex items-center justify-between bg-gray-50 rounded px-2 py-1">
                <span className="truncate">{f.name}</span>
                <button
                  type="button"
                  onClick={(e) => handleRemove(i, e)}
                  className="text-gray-400 hover:text-red-500 ml-2"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <button
        type="button"
        onClick={handleUploadClick}
        disabled={selectedFiles.length === 0 || uploading}
        className="w-full bg-blue-600 text-white rounded px-3 py-1.5 text-xs font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {uploading ? "アップロード中…" : "アップロード"}
      </button>
    </div>
  );
}