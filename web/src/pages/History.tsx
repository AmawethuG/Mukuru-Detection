import { useEffect, useState } from "react";
import { getMe, AccountResponse } from "../api/auth";
import { getTransactionHistory, TransactionHistoryItem } from "../api/transactions";
import { useStore } from "../store/useStore";
import { t } from "../i18n";

export default function History() {
  const lang = useStore((s) => s.language);
  const isDuress = useStore((s) => s.isDuress);

  const [account, setAccount] = useState<AccountResponse | null>(null);
  const [transactions, setTransactions] = useState<TransactionHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load(): Promise<void> {
      try {
        const [acct, history] = await Promise.all([
          getMe(),
          getTransactionHistory({}),
        ]);
        setAccount(acct);
        setTransactions(history.transactions);
      } catch {
        setError(t("common.error", lang));
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
    return (
      <div className="flex justify-center mt-16">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return <p className="text-red-600 text-center mt-8">{error}</p>;
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">{t("history.title", lang)}</h1>

      {account && (
        <div className="bg-white rounded-xl shadow p-4 mb-6">
          <p className="text-sm text-gray-500">{t("history.balance", lang)}</p>
          <p className="text-3xl font-bold text-gray-800">
            {account.balance} {account.currency}
          </p>
        </div>
      )}

      {transactions.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          {t("history.no_transactions", lang)}
        </p>
      ) : (
        <div className="space-y-3">
          {transactions.map((txn) => (
            <div
              key={txn.id}
              className="bg-white rounded-xl shadow p-4 flex items-center gap-4"
            >
              <span className="text-2xl" aria-hidden="true">
                {txn.direction === "sent" ? "↑" : "↓"}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-800 truncate">
                  {txn.direction === "sent"
                    ? `${t("history.transaction.to", lang)} ${txn.recipient}`
                    : `${t("history.transaction.from", lang)} ${txn.recipient}`}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(txn.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="text-right">
                <p
                  className={`font-semibold ${
                    txn.direction === "sent" ? "text-red-600" : "text-green-600"
                  }`}
                >
                  {txn.direction === "sent" ? "−" : "+"}{txn.amount} {txn.currency}
                </p>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                  {txn.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {isDuress && (
        <p className="mt-6 text-center text-xs text-gray-400">
          Decoy account – demo mode active
        </p>
      )}
    </div>
  );
}
