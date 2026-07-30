---
name: dutch-copy
description: 'Dutch (Nederlands) copywriting, spellcheck and proofreading via Loes, the EU-hosted Dutch-native LLM from HostYourAI. Use when writing, checking or rewriting Dutch text such as website copy, product descriptions, emails and UI strings. Diff-reviews every correction so no facts change. Triggers on "spellcheck", "taalfouten", "check deze tekst", "schrijf NL copy", "Nederlandse tekst", "herschrijf dit", "loes", "hostyourai".'
---

# Dutch copy via Loes

## Preflight: run this first, once per session

```sh
loes doctor
```

It reports deps, whether the API key is present, and whether the router answers.
Exit 0 means go ahead. Exit 1 prints exactly what is missing.

**If it says the key is not set, stop and ask the user for it.** Do not go
looking for it. Specifically: no grepping `$HOME` or dotfiles for `hyai-`, no
`security find-generic-password`, no scanning `.env` files. An exported key is
always visible in the agent's environment, so if it is absent there it is not
configured, and only the user can supply it. Hunting for it burns minutes and
thousands of tokens, and rakes unrelated secrets into the transcript. One
question to the user settles it:

> "Loes needs a HostYourAI API key. Grab one at https://hostyourai.com/app/register
> and add `export LOES_PERSONAL_KEY="hyai-..."` to your shell profile."

If `loes` is not on PATH, call the bundled script directly:
`<skill-dir>/scripts/loes doctor`

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

Get a key at <https://hostyourai.com/app/register>, then export it in your shell
profile (`~/.zshrc` / `~/.bashrc`) and restart the shell:

```sh
export LOES_PERSONAL_KEY="hyai-..."   # or LOES_API_KEY / HOSTYOURAI_API_KEY
```

Confirm with `loes doctor`.

`scripts/loes` is a plain shell script. It needs `curl` and `jq`, plus `git` for
the diff (all three ship with macOS 15+; on Debian/Ubuntu:
`apt-get install curl jq git`). No packages, no SDK, no MCP server, no
interpreter runtime.

Symlink it onto your PATH so every session can just call `loes`:

```sh
ln -s "$(pwd)/scripts/loes" ~/bin/loes   # from this skill's directory
```

Without the symlink, call it by path: `<skill-dir>/scripts/loes ...`

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
`--no-guard`, `--verify`, `--no-diff`, `--json`.

Exit codes: `0` ok, `1` usage/input error, `2` API error, `3` a guard tripped
(semantic drift or an em-dash). **Exit 3 means do not ship this output.**

## The drift problem, and what the tool now does about it

`check` is instructed in the strongest terms not to change meaning. It changes
meaning anyway. Three failures observed while building this skill:

- `"...garantie op alle produkten die wij verkopen"` → `"...biedt **u** ... garantie"`
  (flipped who provides the guarantee)
- `"bij ons vind **je**"` → `"bij ons vindt **u**"` (switched register unasked)
- `"energie zuinig"` → `"**energielijk**"`, which is not a Dutch word at all.
  The correct fix was `energiezuinig`. A Dutch-native model still invents
  vocabulary, so "it speaks better Dutch than you" is not "it is right".

Telling you to "read the diff" was not good enough, because the reader is often
a hurried agent. So `check` now **refuses** output that alters anything a
proofreader must never touch. It compares closed token classes between input and
output and exits 3 on any difference:

| class | what it protects |
| --- | --- |
| register | `ik je jij jou jouw jullie u uw wij we ons onze mijn`, i.e. who does what |
| numbers | counts, prices, terms, dates, including `5` → `vijf` |
| links | every `http(s)://…` |
| emails | every address |
| holders | `{{placeholder}}`, `%s`, `${VAR}` |

```
loes: DEFECT  pronoun/register changed (who does what, u vs je)
         removed: 1 je
         added:   1 u
loes: REFUSING this correction: it altered something a proofreader must never touch.
```

Override with `--no-guard` only when you have checked the diff yourself.

### What the guard does not catch

It is a token comparison, not comprehension. It cannot see invented words
(`energielijk`), lost nuance, or a rewritten clause that keeps every pronoun and
number intact. **So still read the diff.** A change is safe only if it is
orthographic: spelling, compounds, punctuation, agreement.

For the invented-word class, `--verify` asks a *different* model family
(`gemma-3-27b-it` by default) to name words that are not real Dutch. It is
advisory and imperfect in both directions, so treat a finding as a prompt to
look, not a verdict, and never treat silence as proof.

When editing a real file, the safe loop is:

```sh
loes check --file copy.md > /tmp/copy.fixed || exit   # exit 3 = refused, stop here
diff copy.md /tmp/copy.fixed                          # read what actually moved
mv /tmp/copy.fixed copy.md                            # only then
```

The `|| exit` matters: it turns the guard into a real gate instead of a message
you can scroll past.

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
