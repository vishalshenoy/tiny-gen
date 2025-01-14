import React, { useState } from "react";
import DiffViewer from "./DiffViewer";
import "./App.css";
import { Button, Input } from "@mantine/core";
import "@mantine/core/styles.css";

async function fetchDiffFromAPI(repoUrl, prompt) {
  const response = await fetch("link_to_modal_deployment", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ repoUrl, prompt }),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch diff from API");
  }
  const data = await response.json();
  return data.diff.replace(/```diff|```/g, "").trim();
}

function parseDiff(diffString) {
  const files = [];
  const lines = diffString.split("\n");

  let currentFile = null;
  let currentChunk = null;

  lines.forEach((line) => {
    if (line.startsWith("---")) {
      if (currentFile) files.push(currentFile);
      currentFile = { oldFile: line.slice(4), newFile: "", chunks: [] };
      currentChunk = null;
    } else if (line.startsWith("+++")) {
      if (currentFile) currentFile.newFile = line.slice(4);
    } else if (line.startsWith("@@")) {
      currentChunk = {
        header: line,
        additions: [],
        deletions: [],
        unchanged: [],
      };
      currentFile.chunks.push(currentChunk);
    } else if (line.startsWith("+")) {
      if (currentChunk) {
        currentChunk.additions.push(line);
      }
    } else if (line.startsWith("-")) {
      if (currentChunk) {
        currentChunk.deletions.push(line);
      }
    } else if (line.trim() !== "") {
      if (currentChunk) {
        currentChunk.unchanged.push(line);
      }
    }
  });

  if (currentFile) files.push(currentFile);
  return files;
}

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [prompt, setPrompt] = useState("");
  const [parsedDiff, setParsedDiff] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerateDiff = async () => {
    setLoading(true);
    setError(null);
    try {
      const rawDiff = await fetchDiffFromAPI(repoUrl, prompt);
      const structuredDiff = parseDiff(rawDiff);
      setParsedDiff(structuredDiff);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <br></br>
      <h1>Tinygen Diff Viewer</h1>
      <br></br>
      <div style={{ display: "flex", justifyContent: "center", gap: "10px" }}>
        <Input
          type="text"
          placeholder="Repository URL"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          radius="xl"
        />
        <Input
          type="text"
          placeholder="Prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          radius="xl"
        />
      </div>
      <br />
      <Button
        onClick={handleGenerateDiff}
        disabled={loading || !repoUrl || !prompt}
        size="md"
        style={{ width: "200px" }}
        color="violet"
        radius="xl"
      >
        {loading ? "Loading..." : "Generate"}
      </Button>
      {error && <p className="error">Error: {error}</p>}
      {parsedDiff.length > 0 &&
        parsedDiff.map((file, index) => <DiffViewer key={index} file={file} />)}
    </div>
  );
}

export default App;
