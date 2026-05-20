# Thematic Analysis

AI-powered thematic analysis for customer interview transcripts. Paste your transcripts into a browser UI and get structured qualitative analysis: open coding, theme development, business implications, recommendations, and a final executive-ready report.

## Getting Started (macOS App)

### First Launch

1. Unzip `Thematic-Analysis-0.1.0-mac-arm64.zip`
2. Optionally drag **Thematic Analysis.app** to your Applications folder
3. **Right-click > Open** on first launch (required because the app is unsigned — macOS blocks unsigned apps on double-click, but right-click > Open bypasses this once)
4. The app opens your browser to `localhost:5111`

### You'll Need

- An **OpenAI API key** — get one at https://platform.openai.com/api-keys
- The app prompts you to enter your key on first use. It's saved locally in `~/.thematic-analysis/.env` and never leaves your machine (except to call the OpenAI API).

## How It Works

### 1. Create a Project

Fill in:
- **Project name** — identifies your study
- **Your name** (as moderator) — so the AI knows not to code your questions
- **Note-takers** (optional) — other team members to exclude from coding
- **Research questions** — what you're trying to answer
- **Business context** — grounds the "so what" analysis in your actual situation
- **Model + reasoning effort** — defaults to GPT-5.4 with high reasoning

### 2. Add Transcripts

Paste one or more interview transcripts and name each participant. Each transcript gets coded independently.

### 3. Run the Analysis

The tool runs 7 stages sequentially, streaming each response in real-time:

| Stage | What It Does |
|-------|-------------|
| 1. Open Coding | Identifies codes with verbatim quotes (per transcript) |
| 2. Axial/Focus Coding | Groups codes into thematic clusters, merges duplicates |
| 3. Develop Themes | Builds interpretive themes answering your research questions |
| 4. Why It Matters | Translates themes into business/product implications |
| 5. Recommendations | Prioritized, actionable next steps with owners and timelines |
| 6. Gap Analysis | Identifies unanswered questions and research limitations |
| 7. Reporting | Final executive-ready synthesis (~6-10 pages) |

After each stage, you **review the output** and choose to continue, retry, or quit. Progress is saved — you can quit and resume later.

### 4. Export

Download individual stage outputs or all outputs as a zip.

## Tips

- **Verbatim quote verification**: After coding, the tool checks that quoted text actually appears word-for-word in your transcripts. You can reject any misquoted passages.
- **Resume**: If you close the app mid-analysis, reopen it and select your project — it picks up where you left off.
- **Multiple transcripts**: Each transcript is coded independently, then codes are merged before the shared analysis stages.

## For Developers

If you're running from source instead of the `.app` bundle:

```bash
uv sync
uv run thematic-analysis   # opens browser to localhost:5111
```

### Building the `.app`

```bash
bash scripts/build-macos.sh
cd dist && zip -r "Thematic-Analysis-0.1.0-mac-arm64.zip" "Thematic Analysis.app"
```

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

## Example Transcript

See `examples/example-transcript.txt` for a sample interview transcript you can paste into the tool to try it out. The `examples/example-config.toml` shows the configuration format (used internally by the tool when you fill in the project setup form).
