import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const STEP_EMAIL = "email";
const STEP_CODE = "code";

export default function Login() {
  const { requestOtp, verifyOtp } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [step, setStep] = useState(STEP_EMAIL);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const signedOut = searchParams.get("e") === "signedout";

  const handleRequestCode = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await requestOtp(email.trim());
      setStep(STEP_CODE);
    } catch {
      setError("メールの送信に失敗しました。メールアドレスをご確認ください。");
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await verifyOtp(email.trim(), code.trim());
      navigate("/");
    } catch {
      setError("認証コードが正しくありません。もう一度お試しください。");
    } finally {
      setSubmitting(false);
    }
  };

  const handleBackToEmail = () => {
    setStep(STEP_EMAIL);
    setCode("");
    setError("");
  };

  return (
    <div className="min-h-screen bg-gray-100 grid place-items-center px-4">
      <div className="w-full max-w-md bg-white rounded-md shadow p-8">
        <h1 className="text-xl font-bold text-gray-900 mb-2">施設ログイン</h1>

        {step === STEP_EMAIL && (
          <>
            <p className="text-sm text-gray-500 mb-6">
              登録済みのメールアドレスを入力してください。認証コードをお送りします。
            </p>
            {signedOut && (
              <p className="text-sm text-gray-500 mb-4">ログアウトしました。</p>
            )}
            <form onSubmit={handleRequestCode} className="space-y-4">
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@facility.co.jp"
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={submitting || !email}
                className="w-full bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {submitting ? "送信中…" : "認証コードを送信"}
              </button>
            </form>
          </>
        )}

        {step === STEP_CODE && (
          <>
            <p className="text-sm text-gray-500 mb-1">
              <span className="font-medium text-gray-700">{email}</span> 宛に認証コードを送信しました。
            </p>
            <p className="text-sm text-gray-500 mb-6">
              メールに記載された6桁のコードを入力してください。
            </p>
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                autoFocus
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                placeholder="123456"
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={submitting || code.length !== 6}
                className="w-full bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {submitting ? "確認中…" : "ログイン"}
              </button>
              <button
                type="button"
                onClick={handleBackToEmail}
                className="w-full text-sm text-gray-500 hover:text-gray-700"
              >
                メールアドレスを変更する
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}