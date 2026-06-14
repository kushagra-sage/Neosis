/** Client-side export helpers (no dependencies). */

export function downloadBlob(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportJson(filename: string, data: unknown): void {
  downloadBlob(`${filename}.json`, JSON.stringify(data, null, 2), "application/json");
}

export function exportCsv(filename: string, rows: Record<string, unknown>[]): void {
  if (rows.length === 0) {
    downloadBlob(`${filename}.csv`, "", "text/csv");
    return;
  }
  const headers = Object.keys(rows[0]!);
  const escape = (v: unknown) => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [
    headers.join(","),
    ...rows.map((r) => headers.map((h) => escape(r[h])).join(",")),
  ];
  downloadBlob(`${filename}.csv`, lines.join("\n"), "text/csv");
}
