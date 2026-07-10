import { useEffect, useState } from "react";
import { fetchWithAuth } from "../lib/fetchWithAuth";
import { useAuth } from "../context/AuthContext";

export default function FacilityHome() {
  const { signOut, getAccessToken } = useAuth();
  const [facility, setFacility] = useState(null);
  const [error, setError] = useState("");

    useEffect(() => {
    fetchWithAuth("/api/facility/me", {}, getAccessToken)
        .then(setFacility)
        .catch((err) => setError(err.message));
    }, [getAccessToken]);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-md mx-auto bg-white rounded-md shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <h1 className="text-lg font-bold text-gray-900">施設マイページ</h1>
          <button onClick={signOut} className="text-sm text-gray-500 hover:text-gray-700">
            ログアウト
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {facility && (
          <dl className="text-sm space-y-2">
            <div><dt className="text-gray-500">施設名</dt><dd className="font-medium">{facility.name}</dd></div>
            <div><dt className="text-gray-500">サービス種別</dt><dd className="font-medium">{facility.service_type}</dd></div>
            <div><dt className="text-gray-500">提出期限</dt><dd className="font-medium">{facility.submission_deadline ?? "-"}</dd></div>
          </dl>
        )}
      </div>
    </div>
  );
}