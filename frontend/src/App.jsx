import React, { useEffect, useMemo, useState } from "react";

const defaultMonth = () => new Date().toISOString().slice(0, 7);

const fetchJson = async (url, options) => {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error("Request failed");
  }
  return response.json();
};

export default function App() {
  const [month, setMonth] = useState(defaultMonth);
  const [summary, setSummary] = useState({ totals: {}, categories: [] });
  const [categories, setCategories] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [bills, setBills] = useState([]);
  const [imports, setImports] = useState([]);
  const [error, setError] = useState("");

  const apiBase = useMemo(() => "/api", []);

  const loadAll = async () => {
    try {
      const [summaryData, categoryData, transferData, expenseData, billData, importData] =
        await Promise.all([
          fetchJson(`${apiBase}/summary/${month}/`),
          fetchJson(`${apiBase}/categories/`),
          fetchJson(`${apiBase}/transfers/?month=${month}`),
          fetchJson(`${apiBase}/expenses/?month=${month}`),
          fetchJson(`${apiBase}/bills/?month=${month}`),
          fetchJson(`${apiBase}/imports/`),
        ]);
      setSummary(summaryData);
      setCategories(categoryData.items);
      setTransfers(transferData.items);
      setExpenses(expenseData.items);
      setBills(billData.items);
      setImports(importData.items);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load data");
    }
  };

  useEffect(() => {
    loadAll();
  }, [month]);

  const submitForm = async (event, endpoint, onDone) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    try {
      await fetchJson(`${apiBase}/${endpoint}/`, {
        method: "POST",
        body: formData,
      });
      event.target.reset();
      onDone?.();
      await loadAll();
    } catch (err) {
      setError(err.message || "Unable to save data");
    }
  };

  const queueImport = async (importId) => {
    try {
      await fetchJson(`${apiBase}/imports/${importId}/queue/`, { method: "POST" });
      await loadAll();
    } catch (err) {
      setError(err.message || "Unable to queue import");
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div>
          <h1>Monthly Expense Tracker</h1>
          <p>
            Track transfers to Wise, categorize expenses, and store bill imports
            for Auchan or Lidl Plus.
          </p>
        </div>
        <div className="month-picker">
          <label htmlFor="month">Month</label>
          <input
            id="month"
            type="month"
            value={month}
            onChange={(event) => setMonth(event.target.value)}
          />
        </div>
      </header>

      {error ? <div className="error">{error}</div> : null}

      <section className="summary">
        <div className="card">
          <h2>Totals</h2>
          <ul>
            <li>
              <span>Transfers</span>
              <strong>€{summary.totals?.transfers || "0.00"}</strong>
            </li>
            <li>
              <span>Expenses</span>
              <strong>€{summary.totals?.expenses || "0.00"}</strong>
            </li>
            <li>
              <span>Bills</span>
              <strong>€{summary.totals?.bills || "0.00"}</strong>
            </li>
          </ul>
        </div>
        <div className="card">
          <h2>Category Breakdown</h2>
          <ul>
            {summary.categories?.length ? (
              summary.categories.map((item) => (
                <li key={item.name}>
                  <span>{item.name}</span>
                  <strong>€{item.total}</strong>
                </li>
              ))
            ) : (
              <li>No category totals yet.</li>
            )}
          </ul>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Add Transfer</h2>
          <form onSubmit={(event) => submitForm(event, "transfers")}>
            <input type="month" name="month" defaultValue={month} required />
            <input type="number" step="0.01" name="amount" placeholder="Amount" required />
            <input type="text" name="note" placeholder="Main bank → Wise" />
            <button type="submit">Save transfer</button>
          </form>
          <ul className="list">
            {transfers.map((item) => (
              <li key={item.id}>
                <strong>€{item.amount}</strong>
                <span>{item.note || "Transfer"}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2>Add Expense</h2>
          <form onSubmit={(event) => submitForm(event, "expenses")}>
            <input type="month" name="month" defaultValue={month} required />
            <select name="category_id" required>
              <option value="">Select category</option>
              {categories.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <input type="number" step="0.01" name="amount" placeholder="Amount" required />
            <input type="text" name="description" placeholder="Lunch, groceries" />
            <button type="submit">Save expense</button>
          </form>
          <ul className="list">
            {expenses.map((item) => (
              <li key={item.id}>
                <strong>€{item.amount}</strong>
                <span>
                  {item["category__name"]}
                  {item.description ? ` · ${item.description}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2>Add Bill</h2>
          <form onSubmit={(event) => submitForm(event, "bills")}>
            <input type="month" name="month" defaultValue={month} required />
            <select name="bill_type">
              <option value="paper">Paper bill</option>
              <option value="app">App download</option>
            </select>
            <input type="text" name="source" placeholder="Auchan, Lidl Plus" />
            <input type="number" step="0.01" name="amount" placeholder="Amount" required />
            <select name="status">
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
              <option value="reimbursed">Reimbursed</option>
            </select>
            <button type="submit">Save bill</button>
          </form>
          <ul className="list">
            {bills.map((item) => (
              <li key={item.id}>
                <strong>€{item.amount}</strong>
                <span>
                  {item.bill_type} · {item.source || "Unknown"} · {item.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Categories</h2>
          <form onSubmit={(event) => submitForm(event, "categories")}>
            <input type="text" name="name" placeholder="Food, Transport" required />
            <button type="submit">Add category</button>
          </form>
          <div className="chips">
            {categories.map((item) => (
              <span key={item.id}>{item.name}</span>
            ))}
          </div>
        </div>

        <div className="card">
          <h2>Headless Import Queue</h2>
          <p>
            Save provider profiles for Auchan or Lidl Plus and hand them to a
            headless browser worker.
          </p>
          <form onSubmit={(event) => submitForm(event, "imports")}>
            <input type="text" name="provider" placeholder="Provider" required />
            <input type="text" name="account_hint" placeholder="Email or phone" />
            <button type="submit">Save import</button>
          </form>
          <ul className="list">
            {imports.map((item) => (
              <li key={item.id}>
                <strong>{item.provider}</strong>
                <span>
                  {item.account_hint || "No account hint"} · {item.status}
                </span>
                <button type="button" onClick={() => queueImport(item.id)}>
                  Queue import
                </button>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
