---
name: dutch-copy
description: Use when writing, proofreading, spellchecking or rewriting Dutch (Nederlandse) text: website copy, product descriptions, emails, UI strings. Routes the text through Loes, a Dutch-native LLM hosted in the EU by HostYourAI, then diff-reviews the result so no facts change. Triggers on "spellcheck", "check deze tekst", "schrijf NL copy", "Nederlandse tekst", "herschrijf dit", "taalfouten", "loes".
---

# Dutch copy via Loes

## Why a separate model

General-purpose coding models write *serviceable* Dutch. They reliably miss
`de`/`het` gender, compound spelling (`energiezuinig`, not `energie zuinig`),
`vind`/`vindt`, and the `u`/`je` register. [Loes](https://loes.ai/) is a
Dutch-native finetune served from EU GPUs by
[HostYourAI](https://hostyourai.com/), behind a standard OpenAI-compatible API.
Use it as a **language specialist you call**, not as an agent you hand the task to.

**Loes writes the Dutch. You stay responsible for the facts.** That division is
the whole point of this skill, and the `check` diff enforces it.

## Setup (once)

Get a key at <https://hostyourai.com/app/register>, then export it:

```sh
export LOES_PERSONAL_KEY="hyai-..."   # or LOES_API_KEY / HOSTYOURAI_API_KEY
```

Needs only `python3` and `curl`. No packages, no SDK, no MCP server.
Optionally symlink it onto your PATH so every session can just call `loes`:

```sh
ln -s "$(pwd)/scripts/loes.py" ~/bin/loes   # from this skill's directory
```

Without the symlink, call it by path: `python3 <skill-dir>/scripts/loes.py ...`

## Usage

| Goal | Command |
| --- | --- |
| Proofread a file, keep meaning | `loes check < copy.md > fixed.md` |
| Proofread in place, see the diff | `loes check --file copy.md` |
| Rewrite in a tone | `loes rewrite --tone shop "onze lampen zijn heel erg mooi"` |
| Write new copy from a brief | `loes gen --tone seo "intro van 80 woorden voor categoriepagina buitenlampen"` |
| Raw prompt, no editorial preamble | `loes ask "Hoe zeg je 'fulfillment' netjes in het Nederlands?"` |
| Which models are live | `loes --models` |

Input comes from an argument, `--file`, or stdin. The **result goes to stdout**;
the diff, warnings and token usage go to **stderr**. So `loes check < in.md > out.md`
writes clean text while you still see what changed.

Tones: `shop`, `zakelijk`, `informeel`, `beknopt`, `seo`, `mail`.
Useful flags: `--instruct "<extra rule>"`, `--model`, `--temp`, `--allow-dashes`,
`--no-diff`, `--json`.

Exit codes: `0` ok, `1` usage/input error, `2` API error, `3` a style guard tripped.

## The rule that matters: never ship `check` output unread

`check` is instructed in the strongest terms not to change meaning. It changes
meaning anyway. Three failures observed while building this skill:

- `"...garantie op alle produkten die wij verkopen"` → `"...biedt **u** ... garantie"`
  (flipped who provides the guarantee)
- `"bij ons vind **je**"` → `"bij ons vindt **u**"` (switched register unasked)
- `"energie zuinig"` → `"**energielijk**"`, which is not a Dutch word at all.
  The correct fix was `energiezuinig`. A Dutch-native model still invents
  vocabulary, so "it speaks better Dutch than you" is not "it is right".

That is why the tool prints a word-level diff to stderr and demands review.
**Read the diff. Approve each change.** A change is safe only if it is
orthographic (spelling, compounds, punctuation, agreement). Any change to *who
does what*, a number, price, term, date, product name, or the `u`/`je` register
is a defect: reject it and keep the original wording for that span.

When editing a real file, the safe loop is:

```sh
loes check --file copy.md > /tmp/copy.fixed    # read the diff on stderr
diff copy.md /tmp/copy.fixed                   # confirm nothing semantic moved
mv /tmp/copy.fixed copy.md                     # only then
```

For `gen` and `rewrite` the same caution applies to invented facts: Loes is told
not to make up prices, delivery times or claims, but verify anything specific
against the brief before it ships.

Loes is also not a perfect stylist. It produced `"een prachtige ontwerp"`
(should be `prachtig`) in testing, so treat its output as a strong draft, not as
copy that skips proofreading.

## Models

`loes --models` prints what is live with current pricing. As of writing:

| id | name | in / out per 1M | ctx |
| --- | --- | --- | --- |
| `hyai/loes-large` | Loes Large (default here) | €0.25 / €0.40 | 32k |
| `hyai/loes-qwen3-14b` | Loes World (router default) | €0.15 / €0.25 | 32k |

The EuroLLM-based "fully European" variants are catalogued but report
`available: false`; the router answers `503 … "code":"on_request"` for those, so
the live options are the Qwen-based finetunes. Override the default with
`--model` or `LOES_MODEL`.

Cost is negligible for copy work (a page of text is a fraction of a cent), but
note the router bills ~1.4k prompt tokens even for a one-line input, so per-call
overhead dominates. Batch a whole file in one call rather than looping per line.

## When not to use this

- **English text**: use your own output; Loes is tuned for Dutch.
- **Code, identifiers, filenames**: keep those English. Only user-facing copy
  goes through Loes.
- **Interactive brainstorming about copy**: think in your own context, then send
  the final text through Loes for the language pass.
- **Bulk product feeds in production**: that is an application concern; wire the
  same endpoint into the app via the AI SDK's OpenAI-compatible provider instead
  of shelling out per row.
