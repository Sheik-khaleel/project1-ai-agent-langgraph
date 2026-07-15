import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080",
  timeout: 15000,
});

export async function sendQuery(message, limit) {
  const response = await client.post("/query", {
    message: `${message.trim()} ${Number.isFinite(limit) ? limit : ""}`.trim(),
  });
  return response.data;
}
