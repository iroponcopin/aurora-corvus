/**
 * ACSK1 — the sealed skin format of scripts/skin_crypt.py, opened in the browser with WebCrypto
 * only, byte for byte the same computation:
 *
 *   master    = PBKDF2-HMAC-SHA256(PIN, salt, iterations, 64 bytes); encKey = master[0:32], macKey = [32:64]
 *   keystream = HMAC-SHA256(encKey, "ACSK" || u32be(block)), concatenated
 *   tag       = HMAC-SHA256(macKey, salt || u32be(len) || ciphertext)   (encrypt-then-MAC)
 *
 * A wrong PIN fails the tag before a single byte is decrypted. The PIN never leaves the page.
 */

export const MAGIC = "ACSK1";
const SALT_LEN = 16;
const TAG_LEN = 32;
const HEADER_LEN = MAGIC.length + SALT_LEN + 4 + 4 + TAG_LEN;
const LABEL = new TextEncoder().encode("ACSK");

export class WrongPin extends Error {
  constructor() {
    super("wrong PIN (the tag does not match)");
    this.name = "WrongPin";
  }
}

function subtle(): SubtleCrypto {
  const s = globalThis.crypto?.subtle;
  if (s === undefined) throw new Error("WebCrypto is not available (it needs a secure context)");
  return s;
}

function u32be(n: number): Uint8Array {
  return new Uint8Array([(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255]);
}

function concat(...parts: Uint8Array[]): Uint8Array<ArrayBuffer> {
  const out = new Uint8Array(new ArrayBuffer(parts.reduce((a, p) => a + p.length, 0)));
  let at = 0;
  for (const p of parts) {
    out.set(p, at);
    at += p.length;
  }
  return out;
}

function copy(a: Uint8Array): Uint8Array<ArrayBuffer> {
  const out = new Uint8Array(new ArrayBuffer(a.length));
  out.set(a);
  return out;
}

async function hmac(key: Uint8Array, data: Uint8Array): Promise<Uint8Array> {
  const k = await subtle().importKey("raw", copy(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await subtle().sign("HMAC", k, copy(data)));
}

export async function sha256Hex(data: Uint8Array): Promise<string> {
  const d = new Uint8Array(await subtle().digest("SHA-256", copy(data)));
  return Array.from(d, (b) => b.toString(16).padStart(2, "0")).join("");
}

function equal(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= (a[i] ?? 0) ^ (b[i] ?? 0);
  return diff === 0;
}

export async function openSealed(blob: Uint8Array, pin: string): Promise<Uint8Array> {
  if (blob.length < HEADER_LEN || new TextDecoder().decode(blob.subarray(0, MAGIC.length)) !== MAGIC) {
    throw new Error("not an ACSK1 file");
  }
  const dv = new DataView(blob.buffer, blob.byteOffset, blob.byteLength);
  let at = MAGIC.length;
  const salt = blob.subarray(at, at + SALT_LEN);
  at += SALT_LEN;
  const iterations = dv.getUint32(at);
  at += 4;
  const length = dv.getUint32(at);
  at += 4;
  const tag = blob.subarray(at, at + TAG_LEN);
  at += TAG_LEN;
  const ciphertext = blob.subarray(at);
  if (ciphertext.length !== length) throw new Error("length field disagrees with the ciphertext");

  const base = await subtle().importKey("raw", new TextEncoder().encode(pin), "PBKDF2", false, ["deriveBits"]);
  const master = new Uint8Array(
    await subtle().deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: copy(salt), iterations }, base, 512),
  );
  const encKey = master.subarray(0, 32);
  const macKey = master.subarray(32, 64);
  const want = await hmac(macKey, concat(salt, u32be(length), ciphertext));
  if (!equal(want, tag)) throw new WrongPin();

  const out = new Uint8Array(length);
  for (let block = 0, i = 0; i < length; block++) {
    const ks = await hmac(encKey, concat(LABEL, u32be(block)));
    for (let j = 0; j < ks.length && i < length; j++, i++) out[i] = (ciphertext[i] ?? 0) ^ (ks[j] ?? 0);
  }
  return out;
}
