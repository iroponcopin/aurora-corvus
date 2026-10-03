import { CopyButton } from "./CopyButton";
import type { FileFacts } from "@/lib/wiki-types";

export interface FileCardLabels {
  fileSize: string;
  sha256: string;
  copy: string;
  copied: string;
}

/**
 * One downloadable file, as the wiki has always described it: name, size (MB/KB to one decimal,
 * then the exact byte count), SHA-256 with a copy button, and the download itself.
 */
export function FileCard({
  tag,
  file,
  note,
  cta,
  labels,
}: {
  tag: string;
  file: FileFacts;
  note?: string;
  cta: string;
  labels: FileCardLabels;
}) {
  return (
    <div className="ac-file ac-card">
      <span className="ac-tag">{tag}</span>
      <h3 className="ac-ltr">{file.name}</h3>
      {note ? <p className="ac-small">{note}</p> : null}
      <dl className="ac-facts">
        <div>
          <dt>{labels.fileSize}</dt>
          <dd className="ac-ltr">
            {file.sizeDisplay} ({file.bytesDisplay} bytes)
          </dd>
        </div>
        <div>
          <dt>{labels.sha256}</dt>
          <dd>
            <code className="ac-hash">{file.sha256}</code>
            <CopyButton text={file.sha256} label={labels.copy} done={labels.copied} />
          </dd>
        </div>
      </dl>
      <a className="ac-btn ac-file-dl" href={file.url} download>
        {cta}
      </a>
    </div>
  );
}
