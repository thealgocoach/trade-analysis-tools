# trade-analysis-tools

Python tools Tom (AlgoCoach) builds and publishes so viewers of his YouTube
walkthroughs can download and run them. Owner: FX Alive Technologies Corp.

Read this before changing any file in this repo.

## Who lands here and what they need

Two kinds of reader:

1. Someone who watched a walkthrough video and came to get the tool
2. Someone who found the repo on GitHub first

Both are already at the download by the time they are reading. So the repo's job
is to make the tool runnable in one go, not to sell anything. The site link
exists for walkthrough videos and other tools, never framed as the download.

## Structure

```
trade-analysis-tools/
├── <tool-name>/              one folder per tool, kebab-case
│   ├── <Tool_Name_x_y>.py    the script
│   ├── <sample>.csv          trimmed sample data so it runs out of the box
│   ├── requirements.txt      pinned to what the script actually imports
│   └── README.md             this tool only
├── .gitignore
├── LICENSE                   MIT, copyright FX Alive Technologies Corp.
└── README.md                 index table, one row per tool
```

Folder names are kebab-case and match the tool name: `best-times-checker`.
Script filenames keep the underscore-and-version form Tom uses locally.

**One repo per suite.** The five analysis tools live here. The Set File Manager
chain gets its own repo. The site is the index across repos.

## Versioning

**Keep versions. Do not delete a published script when a new one ships.**

Tom's call, Aug 2026. Published versions stay in the folder so that viewers
arriving from an older walkthrough video can still get the version they watched,
and so earlier work stays visible.

Still no GitHub Releases and no tags. The site's Get it button points at the repo
home, so it can never go stale.

The version lives in the script filename. Each tool README must state:

- which version is current
- which version each walkthrough video covers
- what changed between versions, in one line each

Without those three lines a reader lands on two scripts and cannot tell which one
to run. That is worse than either version alone, so the README is not optional
here.

Prune only when a version is genuinely obsolete, and only when Tom says so.

## Links

**Never link to YouTube from this repo.** There is no walkthrough on GitHub, and
the site already carries the video link. One index to maintain rather than
several.

**Never link to versioned or deep paths.** Link to `algocoach.com/tools` and
nothing more specific, so links survive the eventual move off Wix.

Frame the site link as walkthrough videos and more tools. Not as the download.

## Every tool folder needs

Before a tool is considered shipped:

- [ ] Script runs from a clean clone with no edits, using the bundled sample data
- [ ] Sample data trimmed small enough to commit, large enough to produce real
      output
- [ ] `requirements.txt` matches the actual imports, nothing extra
- [ ] Path resolution is `__file__`-based so it works from any working directory
- [ ] File writes specify `encoding='utf-8'`
- [ ] Tool README covers: what it does, what it does not do, how to run it,
      what the output means, and the educational-use disclaimer
- [ ] Tool README names the current version, says which version each walkthrough
      video covers, and lists what changed
- [ ] Root README index gains a row for the tool
- [ ] Tool named in plain trader language, no invented jargon

## Language

Output and documentation use terms a trader already knows. Terms previously
rejected: "lift", "times better", "decided days", "good day".

**No profit or performance claims anywhere in this repo.** The tools count
historical price moves and that is how they get described. A tool measures how
often price reached a target distance before a stop distance. It does not find
edges, predict, or produce signals.

Every tool README carries an educational-use line: the tool is for educational
and informational purposes, not financial advice, and the user is responsible for
their own trading decisions.

**No em-dashes** in anything written for this repo.

## Repo settings that stay as they are

- Issues: off
- Website field: algocoach.com
- Releases and tags: none
- License: MIT, copyright FX Alive Technologies Corp.

## Git workflow

Solo repo, commit to `main` directly. Group a tool ship into one commit so the
history reads as one tool per commit where possible.

Commit message form: `add <tool name> v<x.y>` or `update <tool name> to v<x.y>`.

Always show Tom the diff before committing, and never push without him saying so.

## Related

- `algocoach.com/tools` is the public index, one row per tool
- Publishing the video that goes with a tool is a separate process, handled by
  the `algocoach-release` skill in Cowork, not here
