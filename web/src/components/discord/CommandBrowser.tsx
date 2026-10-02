"use client";

import { useMemo, useState } from "react";
import { CopyButton } from "../CopyButton";
import { Icon } from "../Icon";

export interface CommandGroup {
  name: string;
  gloss: string;
  subcommands: { name: string; admin: boolean; gloss: string; params: string[] }[];
}

/**
 * The bot's 21 subcommands in five groups, in the wiki's order. Each row copies "/group sub"
 * (without its arguments) with one click; the filter narrows the list as you type.
 */
export function CommandBrowser({
  groups,
  labels,
}: {
  groups: CommandGroup[];
  labels: { thCmd: string; thWhat: string; thWho: string; whoAll: string; whoAdmin: string; copy: string; copied: string; filter: string };
}) {
  const [q, setQ] = useState("");
  const query = q.trim().toLowerCase();
  const shown = useMemo(
    () =>
      groups
        .map((g) => ({
          ...g,
          subcommands: g.subcommands.filter(
            (s) => query === "" || `/${g.name} ${s.name} ${s.params.join(" ")} ${s.gloss} ${g.gloss}`.toLowerCase().includes(query),
          ),
        }))
        .filter((g) => g.subcommands.length > 0),
    [groups, query],
  );
  return (
    <div className="ac-cmds">
      <label className="ac-cmd-filter">
        <Icon name="terminal" size={16} />
        <input
          type="search"
          className="ac-input"
          placeholder={labels.filter}
          aria-label={labels.filter}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
      </label>
      <div className="ac-cmd-groups">
        {shown.map((g) => (
          <div key={g.name} className="ac-card ac-cmd-group">
            <h3 className="ac-ltr">
              <code>/{g.name}</code>
            </h3>
            <p className="ac-small">{g.gloss}</p>
            <table className="ac-cmd-table">
              <thead className="sr-only">
                <tr>
                  <th scope="col">{labels.thCmd}</th>
                  <th scope="col">{labels.thWhat}</th>
                  <th scope="col">{labels.thWho}</th>
                </tr>
              </thead>
              <tbody>
                {g.subcommands.map((s) => (
                  <tr key={s.name}>
                    <td className="ac-cmd-head">
                      <code className="ac-ltr">
                        /{g.name} {s.name}
                        {s.params.map((p) => (
                          <span key={p} className="ac-cmd-arg">
                            {" "}
                            &lt;{p}&gt;
                          </span>
                        ))}
                      </code>
                      <CopyButton text={`/${g.name} ${s.name}`} label={labels.copy} done={labels.copied} />
                    </td>
                    <td className="ac-cmd-what">{s.gloss}</td>
                    <td>
                      <span className={`ac-who ${s.admin ? "ac-who--admin" : ""}`}>{s.admin ? labels.whoAdmin : labels.whoAll}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}
