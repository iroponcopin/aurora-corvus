import { Fragment, type ReactNode } from "react";

/**
 * The wiki's prose markup, and nothing more: `<b>…</b>` (only when balanced) and `{@code x}`.
 * Anything else stays literal text — this never injects HTML.
 */
export function Rich({ text }: { text: string }): ReactNode {
  const opens = (text.match(/<b>/g) ?? []).length;
  const closes = (text.match(/<\/b>/g) ?? []).length;
  const bold = opens > 0 && opens === closes;
  const parts = text.split(/(<b>[\s\S]*?<\/b>|\{@code\s+[^{}]+?\})/g);
  return (
    <>
      {parts.map((p, i) => {
        if (bold && p.startsWith("<b>") && p.endsWith("</b>")) return <strong key={i}>{p.slice(3, -4)}</strong>;
        const m = /^\{@code\s+([^{}]+?)\}$/.exec(p);
        if (m) return <code key={i}>{m[1]}</code>;
        return <Fragment key={i}>{p}</Fragment>;
      })}
    </>
  );
}

/**
 * Trusted HTML that comes from the wiki's own bundles (e.g. the launcher guide's body_html, the
 * Discord steps' <code>): rendered as written, because it is the repository's copy, not input.
 */
export function TrustedHtml({ html, className, as: Tag = "div" }: { html: string; className?: string; as?: "div" | "p" | "span" }) {
  return <Tag className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
