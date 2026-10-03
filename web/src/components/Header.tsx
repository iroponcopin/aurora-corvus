"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { getLenis } from "./SmoothScroll";
import { Icon } from "./Icon";
import { SoundToggle } from "./SoundToggle";
import { asset, BASE_PATH, LANGUAGES, pathOf } from "@/lib/site";
import { sectionKey, splitPath } from "@/lib/paths";
import type { Lang } from "@/lib/wiki-types";

export interface HeaderLabels {
  siteTitle: string;
  home: string;
  launcher: string;
  brands: string;
  recipes: string;
  changelog: string;
  upcoming: string;
  skin: string;
  discord: string;
  download: string;
  menu: string;
  close: string;
  language: string;
  primary: string;
  sound: string;
  soundOn: string;
  soundOff: string;
}

const LANG_KEY = "aurora-corvus-lang";
const BRAND_SECTIONS = new Set(["ouka", "cherry", "aureum", "cherry-controls", "alpha"]);

function rememberLang(code: string): void {
  try {
    localStorage.setItem(LANG_KEY, code);
  } catch {
    /* storage can be unavailable (private mode); the choice simply isn't remembered */
  }
}

/** Close a popover on Escape or on a pointerdown outside it. */
function useDismiss(open: boolean, close: () => void, refs: React.RefObject<HTMLElement | null>[]): void {
  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent): void => {
      const t = e.target as Node;
      if (refs.some((r) => r.current?.contains(t))) return;
      close();
    };
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, close, refs]);
}

export function Header({ lang, labels }: { lang: Lang; labels: HeaderLabels }) {
  const pathname = usePathname();
  const { section } = splitPath(pathname);
  const key = sectionKey(section);
  const [brandsOpen, setBrandsOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const [sheet, setSheet] = useState(false);
  const [suffix, setSuffix] = useState("");
  const [compact, setCompact] = useState(false);
  const brandsBtn = useRef<HTMLButtonElement>(null);
  const brandsPop = useRef<HTMLDivElement>(null);
  const langBtn = useRef<HTMLButtonElement>(null);
  const langPop = useRef<HTMLDivElement>(null);
  const brandsId = useId();
  const langId = useId();
  const sheetId = useId();

  const closeBrands = useCallback(() => setBrandsOpen(false), []);
  const closeLang = useCallback(() => {
    setLangOpen(false);
    langBtn.current?.focus();
  }, []);
  useDismiss(brandsOpen, closeBrands, [brandsBtn, brandsPop]);
  useDismiss(langOpen, closeLang, [langBtn, langPop]);

  // The language links carry the query and hash of the page (so ?brand= survives a switch).
  useEffect(() => {
    setSuffix(window.location.search + window.location.hash);
    setBrandsOpen(false);
    setSheet(false);
  }, [pathname]);

  useEffect(() => {
    const onScroll = (): void => setCompact(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // The mobile sheet locks the page underneath it.
  useEffect(() => {
    if (!sheet) return;
    const root = document.documentElement;
    const prev = root.style.overflow;
    root.style.overflow = "hidden";
    getLenis()?.stop();
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") setSheet(false);
    };
    document.addEventListener("keydown", onKey);
    return () => {
      root.style.overflow = prev;
      getLenis()?.start();
      document.removeEventListener("keydown", onKey);
    };
  }, [sheet]);

  // Footer links (and any other a[data-lang]) remember the choice too.
  useEffect(() => {
    const onClick = (e: MouseEvent): void => {
      const a = (e.target as Element | null)?.closest?.("a[data-lang]");
      const code = a?.getAttribute("data-lang");
      if (code) rememberLang(code);
    };
    document.addEventListener("click", onClick);
    document.addEventListener("auxclick", onClick);
    return () => {
      document.removeEventListener("click", onClick);
      document.removeEventListener("auxclick", onClick);
    };
  }, []);

  // Focus management inside the language list.
  useEffect(() => {
    if (!langOpen) return;
    const items = Array.from(langPop.current?.querySelectorAll<HTMLAnchorElement>("a") ?? []);
    const current = items.find((a) => a.getAttribute("aria-current") === "true") ?? items[0];
    current?.focus();
    const onKey = (e: KeyboardEvent): void => {
      const i = items.indexOf(document.activeElement as HTMLAnchorElement);
      let next = -1;
      if (e.key === "ArrowDown") next = (i + 1) % items.length;
      else if (e.key === "ArrowUp") next = (i - 1 + items.length) % items.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = items.length - 1;
      if (next >= 0) {
        e.preventDefault();
        items[next]?.focus();
      }
    };
    const pop = langPop.current;
    pop?.addEventListener("keydown", onKey);
    return () => pop?.removeEventListener("keydown", onKey);
  }, [langOpen]);

  const links: { key: string; label: string; href: string }[] = [
    { key: "recipes", label: labels.recipes, href: pathOf(lang, "recipes/") },
    { key: "changelog", label: labels.changelog, href: pathOf(lang, "changelog/") },
    { key: "upcoming", label: labels.upcoming, href: pathOf(lang, "upcoming/") },
    { key: "skin", label: labels.skin, href: pathOf(lang, "skin/") },
    { key: "discord", label: labels.discord, href: pathOf(lang, "discord/") },
  ];
  const brands = [
    { key: "ouka", label: "OUKA", href: pathOf(lang, "ouka/") },
    { key: "cherry", label: "Cherry", href: pathOf(lang, "cherry/") },
    { key: "aureum", label: "Aureum", href: pathOf(lang, "aureum/") },
  ];
  const brandsCurrent = BRAND_SECTIONS.has(key);
  const current = (k: string): "page" | undefined => (k === key ? "page" : undefined);

  return (
    <header className="ac-header" data-compact={compact ? "true" : "false"}>
      <div className="ac-header-pill ac-glass">
        <Link href={pathOf(lang, "")} className="ac-brand" aria-label={`${labels.siteTitle} · ${labels.home}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={asset("logo.png")} alt="" width={22} height={22} />
          <span>{labels.siteTitle}</span>
        </Link>

        <nav className="ac-nav" aria-label={labels.primary}>
          <Link href={pathOf(lang, "launcher/")} className="ac-nav-link" aria-current={current("launcher")}>
            {labels.launcher}
          </Link>
          <div className="ac-nav-brands">
            <button
              ref={brandsBtn}
              type="button"
              className="ac-nav-link"
              aria-expanded={brandsOpen}
              aria-haspopup="true"
              aria-controls={brandsId}
              aria-current={brandsCurrent ? "page" : undefined}
              onClick={() => setBrandsOpen((v) => !v)}
            >
              {labels.brands}
              <Icon name="chevronDown" size={13} className="ac-chev" data-open={brandsOpen} />
            </button>
            <div ref={brandsPop} id={brandsId} className="ac-pop ac-glass" hidden={!brandsOpen}>
              {brands.map((b) => (
                <Link
                  key={b.key}
                  href={b.href}
                  className="ac-pop-item"
                  aria-current={b.key === key ? "page" : undefined}
                  onClick={closeBrands}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={asset(`icons/${b.key}.png`)} alt="" width={28} height={28} />
                  <span>{b.label}</span>
                </Link>
              ))}
            </div>
          </div>
          {links.map((l) => (
            <Link key={l.key} href={l.href} className="ac-nav-link" aria-current={current(l.key)}>
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="ac-header-end">
          <SoundToggle label={labels.sound} on={labels.soundOn} off={labels.soundOff} />
          <div className="ac-lang">
            <button
              ref={langBtn}
              type="button"
              className="ac-iconbtn"
              aria-label={labels.language}
              title={labels.language}
              aria-haspopup="true"
              aria-expanded={langOpen}
              aria-controls={langId}
              onClick={() => (langOpen ? closeLang() : setLangOpen(true))}
            >
              <Icon name="globe" size={17} />
            </button>
            <div ref={langPop} id={langId} className="ac-pop ac-pop--lang ac-glass" hidden={!langOpen}>
              <ul>
                {LANGUAGES.map((l) => (
                  <li key={l.code}>
                    <a
                      href={`${BASE_PATH}${pathOf(l.code, section)}${suffix}`}
                      lang={l.code}
                      hrefLang={l.code}
                      data-lang={l.code}
                      dir={l.dir === "rtl" ? "rtl" : undefined}
                      aria-current={l.code === lang ? "true" : undefined}
                      className="ac-pop-item"
                    >
                      <span>{l.name}</span>
                      {l.code === lang ? <small aria-hidden="true">✓</small> : null}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <Link
            href={pathOf(lang, "download/")}
            className="ac-btn ac-btn--small ac-cta"
            aria-current={current("download")}
          >
            {labels.download}
          </Link>
          <button
            type="button"
            className="ac-iconbtn ac-menu-btn"
            aria-label={sheet ? labels.close : labels.menu}
            aria-expanded={sheet}
            aria-controls={sheetId}
            onClick={() => setSheet((v) => !v)}
          >
            <Icon name={sheet ? "x" : "menu"} size={18} />
          </button>
        </div>
      </div>

      {sheet ? (
        <div id={sheetId} className="ac-sheet" style={{ pointerEvents: "auto" }}>
          <nav aria-label={labels.primary} className="ac-sheet-nav">
            <Link href={pathOf(lang, "launcher/")} onClick={() => setSheet(false)} aria-current={current("launcher")}>
              {labels.launcher}
            </Link>
            <p className="ac-eyebrow">{labels.brands}</p>
            {brands.map((b) => (
              <Link key={b.key} href={b.href} onClick={() => setSheet(false)} aria-current={current(b.key)}>
                {b.label}
              </Link>
            ))}
            <p className="ac-eyebrow" aria-hidden="true">
              {" "}
            </p>
            {links.map((l) => (
              <Link key={l.key} href={l.href} onClick={() => setSheet(false)} aria-current={current(l.key)}>
                {l.label}
              </Link>
            ))}
            <Link
              href={pathOf(lang, "download/")}
              className="ac-btn ac-sheet-cta"
              onClick={() => setSheet(false)}
              aria-current={current("download")}
            >
              {labels.download}
            </Link>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
