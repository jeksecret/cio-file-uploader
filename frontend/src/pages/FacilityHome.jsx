import { useEffect, useState } from "react";
import { fetchWithAuth } from "../lib/fetchWithAuth";
import { useAuth } from "../context/AuthContext";

function StatusBadge({ status }) {
  const isSubmitted = status === "submitted";
  return (
    <span
      className={`text-xs font-medium px-2 py-1 rounded ${
        isSubmitted ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
      }`}
    >
      {isSubmitted ? "提出済み" : "未提出"}
    </span>
  );
}

export default function FacilityHome() {
  const { signOut, getAccessToken } = useAuth();
  const [facility, setFacility] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchWithAuth("/api/facility/me", {}, getAccessToken)
      .then(setFacility)
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 grid place-items-center px-4">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!facility) {
    return (
      <div className="min-h-screen bg-gray-100 grid place-items-center text-gray-500">
        読み込み中…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-blue-500 shadow px-4 py-3 flex justify-end">
        <button onClick={signOut} className="text-xs border border-white bg-transparent text-white font-light px-3 py-2 rounded-sm hover:bg-white hover:text-blue-600">
          ログアウト
        </button>
      </div>

      <div className="max-w-2xl mx-auto p-6 space-y-6">
        <div className="bg-white rounded-md shadow p-6">
          <h1 className="text-lg font-bold text-gray-900 mb-4">{facility.name}</h1>
          <dl className="text-sm space-y-2">
            <div className="flex justify-between">
              <dt className="text-gray-500">サービス種別</dt>
              <dd className="font-medium text-gray-900">{facility.service_type}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">提出期限</dt>
              <dd className="font-medium text-gray-900">
                {facility.submission_deadline ?? "-"}
              </dd>
            </div>
          </dl>
        </div>

        <div className="bg-white rounded-md shadow p-6">
          <h2 className="text-sm font-bold text-gray-900 mb-4">必要書類</h2>
          <ul className="divide-y divide-gray-100">
            {facility.documents.map((doc) => (
              <li key={doc.required_doc_id} className="py-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{doc.document_name}</p>
                  {doc.submitted_at && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      提出日時: {new Date(doc.submitted_at).toLocaleString("ja-JP")}
                    </p>
                  )}
                </div>
                <StatusBadge status={doc.status} />
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-md shadow p-6">
          <h2 className="text-sm font-bold text-gray-900 mb-4">その他ファイル</h2>
          {facility.other_files.length === 0 ? (
            <p className="text-sm text-gray-400">アップロード済みのファイルはありません。</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {facility.other_files.map((f) => (
                <li key={f.id} className="py-2 text-sm text-gray-700">
                  {f.original_filename}
                  <span className="text-xs text-gray-400 ml-2">
                    {new Date(f.submitted_at).toLocaleString("ja-JP")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}