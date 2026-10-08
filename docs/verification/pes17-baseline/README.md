# PES 2017 baseline under Wine (Phase 0 gate, spec 2.1): PASS

- Date: 2026-10-08, 18:12–18:39 local.
- Build: tag `baseline-pes17` (upstream `a5d430d` + MinGW portability edits, see `../QUESTIONS.md`), run in the PES 2017 prefix `$HEROIC_PREFIXES/default/Pro Evolution Soccer 2017` with `/usr/bin/wine` (wine-11.19 Staging).
- Match: testbot scenario `docs/plans/senpai/scenario_subs_bestxi.yaml` match 1, `/g/` (721) vs `/sp/` (750), final 0–1 (bot: `result: '/g/' vs '/sp/' score=(0, 1)`).
- Autosave at match end was set through the prefix registry (`HKCU\Software\The4chanCup\SEN_P-AI`: `MatchAutosaveOnEnd=true`, `MatchAutosaveFile=%HOME_vs_%AWAY.sen`), the same values the Settings dialog writes.

## Gate checks

| Check | Result |
|---|---|
| `OpenProcess`/`VirtualQueryEx`/`ReadProcessMemory` across Wine processes | works: status "SEN:P-AI noticed the teams!" then stats found (window screenshot taken; status texts are not in the debug log) |
| Event set | `Teams Changed` 1, `Stats Found` 1, `Clock Stopped` 21, `Clock Started` 20, `Clock Updated` 1096, `Player Sub` 2, `Card` 1, `Goal` 1, `Stats Lost` 1 |
| Goals vs bot log | SEN:P-AI `Goal` 90' Away `SO, IT HAPPENED AGAIN`; bot `goal: away scored at 90:00`, scorer `SO, IT HAPPENED AGAIN` |
| Subs vs bot log | SEN:P-AI `Player Sub` Away `MY REFFIES :)` at 17.8' (wall 18:22:49), Away `AMD AMX` at 63' (18:32:40); bot `sub at 15': inza -> 9 my reffies :)` (18:22:50), `sub at 60': univer -> 33 amd amx` (18:32:22). The bot's 30' home sub failed on the bot side. Players agree; the bot logs the *scheduled* minute, the game applies the change at the next stoppage, so the minute is not a ±1 oracle (see `../QUESTIONS.md`). |
| `.sen` written | `match.sen`, written on Stats Lost; stat count 175, `finalStats` 32200 bytes |
| Pipe vs log | `diff_events.py events.log tap.bin` exit 0 (1144 frames) |

Evidence: `events.log`, `tap.bin`, `match.sen`, `bot.log` (match 1 only).
