import React from "react";
import "./DiffViewer.css";

function DiffViewer({ file }) {
  return (
    <div className="file-diff">
      <div className="file-header">
        <span>--- {file.oldFile}</span>
        <br />
        <span>+++ {file.newFile}</span>
      </div>
      {file.chunks.map((chunk, index) => (
        <div key={index} className="chunk">
          <div className="chunk-header">{chunk.header}</div>
          <div className="lines">
            {chunk.deletions.map((line, idx) => (
              <div key={`del-${idx}`} className="line deletion">
                {line}
              </div>
            ))}
            {chunk.additions.map((line, idx) => (
              <div key={`add-${idx}`} className="line addition">
                {line}
              </div>
            ))}
            {chunk.unchanged.map((line, idx) => (
              <div key={`unchanged-${idx}`} className="line unchanged">
                {line}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default DiffViewer;
