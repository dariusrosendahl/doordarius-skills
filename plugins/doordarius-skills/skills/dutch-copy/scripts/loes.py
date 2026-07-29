#!/usr/bin/env python3
"""loes - Dutch copy via HostYourAI's Loes models (OpenAI-compatible router).

Modes:
  check    proofread NL text: spelling, grammar, punctuation, clumsy phrasing.
           Meaning must not change. Prints a word-level diff to stderr.
  rewrite  rewrite NL text in a given tone.
  gen      generate NL copy from a brief.
  ask      raw one-shot prompt, no editorial system prompt.

Input comes from a positional argument, --file, or stdin.
The result goes to stdout; the diff, warnings and token usage go to stderr, so
`loes check < in.md > out.md` yields clean text while an agent reading the
combined output still sees exactly what changed.

Requires: python3 (stdlib only) + curl, and an API key in one of
LOES_PERSONAL_KEY / LOES_API_KEY / HOSTYOURAI_API_KEY.

Exit codes: 0 ok, 1 usage/input error, 2 API error, 3 output tripped a guard.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

BASE_URL = os.environ.get("LOES_BASE_URL", "https://hostyourai.com/api/v1")
DEFAULT_MODEL = os.environ.get("LOES_MODEL", "hyai/loes-large")
KEY_VARS = ("LOES_PERSONAL_KEY", "LOES_API_KEY", "HOSTYOURAI_API_KEY")

# Loes models advertise cold_start_seconds up to 120, so allow a long first read.
TIMEOUT = int(os.environ.get("LOES_TIMEOUT", "180"))

STYLE_RULES = (
    "Schrijf Nederlands van moedertaalniveau. "
    "Geen Engelse leenwoorden waar een gangbaar Nederlands woord bestaat. "
    "Geen gestapelde uitroeptekens en geen marketing-superlatieven zonder onderbouwing."
)

NO_DASH_RULE = (
    " Gebruik NOOIT gedachtestreepjes (em-dash of en-dash); "
    "gebruik in plaats daarvan een komma, een dubbele punt of een nieuwe zin."
)

PROMPTS = {
    "check": (
        "Je bent een Nederlandse eindredacteur. Corrigeer spelling, grammatica, "
        "interpunctie en kromme formuleringen.\n"
        "HARDE REGEL: de betekenis, de feiten en het onderwerp van elke zin blijven "
        "exact gelijk. Verander nooit wie iets doet (wij/u/je), nooit een getal, "
        "prijs, termijn, datum of productnaam. Voeg niets toe en laat niets weg.\n"
        "Behoud de bestaande toon en aanspreekvorm (u of je) zoals in de brontekst.\n"
        "Behoud markdown, HTML-tags, URL's en placeholders letterlijk.\n"
        "{style}\n"
        "Antwoord met UITSLUITEND de gecorrigeerde tekst, zonder inleiding, zonder "
        "uitleg, zonder codeblok."
    ),
    "rewrite": (
        "Je bent een Nederlandse copywriter. Herschrijf de tekst van de gebruiker.\n"
        "Behoud alle feiten, getallen, prijzen en productnamen exact.\n"
        "Behoud markdown, HTML-tags, URL's en placeholders letterlijk.\n"
        "{style}\n"
        "Antwoord met UITSLUITEND de herschreven tekst, zonder inleiding of uitleg."
    ),
    "gen": (
        "Je bent een Nederlandse copywriter. Schrijf nieuwe tekst op basis van de "
        "briefing van de gebruiker.\n"
        "Verzin geen feiten, prijzen, termijnen of productclaims die niet in de "
        "briefing staan. Laat onbekende specifieke gegevens weg in plaats van ze te "
        "bedenken.\n"
        "{style}\n"
        "Antwoord met UITSLUITEND de tekst zelf."
    ),
    "ask": None,
}

TONES = {
    "shop": "Toon: webshop, helder en behulpzaam, gericht op een consument die iets wil kopen. Kort, actief, geen jargon.",
    "zakelijk": "Toon: zakelijk en professioneel, aanspreekvorm u, niet stijf.",
    "informeel": "Toon: informeel en vriendelijk, aanspreekvorm je.",
    "beknopt": "Toon: zo beknopt mogelijk. Schrap elk woord dat niets toevoegt.",
    "seo": "Toon: informatief en scanbaar voor lezers en zoekmachines. Korte alinea's, natuurlijk gebruik van het hoofdonderwerp, geen keyword stuffing.",
    "mail": "Toon: e-mail aan collega's. Zakelijk maar menselijk, direct to the point, geen plichtmatige openingszin.",
}

DASHES = re.compile(r"[—–]")
PREAMBLE = re.compile(
    r"^\s*(hier\s+is|hierbij|dit\s+is)\b[^\n:]{0,80}:\s*\n+", re.IGNORECASE
)


def die(msg: str, code: int = 1) -> "None":
    print(f"loes: {msg}", file=sys.stderr)
    raise SystemExit(code)


def api_key() -> str:
    for var in KEY_VARS:
        val = os.environ.get(var, "").strip()
        if val:
            return val
    die(
        "no API key. Get one at https://hostyourai.com/app/register and export it as "
        "LOES_PERSONAL_KEY (or LOES_API_KEY).",
    )
    raise AssertionError  # unreachable


def request(path: str, body: "bytes | None" = None) -> dict:
    """POST/GET the router via curl.

    curl rather than urllib on purpose: it uses the OS trust store, so this works
    on stock macOS python3, which ships without a usable CA bundle.
    The key goes into a 0600 config file, never into argv where `ps` could read it.
    """
    if not shutil.which("curl"):
        die("curl not found on PATH; it is required.", 2)

    key = api_key()
    last = ""
    for attempt in (1, 2):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = os.path.join(td, "curlrc")
            lines = [
                f'url = "{BASE_URL}{path}"',
                f'header = "Authorization: Bearer {key}"',
            ]
            if body is not None:
                body_path = os.path.join(td, "body.json")
                with open(body_path, "wb") as fh:
                    fh.write(body)
                lines += [
                    'header = "Content-Type: application/json"',
                    f"data = @{body_path}",
                ]
            with open(cfg_path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            os.chmod(cfg_path, 0o600)

            proc = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "--max-time",
                    str(TIMEOUT),
                    "-w",
                    "\n%{http_code}",
                    "--config",
                    cfg_path,
                ],
                capture_output=True,
                text=True,
            )

        if proc.returncode != 0:
            last = f"curl exit {proc.returncode}: {proc.stderr.strip()[:300]}"
        else:
            raw, _, status = proc.stdout.rpartition("\n")
            status = status.strip()
            if status.startswith("2"):
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    last = f"non-JSON response: {raw[:300]}"
            else:
                last = f"HTTP {status}: {raw.strip()[:400]}"
                # 4xx is our fault, and the router answers 503 + code "on_request"
                # for models that are catalogued but not live. Neither is transient.
                if status[:1] == "4" or '"on_request"' in raw:
                    break

        if attempt == 1:
            print(
                f"loes: {last} - retrying once (the model may be cold-starting)",
                file=sys.stderr,
            )
            time.sleep(5)

    die(last or "request failed", 2)
    raise AssertionError


def word_diff(before: str, after: str) -> "list[str]":
    a, b = before.split(), after.split()
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        old, new = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if tag == "replace":
            out.append(f"  ~ {old}  ->  {new}")
        elif tag == "delete":
            out.append(f"  - {old}")
        else:
            out.append(f"  + {new}")
    return out


def list_models() -> int:
    for m in request("/models")["data"]:
        if "loes" not in m["id"]:
            continue
        pr = m.get("pricing") or {}
        flag = "ok " if m.get("available") else "OFF"
        default = " (default)" if m.get("default") else ""
        print(
            f"{flag} {m['id']:44} {m.get('display_name', ''):34} "
            f"in={pr.get('input_per_million')} out={pr.get('output_per_million')} EUR/1M "
            f"ctx={m.get('served_context_length')}{default}"
        )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        prog="loes",
        description="Dutch copy via HostYourAI Loes (check / rewrite / gen / ask).",
        epilog=(
            "examples:\n"
            "  loes check < copy.md > fixed.md\n"
            '  loes rewrite --tone shop "onze lampen zijn heel erg mooi"\n'
            '  loes gen --tone seo "intro van 80 woorden voor een categoriepagina kerstverlichting"\n'
            "  loes check --file src/copy/pdp.nl.md --model hyai/loes-qwen3-14b\n"
            "  loes --models"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("mode", nargs="?", choices=sorted(PROMPTS), help="what to do")
    p.add_argument("text", nargs="*", help="text or brief; omit to read stdin")
    p.add_argument("-f", "--file", help="read input from this file instead of stdin")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"default {DEFAULT_MODEL}")
    p.add_argument("-t", "--tone", choices=sorted(TONES), help="tone preset")
    p.add_argument("--instruct", help="extra instruction appended to the system prompt")
    p.add_argument("--temp", type=float, help="default 0.1 for check, 0.5 otherwise")
    p.add_argument("--max-tokens", type=int, default=4000)
    p.add_argument("--allow-dashes", action="store_true", help="permit em/en dashes")
    p.add_argument("--no-diff", action="store_true", help="suppress the diff on stderr")
    p.add_argument("--json", action="store_true", help="dump the raw API response")
    p.add_argument("--models", action="store_true", help="list Loes models and exit")
    args = p.parse_args()

    if args.models:
        return list_models()
    if not args.mode:
        p.print_usage(sys.stderr)
        die("a mode is required (check, rewrite, gen, ask) or use --models")

    if args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            die(f"cannot read {args.file}: {exc}")
    elif args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        die("no input. Pass text, use --file, or pipe on stdin.")

    if not text.strip():
        die("input is empty")

    style = STYLE_RULES + ("" if args.allow_dashes else NO_DASH_RULE)
    system = PROMPTS[args.mode]
    if system:
        system = system.format(style=style)
        if args.tone:
            system += "\n" + TONES[args.tone]
    if args.instruct:
        system = f"{system}\n{args.instruct}" if system else args.instruct

    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": text}
    ]
    temp = args.temp if args.temp is not None else (0.1 if args.mode == "check" else 0.5)

    resp = request(
        "/chat/completions",
        json.dumps(
            {
                "model": args.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": args.max_tokens,
            }
        ).encode("utf-8"),
    )

    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return 0

    try:
        out = resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        die(f"unexpected response: {json.dumps(resp)[:400]}", 2)
        raise AssertionError

    out = PREAMBLE.sub("", out).strip()
    if out.startswith("```") and out.endswith("```"):
        out = re.sub(r"^```[a-z]*\n?|\n?```$", "", out).strip()

    print(out)

    guard_tripped = False
    if not args.allow_dashes and DASHES.search(out):
        print(
            "loes: WARNING output contains an em/en dash. Replace it before shipping "
            "(or pass --allow-dashes if your house style permits them).",
            file=sys.stderr,
        )
        guard_tripped = True

    if args.mode == "check" and not args.no_diff:
        changes = word_diff(text, out)
        if changes:
            print(f"loes: {len(changes)} change(s) vs source:", file=sys.stderr)
            for line in changes:
                print(line, file=sys.stderr)
            print(
                "loes: REVIEW REQUIRED - confirm every change above is purely "
                "orthographic. Loes has been observed silently flipping wij/u and "
                "similar facts while 'correcting'.",
                file=sys.stderr,
            )
        else:
            print("loes: no changes; the source was already clean.", file=sys.stderr)

    usage = resp.get("usage") or {}
    if usage:
        print(
            f"loes: {args.model} in={usage.get('prompt_tokens')} "
            f"out={usage.get('completion_tokens')} tokens",
            file=sys.stderr,
        )

    return 3 if guard_tripped else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
